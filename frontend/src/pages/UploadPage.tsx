import { useRef, useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const API = "http://localhost:8000";

type Phase = "idle" | "validating" | "parsing" | "chunking" | "indexing" | "done" | "error";

const PHASE_LABELS: Record<Phase, string> = {
  idle: "Waiting for file",
  validating: "Validating PDF headers...",
  parsing: "Parsing document structure...",
  chunking: "Chunking text (500c / 50c overlap)...",
  indexing: "Indexing into ChromaDB...",
  done: "Pipeline complete",
  error: "Error",
};

const PHASE_ORDER: Phase[] = ["validating", "parsing", "chunking", "indexing", "done"];

function phaseProgress(p: Phase): number {
  const idx = PHASE_ORDER.indexOf(p);
  if (idx < 0) return 0;
  return Math.round(((idx + 1) / PHASE_ORDER.length) * 100);
}

export function UploadPage() {
  const nav = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState("");
  const [backendUp, setBackendUp] = useState<boolean | null>(null);

  useEffect(() => {
    fetch(`${API}/api/health`)
      .then((r) => setBackendUp(r.ok))
      .catch(() => setBackendUp(false));
  }, []);

  const handleFile = useCallback((f: File) => {
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files accepted.");
      return;
    }
    setError("");
    setFile(f);
    setPhase("idle");
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
    },
    [handleFile]
  );

  const runPipeline = async () => {
    if (!file) return;
    setError("");

    const simulate = (p: Phase, ms: number) =>
      new Promise<void>((res) => { setPhase(p); setTimeout(res, ms); });

    try {
      await simulate("validating", 400);
      await simulate("parsing", 600);
      await simulate("chunking", 500);
      setPhase("indexing");

      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${API}/api/upload-resume`, { method: "POST", body: fd });

      if (!res.ok) {
        const e = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(String((e as { detail?: unknown }).detail ?? res.statusText));
      }

      const data = await res.json() as Record<string, unknown>;
      setPhase("done");
      setTimeout(() => {
        nav(`/results/${String(data.sha256 ?? "unknown")}`, { state: { result: data } });
      }, 600);
    } catch (e: unknown) {
      setPhase("error");
      setError(e instanceof Error ? e.message : "Unknown error");
    }
  };

  const progress = phaseProgress(phase);

  return (
    <div style={{ minHeight: "calc(100vh - 62px)", background: "#0B0B0B", padding: "80px 48px" }}>
      {/* Status */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 60 }}>
        <span style={{
          width: 8, height: 8, borderRadius: "50%",
          background: backendUp === true ? "#22c55e" : backendUp === false ? "#ef4444" : "#555",
          display: "inline-block",
        }} />
        <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.12em", textTransform: "uppercase" as const, color: "#888" }}>
          {backendUp === true
            ? "FastAPI Live — localhost:8000"
            : backendUp === false
            ? "Backend Offline — run: uvicorn src.api.server:app --port 8000"
            : "Checking backend..."}
        </span>
      </div>

      <p style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.15em", textTransform: "uppercase" as const, color: "#888", marginBottom: 20 }}>
        Phase 1 — Document Ingestion
      </p>
      <h1 style={{ fontSize: "clamp(3rem,5vw,5.5rem)", fontWeight: 900, lineHeight: 1.0, letterSpacing: "-0.02em", marginBottom: 64 }}>
        Upload your resume.
      </h1>

      {/* Drop zone */}
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        style={{
          border: `1px solid ${dragging ? "#2200FF" : file ? "#2200FF" : "#222"}`,
          background: dragging ? "rgba(34,0,255,0.05)" : "transparent",
          padding: "80px 48px",
          textAlign: "center" as const,
          cursor: "pointer",
          maxWidth: 700,
          marginBottom: 40,
          transition: "border-color 0.15s, background 0.15s",
        }}
      >
        <input ref={inputRef} type="file" accept=".pdf" hidden onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
        {file ? (
          <>
            <p style={{ fontSize: 28, fontWeight: 800, marginBottom: 8 }}>{file.name}</p>
            <p style={{ fontSize: 13, color: "#888" }}>{(file.size / 1024).toFixed(1)} KB</p>
          </>
        ) : (
          <>
            <p style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Drag PDF here or click to browse</p>
            <p style={{ fontSize: 13, color: "#555" }}>Only .pdf files accepted</p>
          </>
        )}
      </div>

      {/* Progress */}
      {phase !== "idle" && (
        <div style={{ maxWidth: 700, marginBottom: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
            <span style={{ fontSize: 12, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase" as const, color: phase === "error" ? "#ef4444" : "#888" }}>
              {PHASE_LABELS[phase]}
            </span>
            <span style={{ fontSize: 12, color: "#555", fontFamily: "JetBrains Mono, monospace" }}>{progress}%</span>
          </div>
          <div style={{ background: "#1a1a1a", height: 2, width: "100%" }}>
            <div style={{
              background: phase === "error" ? "#ef4444" : phase === "done" ? "#22c55e" : "#2200FF",
              height: "100%", width: `${progress}%`, transition: "width 0.4s ease",
            }} />
          </div>
        </div>
      )}

      {error && <p style={{ maxWidth: 700, fontSize: 13, color: "#ef4444", marginBottom: 24, fontFamily: "JetBrains Mono, monospace" }}>Error: {error}</p>}

      {file && phase === "idle" && (
        <button onClick={runPipeline} style={{
          background: "#2200FF", color: "#fff", border: "none", cursor: "pointer",
          fontSize: 12, fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase" as const,
          padding: "16px 40px",
        }}>
          Run Pipeline &rarr;
        </button>
      )}

      {!file && (
        <div style={{ maxWidth: 700, marginTop: 60, borderTop: "1px solid #1a1a1a", paddingTop: 40 }}>
          <p style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.12em", textTransform: "uppercase" as const, color: "#888", marginBottom: 24 }}>
            What happens when you hit run
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32 }}>
            {[
              ["01 Validate", "Magic bytes check + SHA-256 fingerprint for dedup"],
              ["02 Parse", "Extract raw text via StandardDocumentParser"],
              ["03 Chunk", "Split into 500c segments with 50c overlap windows"],
              ["04 Index", "Embed and persist chunks into local ChromaDB collection"],
            ].map(([title, desc]) => (
              <div key={title} style={{ borderTop: "1px solid #1a1a1a", paddingTop: 20 }}>
                <p style={{ fontSize: 12, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" as const, marginBottom: 8 }}>{title}</p>
                <p style={{ fontSize: 13, color: "#888", lineHeight: 1.6 }}>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
