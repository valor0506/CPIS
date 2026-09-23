import { Link, useLocation } from "react-router-dom";

export function Navbar() {
  const loc = useLocation();
  return (
    <nav style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "20px 48px",
      borderBottom: "1px solid #1a1a1a",
      position: "sticky",
      top: 0,
      background: "#0B0B0B",
      zIndex: 100,
    }}>
      <Link to="/" style={{ fontWeight: 800, fontSize: 16, letterSpacing: "0.05em", color: "#fff", textDecoration: "none" }}>
        CPIS
      </Link>
      <div style={{ display: "flex", gap: 36, alignItems: "center" }}>
        <Link to="/#how" style={navStyle}>Approach</Link>
        <Link to="/upload" style={{ ...navStyle, color: loc.pathname === "/upload" ? "#fff" : "#888" }}>Upload</Link>
        <Link to="/#how" style={navStyle}>How It Works</Link>
        <a href="https://github.com/valor0506/CPIS" target="_blank" rel="noreferrer" style={navStyle}>GitHub</a>
      </div>
      <Link to="/upload" style={{
        fontWeight: 700,
        fontSize: 12,
        letterSpacing: "0.12em",
        textTransform: "uppercase",
        color: "#fff",
        textDecoration: "none",
        padding: "10px 20px",
        border: "1px solid #333",
        transition: "border-color 0.15s",
      }}
        onMouseEnter={e => (e.currentTarget.style.borderColor = "#fff")}
        onMouseLeave={e => (e.currentTarget.style.borderColor = "#333")}
      >
        Start Analyzing
      </Link>
    </nav>
  );
}

const navStyle: React.CSSProperties = {
  fontSize: 14,
  fontWeight: 500,
  color: "#888",
  textDecoration: "none",
  transition: "color 0.15s",
};
