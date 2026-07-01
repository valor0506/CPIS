# CPIS Workflow Review, Log Audit, and Git Guide

This guide provides the necessary resources to commit your changes, review logs, and audit the error-handling mechanisms built during Phase 2 (RAG & Storage Layer).

---

## 1. Suggested Git Commit Messages

To maintain a clean commit history, you can stage and commit Phase 2 changes either in one logical block or in separate commits. Here are the suggested command sequences:

### Option A: Separate Granular Commits (Recommended for clear history)

```bash
# 1. Commit the schema changes
git add src/models/schemas/schemas.py
git commit -m "feat(schemas): add DocumentChunk Pydantic model for vector indexing"

# 2. Commit the chunker logic and tests
git add src/ingestion/parsers/chunker.py src/tests/test_chunker.py
git commit -m "feat(ingestion): implement recursive-character DocumentChunker and tests"

# 3. Commit the vector storage logic and tests
git add src/storage/vector_store.py src/tests/test_vector_store.py
git commit -m "feat(storage): integrate ChromaDB and local/Gemini EmbeddingsProvider with tests"

# 4. Commit the pipeline coordinator and integration tests
git add src/ingestion/pipeline.py src/tests/test_pipeline.py
git commit -m "feat(pipeline): implement IngestionPipeline coordinator with integration tests"
```

### Option B: Single Combined Commit

If you prefer to stage everything at once:
```bash
git add src/ models/ schemas/ ingestion/ storage/ tests/
git commit -m "feat(rag): implement Phase 2 text chunking, ChromaDB integration, and end-to-end ingestion pipeline"
```

---

## 2. Log Auditing & Monitoring

Our logger ([logger.py](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/src/core/logger/logger.py)) writes formatted logs to both the terminal console and to a persistent file specified in settings (default: `logs/cpis.log`).

### How to Live-Monitor Logs in Real-time

#### A. In PowerShell (VS Code Terminal)
Use the `Get-Content` utility with the `-Wait` flag (equivalent to Unix `tail -f`):
```powershell
Get-Content -Path logs/cpis.log -Wait -Tail 20
```

#### B. In Git Bash / WSL
```bash
tail -f logs/cpis.log
```

#### C. Formatting Audit
Every log entry contains the timestamp, log level, originating logger name, source file name, line number, and message:
```text
[2026-07-01 19:28:40,123] [INFO] [vector_store] [vector_store.py:105] - Connected to ChromaDB collection 'cpis_documents' at path 'data/chroma'
```

---

## 3. Workflow & Error-Handling Audit

Here is a review of the data flow and how the system behaves when errors are encountered at each stage:

```
[Raw File Path]
       │
       ▼
 1. IngestionPipeline.ingest_file(file_path)
       │
       ├──► 2. PDFDocumentLoader.load()
       │        ├── Calls PDFFileValidator.validate()
       │        │     * Checks file signature, size limit, type.
       │        │     * On error: raises ValidationException.
       │        │
       │        ├── Extracts pages & generates SHA-256 fingerprint.
       │        │     * Checks if encrypted.
       │        │     * On error/encryption: raises IngestionException.
       │        │
       │        └── Returns Document DTO.
       │
       ├──► 3. StandardDocumentParser.parse()
       │        ├── Cleans control chars and normalizes whitespace.
       │        └── On error (e.g. empty output): raises IngestionException.
       │
       ├──► 4. DocumentChunker.split_document()
       │        ├── Cuts cleaned text into overlapping intervals.
       │        └── Returns List[DocumentChunk].
       │
       └──► 5. ChromaVectorStore.add_chunks()
                ├── Calls EmbeddingsProvider
                │     * Case A (Key set): Call Google Gemini API.
                │       - Network Error / Invalid Key: raises IngestionException.
                │     * Case B (No key): Initialize SentenceTransformer.
                │       - Model Load/Inference Error: raises IngestionException.
                │
                ├── Deletes existing chunks with matching sha256.
                │     * On DB Error: raises IngestionException.
                │
                └── Writes chunks & vectors into ChromaDB.
                      * On DB Error: raises IngestionException.
```

### Key Failure Modes & Security Safeguards:

| Step / Component | What Could Go Wrong | System Safeguard | Raised Exception |
| :--- | :--- | :--- | :--- |
| **Validator** | Uploaded file is actually a renamed executable or script (e.g. `malware.sh` renamed to `resume.pdf`). | Performs binary header check for `%PDF` magic bytes. | `ValidationException` |
| **Loader** | PDF document has security password protection enabled. | Loader attempts to read pages; catches decryption failure. | `IngestionException` |
| **Embeddings (Gemini)** | Gemini API Key is expired, invalid, or rate-limited. | EmbeddingsProvider catches network exceptions from `google.generativeai`. | `IngestionException` |
| **Embeddings (Local)** | CPU/Memory exhaustion during sentence-transformer generation. | Try/except block catches run-time model issues. | `IngestionException` |
| **Vector Store** | Duplicate indexing of the same resume file. | The pipeline deletes any existing chunks referencing the file's SHA-256 hash *prior* to inserting the new ones. | None (Safely deduplicated) |
| **ChromaDB Client** | File locks or folder permission errors when writing to `VECTOR_DB_PATH`. | Catches database write errors from the Chroma client. | `IngestionException` |
