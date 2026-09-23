"""FastAPI Backend Bridge for CPIS Phases 1-3.

Provides REST endpoints to upload resumes (Phase 1),
query vector embeddings & chunks (Phase 2),
and execute the LangGraph self-correcting agent pipeline (Phase 3).
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.core.logger.logger import setup_logger
from src.ingestion.pipeline import IngestionPipeline
from src.ingestion.loaders.pdf_loader import PDFDocumentLoader
from src.ingestion.parsers.document_parser import StandardDocumentParser
from src.ingestion.parsers.chunker import DocumentChunker
from src.storage.vector_store import ChromaVectorStore
from src.agents.graph import run_agentic_pipeline

logger = setup_logger("api_server")

app = FastAPI(
    title="CPIS Career Path Intelligence API",
    description="Interactive backend bridge for CPIS Phases 1, 2, and 3",
    version="1.0.0",
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VectorQueryRequest(BaseModel):
    query: str = Field(..., description="Query text to search across indexed chunks")
    top_k: int = Field(default=3, description="Number of top chunks to retrieve")


class AgentRunRequest(BaseModel):
    document_content: str = Field(..., description="Raw parsed text content of the resume")
    document_id: str = Field(..., description="SHA-256 fingerprint reference")


@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    """Health check endpoint providing status and system readiness."""
    return {
        "status": "healthy",
        "service": "CPIS Agentic Intelligence Engine",
        "phases_active": [
            "Phase 1: Deterministic Document Ingestion",
            "Phase 2: Semantic Chunking & Vector Store (ChromaDB)",
            "Phase 3: LangGraph Agentic Pipeline with Self-Correction"
        ]
    }


@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Ingest a PDF resume through Phase 1 and Phase 2 pipelines."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir) / file.filename

    try:
        # Save file to temporary disk
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Execute Ingestion Pipeline (validates, parses, chunks, and persists to ChromaDB)
        pipeline = IngestionPipeline()
        sha256 = pipeline.ingest_file(temp_path)

        # 2. Extract inspection metadata for UI inspection
        loader = PDFDocumentLoader()
        raw_doc = loader.load(temp_path)
        parser = StandardDocumentParser()
        cleaned_doc = parser.parse(raw_doc)
        chunker = DocumentChunker()
        chunks = chunker.split_document(cleaned_doc)

        return {
            "status": "success",
            "filename": file.filename,
            "sha256": sha256,
            "file_size_bytes": raw_doc.metadata.file_size_bytes,
            "page_count": raw_doc.metadata.page_count,
            "content_length": len(cleaned_doc.content),
            "content_preview": cleaned_doc.content[:800],
            "total_chunks": len(chunks),
            "chunks": [
                {
                    "id": chunk.id,
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                }
                for chunk in chunks[:6]
            ],
        }

    except Exception as e:
        logger.error(f"Error processing uploaded resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/vector-preview")
def vector_search(payload: VectorQueryRequest) -> Dict[str, Any]:
    """Search ChromaDB vector store for relevant chunks matching a query."""
    try:
        store = ChromaVectorStore()
        results = store.similarity_search(query=payload.query, top_k=payload.top_k)
        return {
            "status": "success",
            "query": payload.query,
            "count": len(results),
            "matches": [
                {
                    "id": match.id,
                    "text": match.text,
                    "metadata": match.metadata,
                }
                for match in results
            ],
        }
    except Exception as e:
        logger.error(f"Vector search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/run-agent")
def run_agent(payload: AgentRunRequest) -> Dict[str, Any]:
    """Execute LangGraph agent workflow with resume content."""
    try:
        final_state = run_agentic_pipeline(
            document_content=payload.document_content,
            document_id=payload.document_id,
        )

        extracted_data_dump = None
        if final_state.get("extracted_data"):
            extracted_data_dump = final_state["extracted_data"].model_dump()

        matched_jobs_dump = []
        for job in final_state.get("matched_jobs", []):
            if hasattr(job, "model_dump"):
                matched_jobs_dump.append(job.model_dump())
            elif isinstance(job, dict):
                matched_jobs_dump.append(job)

        return {
            "status": "success",
            "document_id": payload.document_id,
            "is_resume": final_state.get("is_resume"),
            "extracted_data": extracted_data_dump,
            "validation_errors": final_state.get("validation_errors", []),
            "revision_count": final_state.get("revision_count", 0),
            "matched_jobs": matched_jobs_dump,
        }
    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

