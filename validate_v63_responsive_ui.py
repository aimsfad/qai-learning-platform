from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")

required = [
    "3alimnIA V6.3",
    '@media (max-width: 720px)',
    'flex-direction: column !important',
    '[data-testid="stHorizontalBlock"]',
    '[data-testid="stColumn"]',
    'font-family: "Tajawal"',
    'font-family: "Alexandria"',
    '[data-testid="stTabs"] [data-baseweb="tab-list"]',
    'overflow-x: auto !important',
]

missing = [item for item in required if item not in CSS]
if missing:
    raise SystemExit(f"Missing V6.3 responsive rules: {missing}")

print("V6.3 responsive typography validation passed.")
