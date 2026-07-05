"""Agent state definition for the CPIS LangGraph pipeline.

Tracks candidate document information, extracted candidate data,
validation feedback errors, and job matches.
"""

from typing import Annotated, Any, List, Optional, TypedDict
from langgraph.graph.message import add_messages

from src.models.schemas.schemas import ResumeSchema, JobMatchResult


class AgentState(TypedDict):
    """Immutable state passed between nodes in the CPIS agentic graph."""

    messages: Annotated[List[Any], add_messages]
    document_content: str
    document_id: str
    extracted_data: Optional[ResumeSchema]
    validation_errors: List[str]
    revision_count: int
    matched_jobs: List[JobMatchResult]
