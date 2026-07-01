"""Integration tests for the IngestionPipeline."""

import shutil
import tempfile
from pathlib import Path

import pytest

from src.core.config.config import Settings
from src.ingestion.loaders.pdf_loader import PDFDocumentLoader
from src.ingestion.pipeline import IngestionPipeline
from src.models.schemas.schemas import Document, DocumentMetadata
from src.storage.vector_store import ChromaVectorStore


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for integration testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


def test_pipeline_integration_flow(temp_workspace):
    """Verify the integration flow of IngestionPipeline using mock loader + real test db."""
    workspace_path = Path(temp_workspace)
    db_path = str(workspace_path / "chroma")

    # Set up test configuration using local embeddings
    test_settings = Settings(
        VECTOR_DB_PATH=db_path,
        GEMINI_API_KEY=None,
    )

    test_pdf = workspace_path / "test.pdf"

    # Set up mock Document output
    metadata = DocumentMetadata(
        source_path=str(test_pdf),
        file_size_bytes=100,
        page_count=1,
        sha256="mock_sha256_pipeline_test",
    )
    mock_document = Document(
        content="Artificial intelligence models learn from massive amounts of data. This pipeline parses documents.",
        metadata=metadata,
    )

    # Subclass PDFDocumentLoader to mock document loading
    class MockDocumentLoader(PDFDocumentLoader):
        def load(self, file_path: Path) -> Document:
            return mock_document

    # Initialize store and pipeline
    vector_store = ChromaVectorStore(collection_name="pipeline_test_col", settings=test_settings)
    pipeline = IngestionPipeline(
        loader=MockDocumentLoader(),
        vector_store=vector_store,
    )

    # 1. Run ingestion
    sha256 = pipeline.ingest_file(test_pdf)
    assert sha256 == "mock_sha256_pipeline_test"

    # 2. Query vector db to verify the content was parsed, chunked, and indexed correctly
    search_results = vector_store.similarity_search("artificial intelligence models", k=1)
    assert len(search_results) == 1
    assert "artificial intelligence" in search_results[0].text.lower()
    assert search_results[0].metadata["sha256"] == "mock_sha256_pipeline_test"
