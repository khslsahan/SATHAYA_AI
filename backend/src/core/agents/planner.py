"""Planner Agent for query decomposition."""

import json
from typing import List, Dict, Any
import structlog

from src.services.llm_service import get_llm_service
from src.core.prompts.planner_prompt import PLANNER_SYSTEM_PROMPT

logger = structlog.get_logger(__name__)


class PlannerAgent:
    """Agent that decomposes complex queries into sub-queries."""

    def __init__(self):
        """Initialize Planner Agent."""
        self.llm_service = get_llm_service()
        self.system_prompt = PLANNER_SYSTEM_PROMPT

    async def plan(self, query: str) -> Dict[str, Any]:
        """
        Create execution plan for complex query.

        Args:
            query: Complex user query

        Returns:
            Execution plan with sub-queries and order
        """
        logger.info("Planning query decomposition", query=query[:100])

        # Create prompt for LLM
        prompt = f"Break down the following complex legal query into sub-queries:\n\n{query}"

        try:
            # Get LLM response
            response, provider = await self.llm_service.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.5,
            )

            # Parse JSON response
            plan = self._parse_response(response)

            logger.info(
                "Query planned",
                sub_queries_count=len(plan.get("sub_queries", [])),
            )

            return plan

        except Exception as e:
            logger.error("Planning failed", error=str(e))
            # Return simple plan with single query
            return {
                "sub_queries": [
                    {
                        "id": 1,
                        "query": query,
                        "agent": "STATUTORY_AGENT",
                        "reasoning": "Default plan due to planning error",
                    }
                ],
                "execution_order": [1],
                "synthesis_instructions": "Return the result directly",
            }

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into execution plan.

        Args:
            response: LLM response text

        Returns:
            Parsed execution plan
        """
        try:
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()

            plan = json.loads(response)

            # Validate structure
            if "sub_queries" not in plan:
                raise ValueError("Missing sub_queries in plan")

            # Validate sub-queries
            for sq in plan["sub_queries"]:
                required_fields = ["id", "query", "agent"]
                if not all(field in sq for field in required_fields):
                    raise ValueError("Invalid sub-query structure")

                # Validate agent type
                if sq["agent"] not in ["STATUTORY_AGENT", "CASE_LAW_AGENT"]:
                    logger.warning(
                        "Invalid agent type, defaulting to STATUTORY_AGENT",
                        agent=sq["agent"],
                    )
                    sq["agent"] = "STATUTORY_AGENT"

            # Set defaults
            plan.setdefault("execution_order", [sq["id"] for sq in plan["sub_queries"]])
            plan.setdefault(
                "synthesis_instructions",
                "Combine all sub-query results into a coherent answer",
            )

            return plan

        except json.JSONDecodeError as e:
            logger.error("Failed to parse plan response as JSON", error=str(e))
            raise
        except Exception as e:
            logger.error("Error parsing plan response", error=str(e))
            raise

