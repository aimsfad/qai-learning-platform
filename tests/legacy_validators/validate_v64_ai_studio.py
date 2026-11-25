from __future__ import annotations

from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
UI = ROOT / "ui_v6.py"
CSS = ROOT / ".streamlit" / "v6_theme.css"
DB = ROOT / "db.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


ui_text = UI.read_text(encoding="utf-8")
css_text = CSS.read_text(encoding="utf-8")
db_text = DB.read_text(encoding="utf-8")

ast.parse(ui_text)
ast.parse(db_text)

for locale in ("ar", "fr", "en"):
    require(f'"{locale}": {{' in ui_text, f"Missing locale: {locale}")

for token in (
    '"ai_studio_badge"',
    '"ai_studio_visual_labels"',
    "def _render_ai_studio_banner",
    "def _render_stats_grid",
    "v64-ai-banner",
    "v64-stats-grid",
    'context="home"',
    'context="studio"',
):
    require(token in ui_text, f"Missing UI token: {token}")

for token in (
    ".v64-ai-banner",
    ".v64-ai-banner-visual",
    ".v64-stats-grid",
    ".v64-stat-card",
    "repeat(auto-fit, minmax",
    "@media (max-width: 760px)",
    "html[dir=\"rtl\"] .v64-ai-banner-copy",
):
    require(token in css_text, f"Missing CSS token: {token}")

require('APP_VERSION = "v6.' in db_text, "V6+ app version not set")
require("_page_hero(str(c[\"ai_studio_title\"])" not in ui_text, "Legacy AI Studio hero is still active")

print("V6.4 AI Studio and responsive statistics validation passed.")
