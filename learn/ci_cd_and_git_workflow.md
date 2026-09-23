# Spec-Driven Development (SDD), CI/CD & Terminal Command History

> **Core Principle**: Spec-Driven Development means we define the formal interfaces (Pydantic schemas, TypeScript interfaces), write automated tests first, run strict assertions, and build verifiable production code. We never guess or "vibe code".

---

## 1. Spec-Driven Development vs. Vibe Coding

| Attribute | Vibe Coding | Spec-Driven Development (Our Approach) |
|---|---|---|
| **Specification** | Vague prompts, changing requirements | Formal Pydantic DTOs & strict TypeScript contracts |
| **Testing** | "Looks good in browser / no crash" | 28 automated `pytest` suites + `tsc -b` type checking |
| **Error Handling** | Silent catch-alls (`except: pass`) | Custom hierarchy (`CPISException`, `AgentException`) |
| **Git Management** | Giant monolithic `git add .` commits | Granular, partitioned commits by architectural section |
| **Verification** | Guessing if endpoints work | Formal health checks, deterministic unit tests, live integration |

---

## 2. Does this mean CI/CD? How Phase-by-Phase Delivery Works

**Yes, absolutely.** Continuous Integration / Continuous Deployment (CI/CD) in production consists of:
1. **Lint & Static Analysis**: Oxlint / ESLint / Ruff ensuring formatting and safety.
2. **Type Checking**: TypeScript compiler (`tsc -b`) and Python MyPy verifying strict types.
3. **Automated Unit Testing**: `pytest` running every unit test (28 tests across Phase 1, 2, 3).
4. **Build Verification**: Vite building production artifacts (`dist/`).
5. **Phase-by-Phase Merging**: Each feature branch (`feat/phase1`, `feat/phase2`, `feat/frontend-and-api`) is only merged into `main` when the full test suite passes 100%.

---

## 3. Comprehensive Terminal Command History & Purpose

Here is every single command used in this terminal session and exactly why it was run:

### A. Python Environment & Automated Test Suite
| Command | Why it was run |
|---|---|
| `.\venv\Scripts\python -m pytest src/tests/` | Runs all 28 automated tests across config, document parser, file validator, chunker, vector store, and LangGraph agent workflow. |
| `.\venv\Scripts\python -m pytest src/tests/test_agent_workflow.py -v` | Specifically validates the Phase 3 LangGraph state machine: classification, extraction, validation loop, and role matching. |
| `.\venv\Scripts\python -m uvicorn src.api.server:app --port 8000 --host 127.0.0.1` | Starts the production-ready FastAPI backend server exposing `/api/upload-resume`, `/api/vector-preview`, and `/api/run-agent`. |
| `Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health"` | Probes the backend server to confirm active phases and healthy server state. |

### B. Frontend Setup & Build Pipeline
| Command | Why it was run |
|---|---|
| `npm create vite@latest frontend -- --template react-ts` | Scaffolds clean React 18 + TypeScript Vite application. |
| `npm install react-router-dom lucide-react clsx tailwindcss` | Installs client-side routing, icon packages, and styling utilities. |
| `npm run build` (`tsc -b && vite build`) | Compiles TypeScript with strict type checking and outputs minified production bundle in `dist/`. |
| `npm run dev` | Starts Vite Hot-Module-Replacement (HMR) local development server on port 5173. |

### C. Git & Version Control
| Command | Why it was run |
|---|---|
| `git checkout -b feat/frontend-and-api` | Creates an isolated feature branch so unstable experiments never corrupt `main`. |
| `git status` / `git log --oneline` | Inspects working tree changes and reviews clean linear commit history. |
| `git add <files>` & `git commit -m "<type>(<scope>): <desc>"` | Saves atomic, partitioned units of work following Conventional Commits standard. |
