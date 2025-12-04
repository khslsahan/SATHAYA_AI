"""Main orchestrator for coordinating all agents."""

from typing import Dict, Any, List
import structlog

from src.core.agents.router import RouterAgent
from src.core.agents.planner import PlannerAgent
from src.core.agents.statutory import StatutoryAgent
from src.core.agents.case_law import CaseLawAgent
from src.core.agents.refiner import RefinerAgent

logger = structlog.get_logger(__name__)


class Orchestrator:
    """Main orchestrator that coordinates all agents."""

    def __init__(self):
        """Initialize orchestrator with all agents."""
        self.router = RouterAgent()
        self.planner = PlannerAgent()
        self.statutory_agent = StatutoryAgent()
        self.case_law_agent = CaseLawAgent()
        self.refiner = RefinerAgent()

    async def process_query(
        self, query: str, session_id: str | None = None
    ) -> Dict[str, Any]:
        """
        Process a legal query through the agent pipeline.

        Args:
            query: User query
            session_id: Optional session ID for conversation context

        Returns:
            Final answer with citations and sources
        """
        logger.info("Processing query", query=query[:100], session_id=session_id)

        try:
            # Step 1: Route the query
            routing_decision = await self.router.route(query)

            category = routing_decision["category"]
            requires_planner = routing_decision.get("requires_planner", False)
            requires_statutory = routing_decision.get(
                "requires_statutory_agent", True
            )
            requires_case_law = routing_decision.get("requires_case_law_agent", False)

            logger.info(
                "Query routed",
                category=category,
                requires_planner=requires_planner,
            )

            # Step 2: Plan if needed
            plan = None
            if requires_planner:
                plan = await self.planner.plan(query)
                logger.info("Query planned", sub_queries=len(plan.get("sub_queries", [])))

            # Step 3: Execute agent searches
            all_sources = []
            all_citations = []
            answers = []

            if plan:
                # Execute planned sub-queries
                execution_order = plan.get("execution_order", [])
                sub_queries = {
                    sq["id"]: sq for sq in plan.get("sub_queries", [])
                }

                for sub_query_id in execution_order:
                    sub_query = sub_queries.get(sub_query_id)
                    if not sub_query:
                        continue

                    agent_type = sub_query["agent"]
                    sub_query_text = sub_query["query"]

                    if agent_type == "STATUTORY_AGENT":
                        result = await self.statutory_agent.search(sub_query_text)
                    elif agent_type == "CASE_LAW_AGENT":
                        result = await self.case_law_agent.search(sub_query_text)
                    else:
                        result = await self.statutory_agent.search(sub_query_text)

                    answers.append({
                        "sub_query": sub_query_text,
                        "answer": result.get("answer", ""),
                        "citations": result.get("citations", []),
                        "sources": result.get("sources", []),
                    })

                    all_sources.extend(result.get("sources", []))
                    all_citations.extend(result.get("citations", []))

                # Synthesize answers
                synthesis_instructions = plan.get(
                    "synthesis_instructions",
                    "Combine all sub-query results into a coherent answer",
                )
                draft_answer = self._synthesize_answers(answers, synthesis_instructions)

            else:
                # Direct execution without planning
                if requires_statutory:
                    statutory_result = await self.statutory_agent.search(query)
                    answers.append({
                        "answer": statutory_result.get("answer", ""),
                        "citations": statutory_result.get("citations", []),
                        "sources": statutory_result.get("sources", []),
                    })
                    all_sources.extend(statutory_result.get("sources", []))
                    all_citations.extend(statutory_result.get("citations", []))

                if requires_case_law:
                    case_law_result = await self.case_law_agent.search(query)
                    answers.append({
                        "answer": case_law_result.get("answer", ""),
                        "citations": case_law_result.get("citations", []),
                        "sources": case_law_result.get("sources", []),
                    })
                    all_sources.extend(case_law_result.get("sources", []))
                    all_citations.extend(case_law_result.get("citations", []))

                # Combine answers
                if len(answers) == 1:
                    draft_answer = answers[0]["answer"]
                else:
                    draft_answer = self._combine_answers(answers)

            # Step 4: Refine the answer
            refined_result = await self.refiner.refine(
                draft_answer=draft_answer,
                sources=all_sources,
                citations=all_citations,
            )

            final_answer = refined_result["answer"]
            final_citations = refined_result["citations"]

            logger.info(
                "Query processed successfully",
                answer_length=len(final_answer),
                citations_count=len(final_citations),
            )

            return {
                "answer": final_answer,
                "citations": final_citations,
                "sources": all_sources,
                "session_id": session_id,
                "routing": {
                    "category": category,
                    "reasoning": routing_decision.get("reasoning", ""),
                },
            }

        except Exception as e:
            logger.error("Query processing failed", error=str(e), exc_info=True)
            return {
                "answer": f"An error occurred while processing your query: {str(e)}",
                "citations": [],
                "sources": [],
                "session_id": session_id,
                "error": str(e),
            }

    def _synthesize_answers(
        self, answers: List[Dict[str, Any]], instructions: str
    ) -> str:
        """
        Synthesize multiple sub-query answers into one.

        Args:
            answers: List of sub-query answers
            instructions: Synthesis instructions

        Returns:
            Synthesized answer
        """
        if not answers:
            return "No answers to synthesize."

        if len(answers) == 1:
            return answers[0].get("answer", "")

        # Combine answers with clear separation
        synthesized_parts = []
        for i, answer_data in enumerate(answers, 1):
            sub_query = answer_data.get("sub_query", f"Sub-query {i}")
            answer = answer_data.get("answer", "")
            synthesized_parts.append(f"## {sub_query}\n\n{answer}\n")

        synthesized = "\n".join(synthesized_parts)

        # Add synthesis note
        if instructions:
            synthesized = f"{synthesized}\n\n*Note: {instructions}*"

        return synthesized

    def _combine_answers(self, answers: List[Dict[str, Any]]) -> str:
        """
        Combine multiple answers into one.

        Args:
            answers: List of answers

        Returns:
            Combined answer
        """
        if not answers:
            return "No answers available."

        combined_parts = []
        for answer_data in answers:
            answer = answer_data.get("answer", "")
            if answer:
                combined_parts.append(answer)

        return "\n\n".join(combined_parts)

