# CPIS Codebase Reference Guide: Phase 1 (Foundation & Ingestion)

This guide provides a comprehensive breakdown of all files, workflows, terminal commands, and testing setups built during **Phase 1: Document Ingestion Layer**. Use this to explain the codebase in detail during project presentations or job interviews.

---

## 1. Complete File Directory & Role Definitions

### A. Root Configuration Files
1.  **`[.gitignore](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/.gitignore)`**
    *   **What it does**: Excludes temporary files (logs, databases, `.pytest_cache`, virtual environments like `venv`) and secrets (`.env`) from version control.
2.  **`[requirements.txt](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/requirements.txt)`**
    *   **What it does**: Defines the third-party dependencies of the stack (FastAPI, Pydantic, pypdf, pytest, sentence-transformers, chromadb, langgraph, deepeval, etc.).

### B. Core Foundation (`src/core/`)
3.  **`[exceptions.py](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/src/core/exceptions/exceptions.py)`**
    *   **Role**: Standardizes runtime error classifications.
    *   **Details**: Inherits from Python's base `Exception` to create `CPISException`. It then subclasses this into `ConfigException`, `IngestionException`, and `ValidationException`.
4.  **`[config.py](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/src/core/config/config.py)`**
    *   **Role**: Handles type-safe setting initialization.
    *   **Details**: Uses Pydantic's `BaseModel` and `ConfigDict(frozen=True)` to create an immutable `Settings` class that parses environment variables. It implements a thread-safe singleton cache accessor `get_settings()` and a testing helper `reset_settings()`.
5.  **`[logger.py](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/src/core/logger/logger.py)`**
    *   **Role**: Sets up console and rotating file-based logging.
    *   **Details**: Sets the global level (`LOG_LEVEL` like `INFO` or `DEBUG`) and formats log events with timestamps, file names, and line numbers.

### C. Data Models (`src/models/`)
6.  **`[schemas.py](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/src/models/schemas/schemas.py)`**
    *   **Role**: Declares immutable data transfer objects (DTOs).
    *   **Details**:
        *   `DocumentMetadata`: Holds standard attributes (source path, file size in bytes, page count, SHA-256 fingerprint, and a generic dictionary for custom keys).
        *   `Document`: Ties raw extracted text content (`content`) to the verified `DocumentMetadata`.

### D. Ingestion Engine (`src/ingestion/`)
7.  **`[file_validator.py](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/src/ingestion/validators/file_validator.py)`**
    *   **Role**: Performs validation on incoming documents.
    *   **Details**: Defines the `BaseFileValidator` abstract class and a concrete `PDFFileValidator` that checks file existence, size constraints, extensions, and checks binary headers for the `%PDF` signature.
8.  **`[pdf_loader.py](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/src/ingestion/loaders/pdf_loader.py)`**
    *   **Role**: Reads binary files and extracts text.
    *   **Details**: Subclasses `BaseDocumentLoader`. It uses PyPDF to extract text from pages, checks for encryption, hashes files to generate a SHA-256 code, and returns a `Document` DTO.
9.  **`[document_parser.py](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/src/ingestion/parsers/document_parser.py)`**
    *   **Role**: Formats and cleans text extracted from files.
    *   **Details**: Subclasses `BaseDocumentParser`. It uses regular expressions to remove non-printable ASCII characters, compress multi-spaces and tabs into single spaces, and cap consecutive empty newlines at two.

---

## 2. The Step-by-Step Ingestion Workflow

```
[Target File] 
      │
      ▼
1. PDFFileValidator.validate(file_path)
      ├── Checks file existence & types
      ├── Checks size limit (e.g. 10MB)
      ├── Checks .pdf extension
      └── Checks magic bytes header (%PDF)
      │
      ▼
2. PDFDocumentLoader.load(file_path)
      ├── Reads and parses pages using PyPDF
      ├── Extracts text page by page
      ├── Computes file size & SHA-256 checksum
      └── Instantiates Document & DocumentMetadata DTOs
      │
      ▼
3. StandardDocumentParser.parse(document)
      ├── Cleans non-printable control characters
      ├── Compresses spaces/tabs and normalizes linebreaks
      └── Returns a finalized, clean Document DTO
```

---

## 3. Terminal Commands Run & Their Purpose

Here is the exact history of commands run in your shell and what they accomplished:

1.  **`git init`**
    *   *Purpose*: Initialized an empty Git repository in the local `agentic-ai/` folder, replacing the home directory tracking context.
2.  **`python -m venv venv`**
    *   *Purpose*: Built a clean, isolated virtual environment to hold dependencies, keeping global Python modules from conflicting.
3.  **`.\venv\Scripts\pip install -r requirements.txt`**
    *   *Purpose*: Installed all third-party libraries (FastAPI, PyPDF, Pydantic, pytest, etc.) directly into the `venv` virtual environment.
4.  **`.\venv\Scripts\python -m pytest src/tests/`**
    *   *Purpose*: Ran our test suite to verify that code changes comply with our test specs.
5.  **`git add .`**
    *   *Purpose*: Staged all new and modified source files, tests, and configurations to prepare for committing.
6.  **`git commit -m "..."`**
    *   *Purpose*: Recorded staged files into git history (we made distinct commits for feature development and the Pydantic v2 warning cleanups).
7.  **`git branch -M main`**
    *   *Purpose*: Renamed the default git branch to `main`.
8.  **`git remote add origin https://github.com/valor0506/CPIS`**
    *   *Purpose*: Hooked up the local repository to your remote GitHub repository.
9.  **`git push -u origin main`**
    *   *Purpose*: Pushed the local main branch up to GitHub and configured it for tracking.

---

## 4. What is Being Verified in `tests/`?

Each test file in the `src/tests/` folder runs automated checks on our code to ensure that it fails gracefully for bad data and succeeds for valid files.

### A. `[test_config.py](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/src/tests/test_config.py)` (3 Tests)
*   **`test_default_settings`**: Verifies that when no environment variables are set, Settings loads standard defaults (e.g. `FILE_UPLOAD_MAX_SIZE_MB = 10`).
*   **`test_settings_override`**: Verifies that environment overrides (set via monkeypatch) successfully overwrite defaults.
*   **`test_invalid_settings_type`**: Verifies that setting invalid types (e.g. string for max size limit) raises a `ConfigException`.

### B. `[test_file_validator.py](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/src/tests/test_file_validator.py)` (7 Tests)
*   **`test_validator_file_not_found`**: Verifies `ValidationException` is raised when file path does not exist.
*   **`test_validator_path_is_directory`**: Verifies directory paths raise `ValidationException`.
*   **`test_validator_invalid_extension`**: Verifies non-PDF file extensions (like `.txt`) raise `ValidationException`.
*   **`test_validator_empty_file`**: Verifies 0-byte files raise `ValidationException`.
*   **`test_validator_oversized_file`**: Sets size limit to 0MB and checks that files containing bytes raise a size error.
*   **`test_validator_invalid_magic_bytes`**: Verifies files renamed to `.pdf` that do not start with `%PDF` bytes raise `ValidationException`.
*   **`test_validator_valid_pdf`**: Verifies a valid PDF byte signature passes validator check.

### C. `[test_pdf_loader.py](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/src/tests/test_pdf_loader.py)` (3 Tests)
*   **`test_loader_validation_failure`**: Verifies that if the validator throws an exception, the loader fails fast and raises an `IngestionException`.
*   **`test_loader_encrypted_pdf`**: Mocks an encrypted PDF and asserts that the loader raises `IngestionException`.
*   **`test_loader_successful_parsing`**: Mocks `pypdf.PdfReader` pages to output simulated text, asserting that the loaded `Document` DTO aggregates text and metadata correctly.

### D. `[test_document_parser.py](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/src/tests/test_document_parser.py)` (5 Tests)
*   **`test_parser_normalizes_whitespace`**: Verifies that multiple spaces and tabs are compressed into a single space.
*   **`test_parser_normalizes_newlines`**: Verifies that consecutive blank lines are capped at two newlines.
*   **`test_parser_removes_control_characters`**: Verifies that non-printable characters are stripped.
*   **`test_parser_trims_flanking_whitespace`**: Verifies leading/trailing flanking spaces/lines are trimmed.
*   **`test_parser_raises_for_empty_cleaned_content`**: Verifies that if cleaning result is blank, it raises `IngestionException`.
