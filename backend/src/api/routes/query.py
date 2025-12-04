"""Query endpoints for legal queries."""

import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.orchestrator import Orchestrator

router = APIRouter()
orchestrator = Orchestrator()


class QueryRequest(BaseModel):
    """Query request model."""

    query: str = Field(..., description="Legal query to process", min_length=1, max_length=5000)
    session_id: str | None = Field(None, description="Session ID for conversation context")


class QueryResponse(BaseModel):
    """Query response model."""

    answer: str
    citations: list[dict]
    session_id: str
    sources: list[dict] | None = None
    routing: dict | None = None


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a legal query."""
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # Process query through orchestrator
        result = await orchestrator.process_query(
            query=request.query,
            session_id=session_id,
        )

        return QueryResponse(
            answer=result["answer"],
            citations=result.get("citations", []),
            session_id=result.get("session_id", session_id),
            sources=result.get("sources", []),
            routing=result.get("routing"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}",
        )


@router.get("/query/{session_id}")
async def get_query_history(session_id: str):
    """Get query history for a session."""
    # TODO: Implement session history retrieval with database
    raise HTTPException(status_code=501, detail="Query history not yet implemented")

