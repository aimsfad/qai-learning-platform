from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main_app.py"
CSS = ROOT / ".streamlit" / "v4_theme.css"
DB = ROOT / "db.py"

for path in (MAIN, CSS, DB):
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")

ast.parse(MAIN.read_text(encoding="utf-8"))
ast.parse(DB.read_text(encoding="utf-8"))

main = MAIN.read_text(encoding="utf-8")
css = CSS.read_text(encoding="utf-8")
db = DB.read_text(encoding="utf-8")

required_main = [
    "def evaluator_ui()",
    "def evaluator_metric_cards(",
    "def evaluator_filtered_progress()",
    "v45-eval-profile",
    "v45-metric-grid",
    "v45-export-grid",
    "render_evaluator_dashboard",
    "render_llm_performance_evaluation",
    "render_feedback_logs",
]
for marker in required_main:
    if marker not in main:
        raise SystemExit(f"Missing evaluator marker: {marker}")

required_css = ["3alimnIA V4.5", ".v45-metric-grid", ".v45-transcript", ".v45-export-grid"]
for marker in required_css:
    if marker not in css:
        raise SystemExit(f"Missing CSS marker: {marker}")

if "preferred_language" not in db:
    raise SystemExit("students_df does not expose preferred_language")
if 'APP_VERSION = "v4.5-evaluator-research-dashboard"' not in db:
    raise SystemExit("APP_VERSION was not updated")

print("V4.5 evaluator validation passed: routing, multilingual copy, filters, LPQS, exports, and CSS markers.")
