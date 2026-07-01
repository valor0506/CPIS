"""Document schemas for CPIS.

Defines the structure of ingested documents and their metadata to ensure
type safety and consistency across the pipeline.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class DocumentMetadata(BaseModel):
    """Metadata for an ingested document."""

    source_path: str = Field(..., description="The original file path or URL of the document.")
    file_size_bytes: int = Field(..., description="Size of the file in bytes.")
    page_count: int = Field(default=0, description="Total number of pages parsed.")
    sha256: str = Field(..., description="SHA-256 checksum of the file to prevent duplicate processing.")
    custom_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional custom metadata fields.")

    model_config = ConfigDict(frozen=True)


class Document(BaseModel):
    """Represents a validated, parsed document inside CPIS."""

    content: str = Field(..., description="The main text contents of the document.")
    metadata: DocumentMetadata = Field(..., description="Associated document metadata.")

    model_config = ConfigDict(frozen=True)


class DocumentChunk(BaseModel):
    """Represents a single chunk of an ingested document."""

    id: str = Field(..., description="Unique identifier for the chunk, e.g., {sha256}_chunk_{index}.")
    text: str = Field(..., description="Text content of the chunk.")
    metadata: Dict[str, Any] = Field(..., description="Metadata for the chunk, including page offsets and parent details.")

    model_config = ConfigDict(frozen=True)
