import { Link } from "react-router-dom";

const S = {
  page: { minHeight: "100vh", background: "#0B0B0B" } as React.CSSProperties,
  hero: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    minHeight: "calc(100vh - 62px)",
    borderBottom: "1px solid #1a1a1a",
  } as React.CSSProperties,
  heroLeft: {
    padding: "80px 48px",
    display: "flex",
    flexDirection: "column",
    justifyContent: "flex-end",
    borderRight: "1px solid #1a1a1a",
  } as React.CSSProperties,
  heroRight: {
    background: "#2200FF",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  } as React.CSSProperties,
  kicker: {
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: "0.15em",
    textTransform: "uppercase" as const,
    color: "#888",
    marginBottom: 32,
  },
  h1: {
    fontSize: "clamp(3.5rem, 6vw, 6.5rem)",
    fontWeight: 900,
    lineHeight: 1.0,
    letterSpacing: "-0.02em",
    marginBottom: 32,
  },
  heroBody: { fontSize: 16, color: "#888", lineHeight: 1.6, maxWidth: 420, marginBottom: 48 },
  blueTag: {
    fontSize: "clamp(3rem, 7vw, 8rem)",
    fontWeight: 900,
    color: "#fff",
    letterSpacing: "-0.02em",
  },
  howSection: { padding: "100px 48px", borderBottom: "1px solid #1a1a1a" },
  howGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 80, marginTop: 64 },
  howLeft: {},
  howRight: {},
  howStep: { borderTop: "1px solid #1a1a1a", padding: "28px 0" },
  stepNum: { fontSize: 11, fontWeight: 600, color: "#888", letterSpacing: "0.1em", marginBottom: 12 },
  stepTitle: { fontSize: 20, fontWeight: 800, marginBottom: 10, letterSpacing: "-0.01em" },
  stepDesc: { fontSize: 14, color: "#888", lineHeight: 1.6 },
  ctaSection: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    borderBottom: "1px solid #1a1a1a",
  } as React.CSSProperties,
  ctaLeft: { padding: "100px 48px", borderRight: "1px solid #1a1a1a" },
  ctaRight: { padding: "100px 48px", display: "flex", flexDirection: "column" as const, justifyContent: "flex-end" },
  footer: {
    padding: "32px 48px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    borderTop: "1px solid #1a1a1a",
  } as React.CSSProperties,
  footerText: { fontSize: 12, color: "#555" },
};

const btnPrimary: React.CSSProperties = {
  display: "inline-flex", alignItems: "center", gap: 8,
  background: "#fff", color: "#0B0B0B",
  fontSize: 12, fontWeight: 700,
  letterSpacing: "0.1em", textTransform: "uppercase",
  padding: "14px 28px", textDecoration: "none", border: "none", cursor: "pointer",
};

const btnOutline: React.CSSProperties = {
  display: "inline-flex", alignItems: "center", gap: 8,
  background: "transparent", color: "#fff",
  fontSize: 12, fontWeight: 700,
  letterSpacing: "0.1em", textTransform: "uppercase",
  padding: "13px 28px", textDecoration: "none", border: "1px solid #333",
};

export function LandingPage() {
  return (
    <div style={S.page}>
      {/* ---- HERO ---- */}
      <section style={S.hero}>
        <div style={S.heroLeft}>
          <p style={S.kicker}>Autonomous Resume Intelligence System</p>
          <h1 style={S.h1}>
            Upload.<br />
            Parse.<br />
            Match.
          </h1>
          <p style={S.heroBody}>
            Drop a PDF resume. CPIS validates, chunks, and semantically indexes it into ChromaDB, then runs a self-correcting LangGraph agent to extract structured candidate data and rank matching roles.
          </p>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            <Link to="/upload" style={btnPrimary}
              onMouseEnter={e => { e.currentTarget.style.background = "#2200FF"; e.currentTarget.style.color = "#fff"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "#fff"; e.currentTarget.style.color = "#0B0B0B"; }}>
              Upload Resume &rarr;
            </Link>
            <a href="#how" style={btnOutline}
              onMouseEnter={e => { e.currentTarget.style.borderColor = "#fff"; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = "#333"; }}>
              How It Works
            </a>
          </div>
        </div>
        <div style={S.heroRight}>
          <span style={S.blueTag}>CPIS</span>
        </div>
      </section>

      {/* ---- HOW IT WORKS ---- */}
      <section style={S.howSection} id="how">
        <p style={{ ...S.kicker }}>How we process</p>
        <div style={S.howGrid}>
          <div>
            <h2 style={{ fontSize: "clamp(2.5rem,4vw,4.5rem)", fontWeight: 900, lineHeight: 1.05, letterSpacing: "-0.02em" }}>
              Three phases.<br />One autonomous pipeline.
            </h2>
          </div>
          <div>
            <div style={S.howStep}>
              <p style={S.stepNum}>01 — Phase 1</p>
              <p style={S.stepTitle}>Deterministic Ingestion</p>
              <p style={S.stepDesc}>PDF validation via magic bytes header check. SHA-256 fingerprinting for deduplication. Text sanitization and structuring via StandardDocumentParser.</p>
            </div>
            <div style={S.howStep}>
              <p style={S.stepNum}>02 — Phase 2</p>
              <p style={S.stepTitle}>Vector Indexing</p>
              <p style={S.stepDesc}>500-character chunks with 50-character overlapping windows. Semantic embeddings persisted in local ChromaDB. Sub-50ms similarity retrieval.</p>
            </div>
            <div style={S.howStep}>
              <p style={S.stepNum}>03 — Phase 3</p>
              <p style={S.stepTitle}>Agentic Extraction & Matching</p>
              <p style={S.stepDesc}>LangGraph state machine: classify → extract → validate (with self-correction) → match. Bounded to 3 revision cycles. Returns structured ResumeSchema + ranked JobMatchResults.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ---- CTA ---- */}
      <section style={S.ctaSection}>
        <div style={S.ctaLeft}>
          <p style={S.kicker}>Ready to run</p>
          <h2 style={{ fontSize: "clamp(2.5rem,4vw,4.5rem)", fontWeight: 900, lineHeight: 1.05, letterSpacing: "-0.02em", marginTop: 24, marginBottom: 48 }}>
            Test the full pipeline<br />with your own resume.
          </h2>
          <Link to="/upload" style={btnPrimary}
            onMouseEnter={e => { e.currentTarget.style.background = "#2200FF"; e.currentTarget.style.color = "#fff"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "#fff"; e.currentTarget.style.color = "#0B0B0B"; }}>
            Start Now &rarr;
          </Link>
        </div>
        <div style={S.ctaRight}>
          <div style={{ borderTop: "1px solid #1a1a1a", paddingTop: 28, marginBottom: 28 }}>
            <p style={{ fontSize: 11, color: "#555", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 8 }}>Backend stack</p>
            <p style={{ fontSize: 16, fontWeight: 700 }}>FastAPI + LangGraph + ChromaDB</p>
          </div>
          <div style={{ borderTop: "1px solid #1a1a1a", paddingTop: 28, marginBottom: 28 }}>
            <p style={{ fontSize: 11, color: "#555", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 8 }}>Test coverage</p>
            <p style={{ fontSize: 16, fontWeight: 700 }}>28 / 28 Tests Passing</p>
          </div>
          <div style={{ borderTop: "1px solid #1a1a1a", paddingTop: 28 }}>
            <p style={{ fontSize: 11, color: "#555", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 8 }}>Self-correction limit</p>
            <p style={{ fontSize: 16, fontWeight: 700 }}>3 Revision Cycles Max</p>
          </div>
        </div>
      </section>

      {/* ---- FOOTER ---- */}
      <footer style={S.footer}>
        <span style={S.footerText}>CPIS &mdash; Career Path Intelligence System</span>
        <span style={S.footerText}>Phases 1&ndash;3 Production Ready</span>
        <a href="https://github.com/valor0506/CPIS" target="_blank" rel="noreferrer" style={{ ...S.footerText, color: "#555", textDecoration: "none" }}>GitHub &rarr;</a>
      </footer>
    </div>
  );
}
