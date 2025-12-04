"""Tests for Router Agent."""

import pytest
from src.core.agents.router import RouterAgent


@pytest.mark.asyncio
async def test_router_simple_query():
    """Test router with simple query."""
    router = RouterAgent()
    result = await router.route("What is the penalty for theft?")
    
    assert "category" in result
    assert "reasoning" in result
    assert result["category"] in [
        "SIMPLE_FACT",
        "STATUTORY_INTERPRETATION",
        "CASE_LAW_NEEDED",
        "COMPLEX_MULTI_FACETED",
    ]


@pytest.mark.asyncio
async def test_router_complex_query():
    """Test router with complex query."""
    router = RouterAgent()
    result = await router.route(
        "Compare property law and immigration rules for foreign investors"
    )
    
    assert result["category"] == "COMPLEX_MULTI_FACETED"
    assert result.get("requires_planner", False) is True

