from pathlib import Path

root = Path(__file__).resolve().parent
css = (root / ".streamlit" / "v4_theme.css").read_text(encoding="utf-8")
required = [
    "3alimnIA V4.10",
    "--header-height: 0px",
    "padding-top: .12rem",
    'button[role="tab"][aria-selected="true"]',
    "linear-gradient(135deg, #0d3b91",
    "-webkit-text-fill-color: #ffffff",
]
missing = [item for item in required if item not in css]
if missing:
    raise SystemExit(f"Missing V4.10 CSS rules: {missing}")
print("V4.10 compact-top and active-tabs validation passed.")
