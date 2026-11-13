from __future__ import annotations

TERMINAL_BG = "#13150F"
PANEL_BG = "#1C2016"
PHOSPHOR_AMBER = "#E4B44C"
PHOSPHOR_DIM = "#8B9574"
INK = "#D5DDC4"
LINE = "#3A4030"
ALERT = "#D26A2C"

CONSOLE_CSS = f"""
@import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Share+Tech+Mono&display=swap");

:root {{
  --ts-bg: {TERMINAL_BG};
  --ts-panel: {PANEL_BG};
  --ts-amber: {PHOSPHOR_AMBER};
  --ts-dim: {PHOSPHOR_DIM};
  --ts-ink: {INK};
  --ts-line: {LINE};
  --ts-alert: {ALERT};
}}

.stApp {{
  background:
    repeating-linear-gradient(
      0deg,
      rgba(0, 0, 0, 0.11) 0px,
      rgba(0, 0, 0, 0.11) 1px,
      transparent 1px,
      transparent 4px
    ),
    var(--ts-bg);
  color: var(--ts-ink);
  font-family: "IBM Plex Mono", ui-monospace, monospace;
}}

.stApp h1, .stApp h2, .stApp h3,
[data-testid="stHeading"] h1,
[data-testid="stHeading"] h2,
[data-testid="stHeading"] h3 {{
  font-family: "Share Tech Mono", "IBM Plex Mono", monospace !important;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ts-amber) !important;
  font-weight: 400 !important;
}}

[data-testid="stHeader"] {{
  background: transparent;
}}

[data-testid="stToolbar"] {{
  visibility: hidden;
}}

[data-testid="stDeployButton"],
.stDeployButton {{
  display: none !important;
}}

[data-testid="stSidebar"] {{
  background: var(--ts-panel);
  border-right: 1px solid var(--ts-line);
}}

[data-testid="stSidebar"] * {{
  font-family: "IBM Plex Mono", monospace !important;
}}

[data-testid="stAlert"] {{
  background: var(--ts-panel) !important;
  border: 1px solid var(--ts-alert) !important;
  color: var(--ts-ink) !important;
}}

[data-testid="stMetricValue"] {{
  font-family: "Share Tech Mono", monospace !important;
  color: var(--ts-amber) !important;
  font-size: 2.4rem !important;
}}

[data-testid="stMetricLabel"] {{
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ts-dim) !important;
}}

div[data-testid="stRadio"] label {{
  font-family: "IBM Plex Mono", monospace !important;
  letter-spacing: 0.04em;
}}

.stRadio [role="radiogroup"] {{
  border: 1px solid var(--ts-line);
  padding: 0.4rem 0.6rem;
  background: var(--ts-panel);
}}

iframe {{
  border: 1px solid var(--ts-line) !important;
  filter: grayscale(0.35) sepia(0.25) hue-rotate(18deg) contrast(0.95);
}}

.ts-masthead {{
  font-family: "Share Tech Mono", "IBM Plex Mono", monospace;
  letter-spacing: 0.46em;
  color: var(--ts-amber);
  margin: 0 0 0.15rem 0;
  font-size: 0.8rem;
}}

@media (prefers-reduced-motion: reduce) {{
  .stApp {{
    background: var(--ts-bg);
  }}
}}
"""
