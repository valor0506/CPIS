# Frontend Architecture & ABV Editorial Design Language

> **Aesthetic Blueprint**: Reverse-engineered from [ABV Firm (abvfirm.com)](https://abvfirm.com/). Built with React 18, TypeScript, and modern CSS architecture without generic AI clichés (no fuzzy glassmorphism, no fake dashboard tiles, no purple neon badges).

---

## 1. Design Language & Tokens

### Palette
- **Primary Background**: `#0B0B0B` (Deep near-black matte surface)
- **Primary Text**: `#FFFFFF` (High contrast pure white)
- **Muted Text**: `#888888` / `#555555` (Editorial sub-headers and technical labels)
- **Accent Color Block**: `#2200FF` (Solid hyper-saturated royal cobalt blue)
- **Grid Dividers**: `1px solid #1a1a1a` (Structural hairline rules)

### Typography
- **Primary Sans-Serif**: `Barlow` (Clean modernist grotesque sans-serif)
- **Technical Monospace**: `JetBrains Mono` (SHA-256 hashes, vector distances, raw JSON payloads)
- **Kickers**: `font-size: 11px`, `font-weight: 600`, `letter-spacing: 0.12em`, `text-transform: uppercase`
- **Hero Title**: `font-size: clamp(3.5rem, 6vw, 6.5rem)`, `font-weight: 900`, `line-height: 1.0`

---

## 2. Component & Page Structure

```
frontend/src/
├── index.css                # Barlow + JetBrains Mono imports, design tokens, brutalist resets
├── App.tsx                  # Client-side router configuration (React Router DOM)
├── main.tsx                 # DOM root mount
├── components/
│   └── Navbar.tsx           # Hairline bordered monochrome topbar with live status pill
└── pages/
    ├── LandingPage.tsx      # ABV split-screen hero (Dark text pane | Solid Cobalt blue block)
    ├── UploadPage.tsx       # Live PDF drag-and-drop, state-machine stepper & FastAPI POST
    └── ResultsPage.tsx      # Tabbed real data interface (Phase 1 Meta, Phase 2 Vector, Phase 3 Agent)
```

---

## 3. How the Frontend Connects to the Backend

1. **Document Upload (`POST /api/upload-resume`)**:
   - The user selects or drags a real PDF resume into `UploadPage.tsx`.
   - The file is bundled into standard `multipart/form-data` and sent to `http://localhost:8000/api/upload-resume`.
   - The FastAPI backend validates PDF magic bytes, parses text via `DocumentParser`, runs `RecursiveCharacterChunker`, indexes chunks into ChromaDB, and returns `{ sha256, filename, chunk_count, char_count, text }`.

2. **ChromaDB Semantic Search (`POST /api/vector-preview`)**:
   - In `ResultsPage.tsx` under "02 — Vector Chunks", the user can search queries like `"Kubernetes"`.
   - The backend runs vector embedding inference on the query, measures cosine distance, and returns the top matching document chunks with similarity scores.

3. **LangGraph Agentic Execution (`POST /api/run-agent`)**:
   - In `ResultsPage.tsx` under "03 — Agent Output", clicking **Execute Agent Workflow** triggers the compiled LangGraph state machine.
   - The agent classifies the document, extracts candidate skills/experience into Pydantic models, runs self-correction if validation fails, and computes ranked career matches.
