"""Router Agent for query classification and routing."""

import json
from typing import Dict, Any, Literal
import structlog

from src.services.llm_service import get_llm_service
from src.core.prompts.router_prompt import ROUTER_SYSTEM_PROMPT

logger = structlog.get_logger(__name__)


class RouterAgent:
    """Agent that classifies queries and determines routing requirements."""

    def __init__(self):
        """Initialize Router Agent."""
        self.llm_service = get_llm_service()
        self.system_prompt = ROUTER_SYSTEM_PROMPT

    async def route(
        self, query: str
    ) -> Dict[str, Any]:
        """
        Classify query and determine routing.

        Args:
            query: User query

        Returns:
            Routing decision with category and agent requirements
        """
        logger.info("Routing query", query=query[:100])

        # Create prompt for LLM
        prompt = f"Analyze the following legal query and classify it:\n\n{query}"

        try:
            # Get LLM response
            response, provider = await self.llm_service.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.3,  # Low temperature for consistent classification
            )

            # Parse JSON response
            routing_decision = self._parse_response(response)

            logger.info(
                "Query routed",
                category=routing_decision["category"],
                requires_planner=routing_decision.get("requires_planner", False),
            )

            return routing_decision

        except Exception as e:
            logger.error("Routing failed", error=str(e))
            # Default to complex routing on error
            return {
                "category": "COMPLEX_MULTI_FACETED",
                "reasoning": "Error in routing, defaulting to complex",
                "requires_planner": True,
                "requires_statutory_agent": True,
                "requires_case_law_agent": True,
            }

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into routing decision.

        Args:
            response: LLM response text

        Returns:
            Parsed routing decision
        """
        try:
            # Try to extract JSON from response
            # Remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()

            decision = json.loads(response)

            # Validate structure
            required_fields = ["category", "reasoning"]
            if not all(field in decision for field in required_fields):
                raise ValueError("Missing required fields in routing decision")

            # Set defaults
            decision.setdefault("requires_planner", False)
            decision.setdefault("requires_statutory_agent", True)
            decision.setdefault("requires_case_law_agent", False)

            # Validate category
            valid_categories = [
                "SIMPLE_FACT",
                "STATUTORY_INTERPRETATION",
                "CASE_LAW_NEEDED",
                "COMPLEX_MULTI_FACETED",
            ]
            if decision["category"] not in valid_categories:
                logger.warning(
                    "Invalid category, defaulting to COMPLEX_MULTI_FACETED",
                    category=decision["category"],
                )
                decision["category"] = "COMPLEX_MULTI_FACETED"
                decision["requires_planner"] = True

            return decision

        except json.JSONDecodeError as e:
            logger.error("Failed to parse routing response as JSON", error=str(e))
            # Default routing
            return {
                "category": "COMPLEX_MULTI_FACETED",
                "reasoning": "Failed to parse routing response",
                "requires_planner": True,
                "requires_statutory_agent": True,
                "requires_case_law_agent": True,
            }
        except Exception as e:
            logger.error("Error parsing routing response", error=str(e))
            raise

