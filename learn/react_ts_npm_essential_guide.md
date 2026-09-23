# Essential Guide: NPM, TypeScript & React (Practical Cheat Sheet)

> **Context**: This guide breaks down the essential commands, mental models, and debugging techniques for **NPM**, **TypeScript**, and **React** used in this project. Use this reference whenever you are building, debugging, or running the CPIS frontend.

---

## 1. NPM (Node Package Manager) Essentials

### Core Commands
| Command | What it does | When to use it |
|---|---|---|
| `npm create vite@latest frontend -- --template react-ts` | Scaffolds a new React + TypeScript project powered by Vite. | Starting a new frontend from scratch. |
| `npm install <package>` | Installs a production dependency and adds it to `dependencies` in `package.json`. | Adding libraries needed at runtime (e.g. `react-router-dom`, `lucide-react`). |
| `npm install -D <package>` | Installs a development-only dependency in `devDependencies`. | Adding build-time tools (e.g. `typescript`, `@types/react`, `tailwindcss`, `vite`). |
| `npm run dev` | Starts Vite's local dev server with Hot-Module-Replacement (HMR). Default port: `5173`. | Daily development. Updates your browser instantly on file save. |
| `npm run build` | Runs `tsc -b && vite build`. Type-checks the entire project and compiles minified HTML/CSS/JS into `dist/`. | Before committing code, verifying type safety, or deploying to production. |
| `npm run preview` | Spins up a local web server serving the compiled production `dist/` directory. | Testing how the real production build performs before deploying. |
| `npm list --depth=0` | Lists all top-level packages installed in your project. | Inspecting current package versions without opening `package.json`. |

### Crucial Concepts: `package.json` vs `package-lock.json`
- **`package.json`**: Declares what your project *wants* (e.g. `"react": "^18.3.1"`). The `^` allows npm to install compatible minor updates.
- **`package-lock.json`**: Records the **exact version**, integrity hash, and nested dependencies installed on your disk. **Never delete or edit this manually**; commit it to Git so every developer and CI/CD server gets the identical byte-for-byte environment.

### What is `npx`?
- `npx` (Node Package Execute) runs a CLI tool directly without needing to install it globally.
  - Example: `npx tsc --noEmit` runs TypeScript compiler directly.

---

## 2. TypeScript (TS) Essentials & Common Gotchas

TypeScript adds static type definitions to JavaScript, catching bugs at compile-time before your code ever runs in a browser.

### Key TS Commands
| Command | What it does |
|---|---|
| `npx tsc --noEmit` | Type-checks your entire project without generating output files. Exits with code 0 if all types match. |
| `tsc -b` | Builds referenced project configs (`tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`). |

---

### The Gotchas We Solved in this Project

#### Gotcha 1: `Type 'unknown' is not assignable to type 'ReactNode'`
* **The Error**:
  ```tsx
  // If result is Record<string, unknown>, result.text has type unknown:
  {result.text && <p>{result.text}</p>} // ❌ ERROR TS2322!
  ```
* **Why it happens**:
  In JavaScript/React, `{value && <Component />}` evaluates to `value` if falsy. If `value` is typed as `unknown`, the expression's type is `unknown | ReactNode`. React only allows `ReactNode` (string, number, element, null, undefined) in JSX, not `unknown`.
* **The Solution**:
  Explicitly convert the condition to a boolean and cast or convert the display value:
  ```tsx
  // ✅ Correct
  {Boolean(result.text) && <p>{String(result.text)}</p>}
  ```

#### Gotcha 2: Working with `Record<string, unknown>` (Dynamic API JSON)
When FastAPI returns arbitrary JSON, TypeScript doesn't know what fields exist:
```typescript
type AnyRecord = Record<string, unknown>;

// ❌ Cannot do arithmetic on unknown:
const size = result.file_size / 1024; // TS error!

// ✅ Cast to number first:
const size = Number(result.file_size) / 1024;
```

#### Gotcha 3: Union Literal Types for State Machines
Instead of using loose strings (`"idle"`, `"done"`), define strict union types:
```typescript
type Phase = "idle" | "validating" | "parsing" | "chunking" | "indexing" | "done" | "error";

// If you misspell "parsing" as "parseing", TS catches it immediately!
const [phase, setPhase] = useState<Phase>("idle");
```

---

## 3. React Essentials (Hooks & Patterns in CPIS)

### The 5 React Hooks Used in CPIS

#### 1. `useState` — Reactive UI State
Stores component state and triggers a re-render when changed:
```tsx
const [tab, setTab] = useState<"phase1" | "phase2" | "phase3">("phase1");
```

#### 2. `useEffect` — Lifecycle & API Calls
Runs side effects (e.g. checking backend health when component mounts):
```tsx
useEffect(() => {
  fetch("http://localhost:8000/api/health")
    .then((r) => setBackendUp(r.ok))
    .catch(() => setBackendUp(false));
}, []); // Empty dependency array [] means run once on initial load
```

#### 3. `useRef` — Direct DOM Manipulation
Accesses DOM elements directly without triggering re-renders (used for custom file pickers):
```tsx
const inputRef = useRef<HTMLInputElement>(null);

// Open hidden system file dialog when clicking a custom button:
<button onClick={() => inputRef.current?.click()}>Upload File</button>
<input type="file" ref={inputRef} style={{ display: "none" }} />
```

#### 4. `useCallback` — Memoized Event Handlers
Prevents expensive re-creations of handler functions on every render (used for drag-and-drop):
```tsx
const onDrop = useCallback((e: React.DragEvent) => {
  e.preventDefault();
  if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
}, [handleFile]);
```

#### 5. React Router (`useNavigate`, `useParams`, `useLocation`)
Enables multi-page client-side routing without reloading the browser:
```tsx
// Navigating with state data:
const nav = useNavigate();
nav(`/results/${data.sha256}`, { state: { result: data } });

// Reading state in the destination page:
const { sha256 } = useParams();
const { state } = useLocation();
```

---

## 4. Full-Stack Data Flow: React ➔ FastAPI

```
┌─────────────────────────────────┐
│     React Component             │
│   (UploadPage.tsx)              │
└──────────────┬──────────────────┘
               │ 1. File dropped
               ▼
┌─────────────────────────────────┐
│   new FormData()                │
│   formData.append("file", file) │
└──────────────┬──────────────────┘
               │ 2. fetch("http://localhost:8000/api/upload-resume", { method: "POST", body: formData })
               ▼
┌─────────────────────────────────┐
│     FastAPI Backend             │
│   (src/api/server.py)           │
│   - Validate PDF magic bytes    │
│   - DocumentParser.extract()    │
│   - Chunker.split()             │
│   - ChromaDB.index()            │
└──────────────┬──────────────────┘
               │ 3. Returns JSON { sha256, chunk_count, char_count, text }
               ▼
┌─────────────────────────────────┐
│     React Component             │
│   (ResultsPage.tsx)             │
│   - Inspect Chunks (Phase 2)    │
│   - Trigger Agent (Phase 3)     │
└─────────────────────────────────┘
```

---

## 5. Daily Terminal Quick-Reference

```powershell
# 1. Start backend server (Python FastAPI)
.\venv\Scripts\python -m uvicorn src.api.server:app --port 8000 --reload

# 2. Start frontend server (React Vite)
cd frontend
npm run dev

# 3. Check for TypeScript errors across all files
npm run build

# 4. If npm gets corrupted or strange package errors occur:
rm -r node_modules, package-lock.json
npm install
```
