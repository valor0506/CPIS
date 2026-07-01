"""Vector storage implementation for CPIS.

Interfaces with ChromaDB to persist document chunks, generate text embeddings,
and perform semantic similarity searches.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb

from src.core.config.config import get_settings
from src.core.exceptions.exceptions import IngestionException
from src.core.logger.logger import setup_logger
from src.models.schemas.schemas import DocumentChunk

logger = setup_logger("vector_store")


class EmbeddingsProvider:
    """Wrapper to provide embeddings using Google Gemini API or local sentence-transformers."""

    def __init__(self, gemini_api_key: Optional[str] = None) -> None:
        """Initialize the embeddings provider.

        If gemini_api_key is provided, use Google Generative AI embeddings (cloud).
        Otherwise, fall back to local sentence-transformers (offline).
        """
        self.gemini_api_key = gemini_api_key
        self._local_model = None

        if not self.gemini_api_key:
            logger.info("No GEMINI_API_KEY found. Initializing local SentenceTransformer (all-MiniLM-L6-v2)...")
            from sentence_transformers import SentenceTransformer

            self._local_model = SentenceTransformer("all-MiniLM-L6-v2")
        else:
            logger.info("GEMINI_API_KEY found. Using Google Generative AI Embeddings (text-embedding-004)...")
            import google.generativeai as genai

            genai.configure(api_key=self.gemini_api_key)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of document texts."""
        if not texts:
            return []

        if self.gemini_api_key:
            try:
                import google.generativeai as genai

                response = genai.embed_content(
                    model="models/text-embedding-004",
                    content=texts,
                    task_type="retrieval_document",
                )
                # Google Generative AI returns results inside 'embedding' key
                return response["embedding"]
            except Exception as e:
                raise IngestionException(f"Failed to generate Gemini embeddings: {str(e)}", original_exception=e)
        else:
            try:
                embeddings = self._local_model.encode(texts)
                return [emb.tolist() for emb in embeddings]
            except Exception as e:
                raise IngestionException(
                    f"Failed to generate local SentenceTransformer embeddings: {str(e)}", original_exception=e
                )

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query text."""
        if self.gemini_api_key:
            try:
                import google.generativeai as genai

                response = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type="retrieval_query",
                )
                return response["embedding"]
            except Exception as e:
                raise IngestionException(f"Failed to generate Gemini query embedding: {str(e)}", original_exception=e)
        else:
            try:
                embedding = self._local_model.encode(text)
                return embedding.tolist()
            except Exception as e:
                raise IngestionException(
                    f"Failed to generate local SentenceTransformer query embedding: {str(e)}", original_exception=e
                )


class BaseVectorStore(ABC):
    """Abstract Base Class for CPIS Vector Stores."""

    @abstractmethod
    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Embed and persist list of document chunks into the store."""
        pass

    @abstractmethod
    def similarity_search(self, query: str, k: int = 4) -> List[DocumentChunk]:
        """Query the vector store for semantic matches."""
        pass

    @abstractmethod
    def delete_document(self, sha256: str) -> None:
        """Delete all database records associated with the original document hash."""
        pass


class ChromaVectorStore(BaseVectorStore):
    """Concrete implementation of BaseVectorStore utilizing ChromaDB."""

    def __init__(self, collection_name: str = "cpis_documents", settings=None) -> None:
        """Initialize ChromaClient and connect to/create the target collection."""
        self.settings = settings or get_settings()
        db_path = self.settings.VECTOR_DB_PATH

        # Ensure parent folder for persistent storage exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=db_path)
        self.embeddings_provider = EmbeddingsProvider(gemini_api_key=self.settings.GEMINI_API_KEY)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        logger.info(f"Connected to ChromaDB collection '{collection_name}' at path '{db_path}'")

    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Embed and upsert chunks into the Chroma collection."""
        if not chunks:
            logger.warning("No chunks provided to store.")
            return

        ids = [c.id for c in chunks]
        texts = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]

        # Generate embeddings
        embeddings = self.embeddings_provider.embed_documents(texts)

        try:
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings,
            )
            logger.info(f"Successfully added {len(chunks)} chunks to vector store.")
        except Exception as e:
            raise IngestionException(f"ChromaDB insert failed: {str(e)}", original_exception=e)

    def similarity_search(self, query: str, k: int = 4) -> List[DocumentChunk]:
        """Find top k document chunks matching the query string semantically."""
        if not query.strip():
            return []

        # Get embedding for query
        query_embedding = self.embeddings_provider.embed_query(query)

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
            )

            # Reconstruct list of DocumentChunk DTOs from search result structure
            chunks: List[DocumentChunk] = []

            # Chroma query results format: {'ids': [[...]], 'documents': [[...]], 'metadatas': [[...]], ...}
            if results and results.get("ids") and len(results["ids"][0]) > 0:
                ids = results["ids"][0]
                documents = results["documents"][0]
                metadatas = results["metadatas"][0]

                for idx in range(len(ids)):
                    chunks.append(
                        DocumentChunk(
                            id=ids[idx],
                            text=documents[idx],
                            metadata=metadatas[idx],
                        )
                    )

            return chunks
        except Exception as e:
            raise IngestionException(f"ChromaDB query failed: {str(e)}", original_exception=e)

    def delete_document(self, sha256: str) -> None:
        """Remove all chunks tagged with the given original file hash."""
        if not sha256:
            return

        try:
            # Chroma supports dictionary-based where conditions on metadata
            self.collection.delete(where={"sha256": sha256})
            logger.info(f"Deleted all database chunks with SHA-256: {sha256}")
        except Exception as e:
            raise IngestionException(f"ChromaDB deletion failed: {str(e)}", original_exception=e)
