"""Ingestion pipeline coordinator for CPIS.

Integrates file validation, loading, text parsing, chunking,
and vector database indexing into a unified execution flow.
"""

from pathlib import Path
from typing import Optional

from src.core.logger.logger import setup_logger
from src.ingestion.loaders.pdf_loader import PDFDocumentLoader
from src.ingestion.parsers.chunker import DocumentChunker
from src.ingestion.parsers.document_parser import StandardDocumentParser
from src.ingestion.validators.file_validator import PDFFileValidator
from src.storage.vector_store import BaseVectorStore, ChromaVectorStore

logger = setup_logger("ingestion_pipeline")


class IngestionPipeline:
    """Coordinates the full document ingestion process from raw file to vector store."""

    def __init__(
        self,
        validator: Optional[PDFFileValidator] = None,
        loader: Optional[PDFDocumentLoader] = None,
        parser: Optional[StandardDocumentParser] = None,
        chunker: Optional[DocumentChunker] = None,
        vector_store: Optional[BaseVectorStore] = None,
    ) -> None:
        """Initialize the pipeline with component instances (allows dependency injection)."""
        self.validator = validator or PDFFileValidator()
        self.loader = loader or PDFDocumentLoader(validator=self.validator)
        self.parser = parser or StandardDocumentParser()
        self.chunker = chunker or DocumentChunker()
        self.vector_store = vector_store or ChromaVectorStore()

    def ingest_file(self, file_path: Path) -> str:
        """Execute the ingestion flow: validate, load, parse, chunk, and index into vector store.

        Args:
            file_path: Absolute path to the PDF document.

        Returns:
            str: SHA-256 fingerprint of the ingested document on success.
        """
        logger.info(f"Initiating ingestion pipeline for: {file_path}")

        # 1. Load document (internally validates the file)
        document = self.loader.load(file_path)

        # 2. Parse and sanitize text
        cleaned_document = self.parser.parse(document)

        # 3. Split into overlapping text chunks
        chunks = self.chunker.split_document(cleaned_document)

        # 4. Persistence with deduplication:
        # To prevent duplicate/stale chunks from being indexed, delete any existing
        # records sharing the same document SHA-256 before inserting the new ones.
        sha256 = cleaned_document.metadata.sha256
        self.vector_store.delete_document(sha256)
        self.vector_store.add_chunks(chunks)

        logger.info(f"Ingestion successful for {file_path}. Document SHA-256: {sha256}")
        return sha256
