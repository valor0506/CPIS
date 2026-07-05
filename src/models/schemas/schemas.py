"""Document schemas for CPIS.

Defines the structure of ingested documents and their metadata to ensure
type safety and consistency across the pipeline.
"""

from typing import Dict, Any, Optional, List
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


class PersonalInfo(BaseModel):
    """Personal contact details extracted from the resume."""

    name: Optional[str] = Field(None, description="Candidate's full name.")
    email: Optional[str] = Field(None, description="Candidate's email address.")
    phone: Optional[str] = Field(None, description="Candidate's phone number.")
    location: Optional[str] = Field(None, description="Candidate's physical location/address.")

    model_config = ConfigDict(frozen=True)


class Education(BaseModel):
    """Education history details."""

    degree: Optional[str] = Field(None, description="Degree or certificate name (e.g., B.S., M.S., Ph.D.).")
    major: Optional[str] = Field(None, description="Field of study or major.")
    institution: Optional[str] = Field(None, description="Name of the university, college, or school.")
    graduation_year: Optional[int] = Field(None, description="Year of graduation or expected graduation.")

    model_config = ConfigDict(frozen=True)


class Experience(BaseModel):
    """Work experience history details."""

    job_title: Optional[str] = Field(None, description="Designation or job title.")
    company: Optional[str] = Field(None, description="Name of the company or employer.")
    duration: Optional[str] = Field(None, description="Employment duration (e.g., '2 years', '2020-2022').")
    description: Optional[str] = Field(None, description="Summary of responsibilities and achievements.")

    model_config = ConfigDict(frozen=True)


class ResumeSchema(BaseModel):
    """Structured candidate data extracted from a resume document."""

    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


class JobMatchResult(BaseModel):
    """Represents a job match result from a vector database query."""

    job_id: str = Field(..., description="Unique identifier for the matched job/chunk.")
    score: float = Field(..., description="Semantic alignment/similarity score.")
    job_title: Optional[str] = Field(None, description="Title of the matched job position.")
    company: Optional[str] = Field(None, description="Company offering the job position.")
    snippet: str = Field(..., description="Snippet of the matching job text.")

    model_config = ConfigDict(frozen=True)

