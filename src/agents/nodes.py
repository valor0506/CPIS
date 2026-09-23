"""Nodes implementation for the CPIS LangGraph pipeline.

Implements the resume text extraction, data validation,
and semantic job matching steps.
"""

import json
import re
from typing import Dict, Any, List

import google.generativeai as genai

from src.core.config.config import get_settings
from src.core.exceptions.exceptions import AgentException
from src.core.logger.logger import setup_logger
from src.models.schemas.schemas import ResumeSchema, JobMatchResult
from src.storage.vector_store import ChromaVectorStore
from src.agents.state import AgentState

logger = setup_logger("agent_nodes")


def classify_document(state: AgentState) -> Dict[str, Any]:
    """Determine if the document is a resume before expensive processing.

    Args:
        state: The current agent state.

    Returns:
        Dict[str, Any]: State updates with is_resume boolean.
    """
    settings = get_settings()
    content = state["document_content"]

    # Truncate content to first 1500 chars to save tokens
    truncated_content = content[:1500]
    logger.info(f"Classifying document. Truncated length: {len(truncated_content)}")

    if not settings.GEMINI_API_KEY:
        raise AgentException("GEMINI_API_KEY is not set. Cannot run agentic classification.")

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = (
            f"Analyze the following text and determine if it appears to be a resume or CV. "
            f"Output a JSON object with a single boolean key 'is_resume'.\n\n"
            f"Text:\n{truncated_content}"
        )

        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "OBJECT",
                    "properties": {
                        "is_resume": {"type": "BOOLEAN"}
                    },
                    "required": ["is_resume"]
                }
            }
        )

        res_json = json.loads(response.text)
        is_resume = res_json.get("is_resume", False)

        if is_resume:
            logger.info("Document classified as a RESUME. Proceeding.")
        else:
            logger.warning("Document classified as NON-RESUME. Halting pipeline.")

        return {"is_resume": is_resume}

    except Exception as e:
        logger.error(f"Error during document classification: {str(e)}")
        raise AgentException(f"Document classification failed: {str(e)}", original_exception=e)


def extract_resume(state: AgentState) -> Dict[str, Any]:
    """Extract structured candidate information from resume text using Gemini.

    Args:
        state: The current agent state.

    Returns:
        Dict[str, Any]: State updates with extracted_data and revision_count.
    """
    settings = get_settings()
    content = state["document_content"]
    errors = state.get("validation_errors", [])
    revision = state.get("revision_count", 0)

    logger.info(f"Extracting resume. Revision count: {revision}")

    if not settings.GEMINI_API_KEY:
        raise AgentException("GEMINI_API_KEY is not set. Cannot run agentic resume extraction.")

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"Extract structured resume information from the following resume text:\n\n{content}\n\n"
        if errors:
            prompt += "IMPORTANT: Your previous extraction failed validation with the following errors:\n"
            for err in errors:
                prompt += f"- {err}\n"
            prompt += "\nPlease pay close attention to these errors, correct them, and output a valid JSON matching the schema."

        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": ResumeSchema
            }
        )

        # Parse extracted json to Pydantic model
        extracted_data = ResumeSchema.model_validate_json(response.text)
        logger.info("Successfully extracted candidate data using Gemini API.")

        return {
            "extracted_data": extracted_data,
            "revision_count": revision + 1,
            "messages": [("assistant", response.text)]
        }

    except Exception as e:
        logger.error(f"Error during Gemini extraction: {str(e)}")
        raise AgentException(f"Gemini resume extraction failed: {str(e)}", original_exception=e)


def validate_data(state: AgentState) -> Dict[str, Any]:
    """Validate the extracted data against business rules.

    Args:
        state: The current agent state.

    Returns:
        Dict[str, Any]: State updates with list of validation_errors.
    """
    logger.info("Running validation on extracted candidate data.")
    errors = []
    data = state.get("extracted_data")

    if not data:
        errors.append("No data was extracted from the resume.")
        return {"validation_errors": errors}

    # Rule 1: Candidate name must be present
    name = data.personal_info.name
    if not name or not name.strip():
        errors.append("Candidate name is missing or empty.")

    # Rule 2: Email must be present and valid
    email = data.personal_info.email
    if not email or not email.strip():
        errors.append("Candidate email is missing or empty.")
    else:
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_pattern, email.strip()):
            errors.append(f"Candidate email '{email}' is invalid.")

    # Rule 3: Skills list must not be empty
    if not data.skills or len(data.skills) == 0:
        errors.append("At least one skill must be extracted.")

    if errors:
        logger.warning(f"Validation failed with {len(errors)} errors: {errors}")
    else:
        logger.info("Validation succeeded.")

    return {"validation_errors": errors}


def match_job(state: AgentState) -> Dict[str, Any]:
    """Search for matching jobs in ChromaDB and score the alignment.

    Args:
        state: The current agent state.

    Returns:
        Dict[str, Any]: State updates with matched_jobs list.
    """
    settings = get_settings()
    data = state.get("extracted_data")

    if not data:
        logger.warning("No candidate data available to perform job matching.")
        return {"matched_jobs": []}

    logger.info(f"Querying vector database to match jobs for candidate: {data.personal_info.name}")

    # 1. Build search query from candidate skills and experience titles
    query_parts = []
    if data.skills:
        query_parts.append(f"Skills: {', '.join(data.skills)}")
    for exp in data.experience:
        if exp.job_title:
            company_str = f" at {exp.company}" if exp.company else ""
            query_parts.append(f"Worked as {exp.job_title}{company_str}")

    query_text = "; ".join(query_parts) if query_parts else "Software Developer"

    # 2. Similarity search in ChromaDB
    collection_name = getattr(settings, "JOBS_COLLECTION_NAME", "jobs")
    try:
        store = ChromaVectorStore(collection_name=collection_name)
        chunks = store.similarity_search(query_text, k=3)
        logger.info(f"Found {len(chunks)} matching job chunks in collection '{collection_name}'")
    except Exception as e:
        logger.error(f"Error querying vector store: {e}")
        chunks = []

    # 3. Evaluate alignment scoring
    matched_jobs = []
    for chunk in chunks:
        score = 0.5  # Default fallback score
        explanation = "Retrieved via vector similarity query."

        # If Gemini is configured, use it to grade the semantic alignment
        if settings.GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel("gemini-1.5-flash")

                profile_summary = f"Skills: {data.skills}\nExperience: {[{'title': e.job_title, 'company': e.company, 'desc': e.description} for e in data.experience]}"
                prompt = (
                    f"Evaluate the fit between this candidate profile and this job description snippet.\n\n"
                    f"Candidate Profile:\n{profile_summary}\n\n"
                    f"Job Snippet:\n{chunk.text}\n\n"
                    f"Provide a float score between 0.0 (no fit) and 1.0 (perfect fit). "
                    f"Format your output as a JSON object with keys: 'score' (float) and 'explanation' (string)."
                )

                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                res_json = json.loads(response.text)
                score = float(res_json.get("score", 0.5))
                explanation = res_json.get("explanation", explanation)
            except Exception as e:
                logger.warning(f"Failed to score chunk with Gemini: {e}")

        # Fetch metadata details
        job_title = chunk.metadata.get("job_title") or chunk.metadata.get("title")
        company = chunk.metadata.get("company")

        matched_jobs.append(
            JobMatchResult(
                job_id=chunk.id,
                score=score,
                job_title=job_title,
                company=company,
                snippet=chunk.text
            )
        )

    # Sort results by score (descending)
    matched_jobs.sort(key=lambda x: x.score, reverse=True)
    return {"matched_jobs": matched_jobs}
