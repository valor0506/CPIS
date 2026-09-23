"""LangGraph definition and compilation for the CPIS agentic pipeline.

Compiles the graph state machine with cyclic routing logic for
self-correction and structured output matching.
"""

from typing import Dict, Any

from langgraph.graph import StateGraph, START, END

from src.core.config.config import get_settings
from src.core.logger.logger import setup_logger
from src.agents.state import AgentState
from src.agents.nodes import extract_resume, validate_data, match_job, classify_document

logger = setup_logger("agent_graph")


def should_continue(state: AgentState) -> str:
    """Determine the next step in the workflow based on validation errors.

    Args:
        state: The current agent state.

    Returns:
        str: Next node to execute ("match_job" or "extract_resume").
    """
    settings = get_settings()
    errors = state.get("validation_errors", [])
    revision = state.get("revision_count", 0)

    if not errors:
        logger.info("No validation errors found. Proceeding to job matching.")
        return "match_job"

    if revision >= settings.MAX_REVISION_COUNT:
        logger.warning(
            f"Validation errors present ({len(errors)} errors), but reached "
            f"maximum revision limit ({settings.MAX_REVISION_COUNT}). Proceeding to job matching."
        )
        return "match_job"

    logger.info(
        f"Validation failed with {len(errors)} errors. Routing back to "
        f"extract_resume for correction (Attempt {revision + 1} of {settings.MAX_REVISION_COUNT})."
    )
    return "extract_resume"


def route_classification(state: AgentState) -> str:
    """Determine whether to proceed with extraction based on classification."""
    is_resume = state.get("is_resume")
    if is_resume:
        logger.info("Classification passed. Routing to extract_resume.")
        return "extract_resume"
    else:
        logger.warning("Classification failed. Routing to END.")
        return END


# Build the Graph
builder = StateGraph(AgentState)

# Register Nodes
builder.add_node("classify_document", classify_document)
builder.add_node("extract_resume", extract_resume)
builder.add_node("validate_data", validate_data)
builder.add_node("match_job", match_job)

# Register Flow Edges
builder.add_edge(START, "classify_document")

builder.add_conditional_edges(
    "classify_document",
    route_classification,
    {
        "extract_resume": "extract_resume",
        END: END,
    }
)

builder.add_edge("extract_resume", "validate_data")

# Register Conditional Routing Edges
builder.add_conditional_edges(
    "validate_data",
    should_continue,
    {
        "match_job": "match_job",
        "extract_resume": "extract_resume",
    }
)

builder.add_edge("match_job", END)

# Compile Graph
graph = builder.compile()


def run_agentic_pipeline(document_content: str, document_id: str) -> Dict[str, Any]:
    """Run the compiled LangGraph pipeline for resume processing and job matching.

    Args:
        document_content: Parsed and clean text content of the resume.
        document_id: SHA-256 fingerprint reference.

    Returns:
        Dict[str, Any]: Final output state containing extracted data, validation errors,
                       and matched jobs.
    """
    initial_state: AgentState = {
        "messages": [],
        "document_content": document_content,
        "document_id": document_id,
        "is_resume": None,
        "extracted_data": None,
        "validation_errors": [],
        "revision_count": 0,
        "matched_jobs": [],
    }

    logger.info(f"Running LangGraph agentic pipeline for document {document_id}")
    final_state = graph.invoke(initial_state)
    return final_state
