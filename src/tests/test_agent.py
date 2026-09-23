"""Unit and integration tests for the CPIS LangGraph agentic pipeline."""

import json
from unittest.mock import MagicMock, patch
import pytest

from src.core.config.config import Settings
from src.core.exceptions.exceptions import AgentException
from src.agents.graph import run_agentic_pipeline
from src.models.schemas.schemas import DocumentChunk


@pytest.fixture
def mock_settings(monkeypatch):
    """Set up test settings with GEMINI_API_KEY to bypass check."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_key_abc_123")
    monkeypatch.setenv("MAX_REVISION_COUNT", "2")
    from src.core.config.config import reset_settings
    reset_settings()
    yield
    reset_settings()


@pytest.fixture
def mock_vector_store():
    """Mock the ChromaVectorStore to avoid disk writes and return dummy jobs."""
    with patch("src.agents.nodes.ChromaVectorStore") as mock_cls:
        mock_instance = MagicMock()
        
        # Mock matching jobs chunks
        chunk = DocumentChunk(
            id="job_chunk_1",
            text="We are looking for a Python Software Engineer with Machine Learning experience.",
            metadata={"job_title": "Python Engineer", "company": "TechCorp"}
        )
        mock_instance.similarity_search.return_value = [chunk]
        mock_cls.return_value = mock_instance
        yield mock_instance


@patch("src.agents.nodes.genai.GenerativeModel")
def test_agent_success_flow(mock_model_cls, mock_settings, mock_vector_store):
    """Verify that the agent extracts, validates, and matches jobs successfully without retries."""
    # Set up mock response
    mock_class_response = MagicMock()
    mock_class_response.text = '{"is_resume": true}'

    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "personal_info": {
            "name": "John Doe",
            "email": "john.doe@gmail.com",
            "phone": "555-0199",
            "location": "San Francisco, CA"
        },
        "education": [
            {
                "degree": "B.S.",
                "major": "Computer Science",
                "institution": "Stanford University",
                "graduation_year": 2022
            }
        ],
        "experience": [
            {
                "job_title": "Software Intern",
                "company": "Google",
                "duration": "3 months",
                "description": "Built backend APIs."
            }
        ],
        "skills": ["Python", "Pydantic", "SQL"]
    })
    
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = [mock_class_response, mock_response]
    mock_model_cls.return_value = mock_model

    # Run pipeline
    final_state = run_agentic_pipeline(
        document_content="John Doe is a Stanford graduate with experience at Google. Skills: Python.",
        document_id="dummy_sha256"
    )

    # Assert success state
    assert final_state["revision_count"] == 1
    assert len(final_state["validation_errors"]) == 0
    assert final_state["extracted_data"].personal_info.name == "John Doe"
    assert final_state["extracted_data"].personal_info.email == "john.doe@gmail.com"
    assert "Python" in final_state["extracted_data"].skills
    
    # Assert job matching ran
    assert len(final_state["matched_jobs"]) == 1
    assert final_state["matched_jobs"][0].job_title == "Python Engineer"
    assert final_state["matched_jobs"][0].score == 0.5  # Fallback score since Gemini wasn't fully mocked for scoring


@patch("src.agents.nodes.genai.GenerativeModel")
def test_agent_self_correction_loop(mock_model_cls, mock_settings, mock_vector_store):
    """Verify that the agent loops back to self-correct when validation errors occur."""
    mock_model = MagicMock()
    
    mock_class_response = MagicMock()
    mock_class_response.text = '{"is_resume": true}'
    
    # First response: invalid email and missing skills
    response_invalid = MagicMock()
    response_invalid.text = json.dumps({
        "personal_info": {
            "name": "Jane Smith",
            "email": "invalid_email_format",
            "phone": "555-0211",
            "location": "NY"
        },
        "education": [],
        "experience": [],
        "skills": []
    })
    
    # Second response: corrected data
    response_corrected = MagicMock()
    response_corrected.text = json.dumps({
        "personal_info": {
            "name": "Jane Smith",
            "email": "jane.smith@gmail.com",
            "phone": "555-0211",
            "location": "NY"
        },
        "education": [],
        "experience": [],
        "skills": ["Python", "FastAPI"]
    })

    # Feed consecutive return values to simulate correction success
    mock_model.generate_content.side_effect = [mock_class_response, response_invalid, response_corrected]
    mock_model_cls.return_value = mock_model

    # Run pipeline
    final_state = run_agentic_pipeline(
        document_content="Jane Smith can be reached at jane.smith@gmail.com. She knows Python.",
        document_id="dummy_sha256_loop"
    )

    # Assert self-correction occurred and succeeded
    assert final_state["revision_count"] == 2
    assert len(final_state["validation_errors"]) == 0
    assert final_state["extracted_data"].personal_info.email == "jane.smith@gmail.com"
    assert "FastAPI" in final_state["extracted_data"].skills


@patch("src.agents.nodes.genai.GenerativeModel")
def test_agent_max_revisions_termination(mock_model_cls, mock_settings, mock_vector_store):
    """Verify that the agent exits the self-correction cycle after reaching max revisions."""
    mock_model = MagicMock()
    
    mock_class_response = MagicMock()
    mock_class_response.text = '{"is_resume": true}'
    
    # Repeatedly return invalid data (missing email & skills)
    response_invalid = MagicMock()
    response_invalid.text = json.dumps({
        "personal_info": {
            "name": "Broken Candidate",
            "email": "",
            "phone": "",
            "location": ""
        },
        "education": [],
        "experience": [],
        "skills": []
    })
    
    # Classification -> invalid -> invalid -> invalid
    mock_model.generate_content.side_effect = [mock_class_response, response_invalid, response_invalid, response_invalid, response_invalid]
    mock_model_cls.return_value = mock_model

    # Run pipeline
    final_state = run_agentic_pipeline(
        document_content="Just some unstructured noise.",
        document_id="dummy_sha256_max"
    )

    # Assert that it stopped at MAX_REVISION_COUNT (which is configured to 2 in mock_settings)
    assert final_state["revision_count"] == 2
    # Errors remain in state but pipeline terminated and matched jobs (even with low quality)
    assert len(final_state["validation_errors"]) > 0
    assert "Candidate email is missing or empty." in final_state["validation_errors"]
    assert "At least one skill must be extracted." in final_state["validation_errors"]


def test_agent_missing_api_key(monkeypatch):
    """Verify that AgentException is raised when GEMINI_API_KEY is not set."""
    monkeypatch.setenv("GEMINI_API_KEY", "")
    from src.core.config.config import reset_settings
    reset_settings()

    with pytest.raises(AgentException, match="GEMINI_API_KEY is not set"):
        run_agentic_pipeline(
            document_content="Candidate info",
            document_id="hash123"
        )


@patch("src.agents.nodes.genai.GenerativeModel")
def test_agent_halts_on_non_resume(mock_model_cls, mock_settings):
    """Verify that the agent halts execution early if document is not a resume."""
    mock_model = MagicMock()
    
    mock_class_response = MagicMock()
    mock_class_response.text = '{"is_resume": false}'
    
    mock_model.generate_content.return_value = mock_class_response
    mock_model_cls.return_value = mock_model

    final_state = run_agentic_pipeline(
        document_content="Today's Lunch Special: Pizza and Pasta.",
        document_id="restaurant_menu"
    )

    # Agent should halt after classify_document and not proceed to extract_resume
    assert final_state["is_resume"] is False
    assert final_state["extracted_data"] is None
    assert final_state["revision_count"] == 0
    assert len(final_state["matched_jobs"]) == 0
