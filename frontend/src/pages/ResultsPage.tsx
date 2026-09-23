import { useLocation, useParams, useNavigate, Link } from "react-router-dom";
import { useState } from "react";

const API = "http://localhost:8000";
type Tab = "phase1" | "phase2" | "phase3";
type AnyRecord = Record<string, unknown>;

const TAB_LABELS: Record<Tab, string> = {
  phase1: "01 — Document Data",
  phase2: "02 — Vector Chunks",
  phase3: "03 — Agent Output",
};

export function ResultsPage() {
  const { sha256 } = useParams();
  const { state } = useLocation();
  const nav = useNavigate();
  const [tab, setTab] = useState<Tab>("phase1");
  const [agentResult, setAgentResult] = useState<AnyRecord | null>(null);
  const [agentRunning, setAgentRunning] = useState(false);
  const [agentError, setAgentError] = useState("");
  const [chunkQuery, setChunkQuery] = useState("");
  const [chunkResults, setChunkResults] = useState<AnyRecord[] | null>(null);
  const [chunkSearching, setChunkSearching] = useState(false);

  const result = (state as { result?: AnyRecord } | null)?.result ?? null;

  if (!result) {
    return (
      <div style={{ minHeight: "calc(100vh - 62px)", background: "#0B0B0B", padding: "80px 48px" }}>
        <p style={{ fontSize: 11, color: "#888", letterSpacing: "0.12em", textTransform: "uppercase" as const, marginBottom: 24 }}>No Data</p>
        <h1 style={{ fontSize: "clamp(2rem,4vw,4rem)", fontWeight: 900, letterSpacing: "-0.02em", marginBottom: 32 }}>No results to show.</h1>
        <Link to="/upload" style={{ fontSize: 12, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase" as const, color: "#fff", textDecoration: "none", padding: "14px 28px", border: "1px solid #333" }}>
          &larr; Upload a Resume
        </Link>
      </div>
    );
  }

  const runAgent = async () => {
    setAgentRunning(true);
    setAgentError("");
    try {
      const res = await fetch(`${API}/api/run-agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document_id: sha256, text: String(result.text ?? "") }),
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({ detail: res.statusText })) as AnyRecord;
        throw new Error(String(e.detail ?? res.statusText));
      }
      setAgentResult(await res.json() as AnyRecord);
    } catch (e: unknown) {
      setAgentError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setAgentRunning(false);
    }
  };

  const searchChunks = async () => {
    if (!chunkQuery.trim()) return;
    setChunkSearching(true);
    try {
      const res = await fetch(`${API}/api/vector-preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: chunkQuery, n_results: 5 }),
      });
      const data = await res.json() as { results?: AnyRecord[] };
      setChunkResults(data.results ?? []);
    } catch {
      setChunkResults([]);
    } finally {
      setChunkSearching(false);
    }
  };

  const border = "1px solid #1a1a1a";
  const mono: React.CSSProperties = { fontFamily: "JetBrains Mono, monospace", fontSize: 12, color: "#888" };
  const kicker: React.CSSProperties = { fontSize: 11, fontWeight: 600, letterSpacing: "0.12em", textTransform: "uppercase" as const, color: "#888", marginBottom: 8 };

  return (
    <div style={{ minHeight: "calc(100vh - 62px)", background: "#0B0B0B" }}>
      {/* Top meta */}
      <div style={{ padding: "32px 48px", borderBottom: border, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap" as const, gap: 24 }}>
        <div>
          <p style={kicker}>Results — Document Processed</p>
          <p style={{ ...mono, color: "#fff", fontSize: 13, fontWeight: 600, marginTop: 4 }}>
            {sha256?.slice(0, 16)}...{sha256?.slice(-8)}
          </p>
        </div>
        <div style={{ display: "flex", gap: 32 }}>
          {[
            ["Chunks", String(result.chunk_count ?? "—")],
            ["Characters", String(result.char_count ?? "—")],
            ["Collection", String(result.collection ?? "resumes")],
          ].map(([label, val]) => (
            <div key={label}>
              <p style={kicker}>{label}</p>
              <p style={{ fontSize: 20, fontWeight: 800 }}>{String(val)}</p>
            </div>
          ))}
        </div>
        <button onClick={() => nav("/upload")} style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase" as const, background: "transparent", color: "#888", border: "1px solid #222", cursor: "pointer", padding: "10px 20px" }}>
          &larr; Upload Another
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", borderBottom: border }}>
        {(Object.keys(TAB_LABELS) as Tab[]).map((t) => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: "20px 32px", borderRight: border,
            fontSize: 12, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" as const,
            background: "transparent", color: tab === t ? "#fff" : "#555",
            border: "none", borderBottom: tab === t ? "2px solid #2200FF" : "2px solid transparent",
            cursor: "pointer",
          }}>
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      <div style={{ padding: "48px 48px" }}>
        {/* Phase 1 */}
        {tab === "phase1" && (
          <div style={{ maxWidth: 900 }}>
            <h2 style={{ fontSize: "clamp(2rem,3vw,3.5rem)", fontWeight: 900, letterSpacing: "-0.02em", marginBottom: 48 }}>Document structure extracted.</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1px", background: "#1a1a1a" }}>
              {([
                ["SHA-256 Fingerprint", String(result.sha256 ?? "—")],
                ["Filename", String(result.filename ?? "—")],
                ["File Size", result.file_size != null ? `${(Number(result.file_size) / 1024).toFixed(1)} KB` : "—"],
                ["Character Count", String(result.char_count ?? "—")],
                ["Collection", String(result.collection ?? "resumes")],
                ["Chunk Count", String(result.chunk_count ?? "—")],
              ] as [string, string][]).map(([label, val]) => (
                <div key={label} style={{ background: "#0B0B0B", padding: "24px 28px" }}>
                  <p style={{ ...kicker, marginBottom: 8 }}>{label}</p>
                  <p style={{ ...mono, color: "#fff", wordBreak: "break-all" as const }}>{String(val)}</p>
                </div>
              ))}
            </div>
            {Boolean(result.text) && (
              <div style={{ marginTop: 40 }}>
                <p style={{ ...kicker, marginBottom: 16 }}>Raw Extracted Text (first 1200 chars)</p>
                <div style={{ background: "#0f0f0f", border, padding: "24px", ...mono, lineHeight: 1.8, whiteSpace: "pre-wrap" as const }}>
                  {String(result.text).slice(0, 1200)}{String(result.text).length > 1200 ? "\n\n[... truncated]" : ""}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Phase 2 */}
        {tab === "phase2" && (
          <div style={{ maxWidth: 900 }}>
            <h2 style={{ fontSize: "clamp(2rem,3vw,3.5rem)", fontWeight: 900, letterSpacing: "-0.02em", marginBottom: 16 }}>Chunks indexed in ChromaDB.</h2>
            <p style={{ fontSize: 14, color: "#888", marginBottom: 48 }}>{String(result.chunk_count ?? 0)} chunks stored — test semantic search below.</p>
            <div style={{ display: "flex", gap: 0, marginBottom: 8 }}>
              <input value={chunkQuery} onChange={(e) => setChunkQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && searchChunks()}
                placeholder="Type a query — e.g. 'Python experience'"
                style={{ flex: 1, background: "#111", border: "1px solid #222", borderRight: "none", color: "#fff", padding: "14px 20px", fontSize: 14, fontFamily: "Barlow, sans-serif", outline: "none" }}
              />
              <button onClick={searchChunks} disabled={chunkSearching} style={{ background: "#2200FF", color: "#fff", border: "none", cursor: "pointer", padding: "14px 28px", fontSize: 12, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase" as const }}>
                {chunkSearching ? "..." : "Search"}
              </button>
            </div>
            <p style={{ fontSize: 11, color: "#555", marginBottom: 40 }}>Cosine similarity lookup against the indexed document chunks.</p>
            {chunkResults?.length === 0 && <p style={{ fontSize: 13, color: "#888" }}>No results returned.</p>}
            {chunkResults?.map((r, i) => (
              <div key={i} style={{ borderTop: "1px solid #1a1a1a", paddingTop: 24, marginBottom: 24 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                  <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" as const, color: "#2200FF" }}>Chunk #{i + 1}</p>
                  <p style={{ ...mono, color: "#888" }}>Score: {typeof r.distance === "number" ? (1 - r.distance).toFixed(4) : "—"}</p>
                </div>
                <p style={{ ...mono, lineHeight: 1.8, whiteSpace: "pre-wrap" as const, color: "#ccc" }}>
                  {String(r.document ?? r.text ?? "").slice(0, 400)}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Phase 3 */}
        {tab === "phase3" && (
          <div style={{ maxWidth: 900 }}>
            <h2 style={{ fontSize: "clamp(2rem,3vw,3.5rem)", fontWeight: 900, letterSpacing: "-0.02em", marginBottom: 16 }}>Agentic extraction & matching.</h2>
            <p style={{ fontSize: 14, color: "#888", marginBottom: 40 }}>LangGraph pipeline: classify → extract → validate → match. Up to 3 self-correction cycles.</p>
            {!agentResult && !agentRunning && (
              <button onClick={runAgent} style={{ background: "#2200FF", color: "#fff", border: "none", cursor: "pointer", fontSize: 12, fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase" as const, padding: "16px 40px", marginBottom: 48 }}>
                Execute Agent Workflow &rarr;
              </button>
            )}
            {agentRunning && (
              <div style={{ marginBottom: 48 }}>
                <p style={kicker}>Agent running...</p>
                <div style={{ background: "#1a1a1a", height: 2, width: 400, marginTop: 12 }}>
                  <div style={{ background: "#2200FF", height: "100%", width: "60%" }} />
                </div>
              </div>
            )}
            {agentError && <p style={{ fontSize: 13, color: "#ef4444", fontFamily: "JetBrains Mono, monospace", marginBottom: 24 }}>Error: {agentError}</p>}
            {agentResult && (
              <>
                {Boolean(agentResult.candidate) && (
                  <div style={{ marginBottom: 48 }}>
                    <p style={{ ...kicker, marginBottom: 16 }}>Extracted Candidate Profile</p>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1px", background: "#1a1a1a", marginBottom: 24 }}>
                      {Object.entries(agentResult.candidate as AnyRecord).slice(0, 6).map(([k, v]) => (
                        <div key={k} style={{ background: "#0B0B0B", padding: "20px 24px" }}>
                          <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase" as const, color: "#555", marginBottom: 6 }}>{k.replace(/_/g, " ")}</p>
                          <p style={{ fontSize: 13, color: "#fff", fontFamily: "JetBrains Mono, monospace", wordBreak: "break-all" as const }}>
                            {Array.isArray(v) ? (v as unknown[]).join(", ") : String(v ?? "—").slice(0, 80)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {Array.isArray(agentResult.matches) && (agentResult.matches as AnyRecord[]).length > 0 && (
                  <div>
                    <p style={{ ...kicker, marginBottom: 24 }}>Matched Roles — Ranked by Relevance</p>
                    {(agentResult.matches as AnyRecord[]).map((job, i) => (
                      <div key={i} style={{ borderTop: "1px solid #1a1a1a", padding: "28px 0", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <div>
                          <p style={{ fontSize: 18, fontWeight: 800, marginBottom: 8 }}>{String(job.title ?? job.role ?? "Role")}</p>
                          <p style={{ fontSize: 13, color: "#888" }}>{String(job.company ?? "")} {job.location ? `— ${String(job.location)}` : ""}</p>
                        </div>
                        <div style={{ textAlign: "right" as const }}>
                          <p style={{ fontSize: 28, fontWeight: 900, color: "#2200FF" }}>
                            {typeof job.score === "number" ? `${Math.round(job.score * 100)}%` : "—"}
                          </p>
                          <p style={{ fontSize: 11, color: "#555", letterSpacing: "0.08em", textTransform: "uppercase" as const }}>match</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <details style={{ marginTop: 48, borderTop: "1px solid #1a1a1a", paddingTop: 24 }}>
                  <summary style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase" as const, color: "#888", cursor: "pointer", marginBottom: 16 }}>
                    View Raw Agent Response
                  </summary>
                  <pre style={{ background: "#0f0f0f", border: "1px solid #1a1a1a", padding: 24, fontSize: 11, fontFamily: "JetBrains Mono, monospace", color: "#888", overflowX: "auto" as const, lineHeight: 1.8 }}>
                    {JSON.stringify(agentResult, null, 2)}
                  </pre>
                </details>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}


