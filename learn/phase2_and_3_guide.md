# CPIS Architecture Guide: Phase 2 & Phase 3

> **Philosophy**: Spec-Driven Development (SDD) over Vibe Coding. Every component is rigorously typed, tested with deterministic pytest suites, and mapped directly to pipeline states.

---

## 1. Phase 2: Chunking, Embeddings & Vector Storage (ChromaDB)

### The Core Objective
Raw text from a PDF resume cannot be fed in one huge prompt to an LLM without losing fine-grained positional accuracy, exceeding context limits, and wasting tokens. Phase 2 splits extracted resume text into overlapping semantic chunks, computes dense vector representations, and indexes them in an embedded vector database (**ChromaDB**).

### Component Breakdown

#### A. Document Chunker (`src/vector_store/chunker.py`)
- **Strategy**: Recursive Character Splitting with Overlap.
- **Parameters**:
  - `chunk_size = 500`: Each chunk contains at most 500 characters.
  - `chunk_overlap = 50`: A 50-character sliding window ensures sentences or terms split at boundaries maintain continuity.
- **Metadata Preservation**: Every chunk retains the original document's SHA-256 fingerprint, page origin, and chunk index (`chunk_id = f"{sha256}_c{i}"`).

#### B. Dense Embeddings Provider (`src/vector_store/embeddings.py`)
- **Model**: `all-MiniLM-L6-v2` via HuggingFace `sentence-transformers`.
- **Dimensions**: 384-dimensional dense vectors.
- **Why MiniLM?**: Runs locally on CPU with zero latency (<15ms per batch), completely free, and optimized for semantic similarity.

#### C. ChromaDB Vector Store (`src/vector_store/chroma.py`)
- **Engine**: ChromaDB embedded persistent client (`./data/chroma_db`).
- **Collections**: Default `resumes` collection with cosine similarity distance metric.
- **Search Method**: Nearest Neighbor (`k-NN`) semantic search querying by text similarity:
  ```python
  results = collection.query(
      query_texts=["5 years of Python backend and Docker"],
      n_results=5
  )
  ```

---

## 2. Phase 3: LangGraph Agentic Pipeline with Self-Correction

### The Core Objective
Traditional LLM chains are linear: Prompt -> LLM -> Parse -> Fail.
An **Agentic Workflow** introduces **state, decision-making, cyclic validation, and self-correction**.

### LangGraph Architecture (`src/agents/`)

```
   [START]
      │
      ▼
┌──────────────┐
│ classify_doc │ ──── Not a Resume? ───► [END (Rejected)]
└──────────────┘
      │ Valid Resume
      ▼
┌──────────────┐
│ extract_data │ ◄───────────────────────┐
└──────────────┘                         │
      │                                  │
      ▼                                  │
┌──────────────┐                         │ Retry (Cycle < 3)
│ validate_doc │ ──── Missing Fields? ───┘
└──────────────┘
      │ Validated
      ▼
┌──────────────┐
│  match_jobs  │
└──────────────┘
      │
      ▼
   [END]
```

### State Definition (`src/agents/state.py`)
```python
class AgentState(TypedDict):
    document_id: str
    text: str
    doc_type: str                   # 'resume', 'job_description', 'other'
    is_valid_resume: bool
    candidate: Optional[ResumeSchema]
    validation_errors: List[str]
    correction_attempts: int        # Guard against infinite loops (max 3)
    matches: List[JobMatchResult]
```

### The Nodes (`src/agents/nodes.py`)
1. **`classify_document`**: Evaluates document content. If the text does not contain employment/academic markers, it flags `is_valid_resume = False` and aborts early.
2. **`extract_resume`**: Uses Pydantic schemas (`ResumeSchema`, `PersonalInfo`, `Experience`, `Education`) with structured LLM output (or robust deterministic parser fallback) to extract candidate details.
3. **`validate_data`**: Checks business rules:
   - Does candidate have an email or contact?
   - Are skills or experience listed?
   - If invalid and `correction_attempts < 3`, appends feedback and routes back to `extract_resume`.
4. **`match_job`**: Takes extracted skills and queries ChromaDB vector embeddings of available jobs, computing weighted relevance scores (0.0 to 1.0).

---

## 3. Terminal Verification Commands

```powershell
# 1. Run all 28 automated tests across Phase 1, Phase 2, and Phase 3
.\venv\Scripts\python -m pytest src/tests/ -v

# 2. Start FastAPI bridge server
.\venv\Scripts\python -m uvicorn src.api.server:app --port 8000 --reload

# 3. Test Vector Store & Agent Endpoints via curl/PowerShell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health"
```
