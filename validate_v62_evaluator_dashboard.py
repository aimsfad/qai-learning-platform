from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main_app.py"
REQ = ROOT / "requirements.txt"
CSS = ROOT / ".streamlit" / "v6_theme.css"
CONFIG = ROOT / ".streamlit" / "config.toml"
DB = ROOT / "db.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    source = MAIN.read_text(encoding="utf-8")
    ast.parse(source)
    req = REQ.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    db_source = DB.read_text(encoding="utf-8")

    require("import plotly.express as px" in source, "Plotly Express import is missing")
    require("def render_evaluator_dashboard()" in source, "Evaluator dashboard function is missing")
    require("st.tabs([" in source, "Native evaluator tabs are missing")
    require("st.metric(" in source, "Native KPI metrics are missing")
    require("st.column_config.ProgressColumn" in source, "ProgressColumn is missing")
    require("db.research_export_tables" in source, "Research export integration is missing")
    require("theme=\"streamlit\"" in source, "Charts must inherit the Streamlit theme")
    require("plotly>=6.0,<7" in req, "Plotly requirement is missing")
    require("V6.2 — Evaluator Intelligence Dashboard" in css, "V6.2 CSS block is missing")
    require("chartCategoricalColors" in config, "Chart palette is missing from config.toml")
    require("v6.2-evaluator-intelligence-dashboard" in db_source, "App version was not updated")
    require("np.random" not in source and "load_mock_data" not in source, "Mock data must not be used")
    print("V6.2 evaluator intelligence dashboard validation passed.")


if __name__ == "__main__":
    main()
