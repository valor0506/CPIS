# Career Pipeline Intelligence System (CPIS)

CPIS is a stateful, multi-agent AI system designed to automate the ingestion, parsing, verification, semantic indexing, and processing of career documents (such as resumes, portfolios, and job postings).

Built on top of **FastAPI** and **LangGraph**, it enforces high engineering standards (Single Responsibility Principle, Dependency Injection, Pydantic type safety) and optimizes document ingestion for Retrieval-Augmented Generation (RAG).

---

## Tech Stack
*   **Backend Framework**: FastAPI & Uvicorn
*   **State Machine/Agentic Layer**: LangGraph
*   **Validation & Serialization**: Pydantic v2
*   **Database & Vector Store**: ChromaDB
*   **Embeddings Engine**: Sentence-Transformers (`all-MiniLM-L6-v2` local) & Google Gemini (`text-embedding-004` API)
*   **PDF Extraction**: PyPDF
*   **Testing**: Pytest

---

## Key Features

### Phase 1: Ingestion & Validation
*   **Header Byte Validation**: Checks files for the `%PDF` signature to ensure only valid binaries are processed.
*   **SHA-256 Deduplication**: Calculates file fingerprints to prevent duplicate processing.
*   **Text Normalization**: Standardizes whitespace, removes control characters, and optimizes token density.

### Phase 2: RAG & Storage Layer
*   **Overlapping Chunker**: Splits text recursive-character wise to keep sentence context.
*   **ChromaDB Vector Store**: Persists document vectors and filters out old versions automatically.
*   **Hybrid Embeddings**: Runs completely offline using local embeddings, or hooks into Google Gemini embeddings API dynamically.

---

## Directory Structure
```
agentic-ai/
├── src/
│   ├── core/
│   │   ├── config/          # Pydantic v2 Configuration
│   │   ├── exceptions/      # Custom exception classes
│   │   └── logger/          # Application logging config
│   ├── ingestion/
│   │   ├── loaders/         # Document load handlers (PDF)
│   │   ├── parsers/         # Normalization & Chunker
│   │   └── validators/      # Byte & constraint validation
│   ├── models/
│   │   └── schemas/         # Immutable Pydantic models (DTOs)
│   ├── storage/
│   │   └── vector_store.py  # ChromaDB & Embeddings integration
│   └── tests/               # Pytest unit & integration suite
```

---

## Getting Started

### Installation
1. Navigate to the project directory:
   ```bash
   cd agentic-ai
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On Unix/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
FILE_UPLOAD_MAX_SIZE_MB=10
VECTOR_DB_PATH=data/chroma
```

### Running Tests
Execute the unit and integration tests:
```bash
python -m pytest src/tests/
```
