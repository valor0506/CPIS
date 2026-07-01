# Implementation Plan - CPIS Phase 2: Chunking Engine

This document outlines the design and implementation details for Phase 2 of the Career Pipeline Intelligence System (CPIS) — the **Chunking Engine**.

## User Review Required

We are building a robust chunking engine that will split long parsed documents (like resumes and job descriptions) into semantic or sized passages prior to embedding generation.
1. **Model Expansion**: We will add a new `Chunk` and `ChunkMetadata` schema to `src/models/schemas/schemas.py`.
2. **Chunking Strategies**:
   - `BaseChunker`: Abstract base class enforcing a contract for all splitters.
   - `RecursiveCharacterChunker`: Concrete class that recursively splits text based on separators (`\n\n`, `\n`, ` `, and `""`) to keep chunks within size constraints while maintaining semantic integrity (paragraphs and sentences) and preserving overlaps.

> [!IMPORTANT]
> To support company-specific interview RAG pipelines (which require page context or source line numbers), each `Chunk` will record the index bounds (`start_index`, `end_index`) of the parent text.

## Open Questions
- What is the default recommended `chunk_size` and `chunk_overlap` for resumes and job descriptions? (Proposed defaults: `chunk_size = 500` characters, `chunk_overlap = 50` characters).

---

## Proposed Changes

We will create the chunking strategies files in `src/chunking/strategies/` and update the schemas.

### Models

#### [MODIFY] [schemas.py](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/src/models/schemas/schemas.py)
- **Why this file exists**: Extends our data models to represent chunked text data.
- **What it owns**: `ChunkMetadata` and `Chunk` DTOs.
- **Inputs**: Text chunk, character indices, and parent metadata reference.
- **Outputs**: Validated Pydantic models.
- **Failure modes**: Mismatched types or indexes.

### Chunking Strategies

#### [NEW] [chunk_strategy.py](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/src/chunking/strategies/chunk_strategy.py)
- **Why this file exists**: Establishes the interface contract for any chunking strategy (e.g. character, semantic, token-based).
- **What it owns**: `BaseChunker` interface.
- **Inputs**: `Document`.
- **Outputs**: `List[Chunk]`.
- **Failure modes**: Standard contract errors.

#### [NEW] [recursive_chunker.py](file:///c:/Users/suvan/Desktop/AI%20+%20LLM%20+%20RAG/agentic-ai/src/chunking/strategies/recursive_chunker.py)
- **Why this file exists**: Implements recursive character splitting to break text at natural boundaries.
- **What it owns**: `RecursiveCharacterChunker` class.
- **Inputs**: `Document`, custom chunk size, overlap size, and optional delimiters.
- **Outputs**: `List[Chunk]` containing text segments.
- **Failure modes**: `ValidationException` when overlap is greater than or equal to chunk size.

---

## Verification Plan

### Automated Tests
We will add `src/tests/test_recursive_chunker.py` to cover:
- Edge cases (short text that fits in one chunk, empty text).
- Overlap correctness (verifying overlapping content matching).
- Handling boundary parameters (overlap >= size throws `ValidationException`).
- Delimiter behavior (splitting correctly on paragraph/sentence bounds).

We will run:
```bash
python -m pytest src/tests/
```
