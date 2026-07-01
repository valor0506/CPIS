"""Unit tests for ChromaVectorStore."""

import shutil
import tempfile
from pathlib import Path

import pytest

from src.core.config.config import Settings
from src.models.schemas.schemas import DocumentChunk
from src.storage.vector_store import ChromaVectorStore


@pytest.fixture
def temp_chroma_dir():
    """Create a temporary directory for ChromaDB storage and clean it up after tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


def test_chroma_vector_store_flow(temp_chroma_dir):
    """Verify that ChromaVectorStore successfully adds, queries, and deletes document chunks."""
    # Configure test settings to point to the temporary directory and disable cloud embeddings
    test_settings = Settings(
        VECTOR_DB_PATH=str(Path(temp_chroma_dir) / "chroma"),
        GEMINI_API_KEY=None,  # Force local SentenceTransformer mode
    )

    store = ChromaVectorStore(collection_name="test_collection", settings=test_settings)

    # 1. Prepare dummy chunks
    chunk1 = DocumentChunk(
        id="hash_fox_chunk_0",
        text="The quick brown fox jumps over the lazy dog.",
        metadata={"sha256": "hash_fox", "chunk_index": 0, "source_path": "fox.pdf"},
    )
    chunk2 = DocumentChunk(
        id="hash_ai_chunk_0",
        text="Artificial intelligence and neural networks are transforming modern computing pipelines.",
        metadata={"sha256": "hash_ai", "chunk_index": 0, "source_path": "ai.pdf"},
    )

    # 2. Add chunks to database
    store.add_chunks([chunk1, chunk2])

    # 3. Test Similarity Search
    # Query matching chunk1 context
    results = store.similarity_search("Tell me about a dog or a fox jumping.", k=1)
    assert len(results) == 1
    assert "fox" in results[0].text
    assert results[0].metadata["sha256"] == "hash_fox"

    # Query matching chunk2 context
    results_ai = store.similarity_search("neural network computing architectures", k=1)
    assert len(results_ai) == 1
    assert "intelligence" in results_ai[0].text
    assert results_ai[0].metadata["sha256"] == "hash_ai"

    # 4. Test deletion by document SHA-256
    store.delete_document("hash_fox")

    # Search again; the fox document should be deleted, leaving only the AI chunk
    results_post_delete = store.similarity_search("fox dog jumping", k=2)
    for res in results_post_delete:
        assert res.metadata["sha256"] != "hash_fox"
