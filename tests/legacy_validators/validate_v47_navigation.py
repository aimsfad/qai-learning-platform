from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main_app.py"
CSS = ROOT / ".streamlit" / "v4_theme.css"
DB = ROOT / "db.py"


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise AssertionError(f"Missing {label}: {token}")


def main() -> None:
    main_text = MAIN.read_text(encoding="utf-8")
    css_text = CSS.read_text(encoding="utf-8")
    db_text = DB.read_text(encoding="utf-8")

    ast.parse(main_text, filename=str(MAIN))
    ast.parse(DB.read_text(encoding="utf-8"), filename=str(DB))

    require(main_text, "v47-shell-marker", "global shell marker")
    require(main_text, "target.expander(title, expanded=active_group)", "collapsible active navigation groups")
    require(main_text, "v47-page-hero-compact", "compact evaluator hero")
    require(main_text, "shell_ratio = [0.215, 0.785]", "evaluator rail ratio")

    require(css_text, ":has(.v47-shell-marker)", "sticky shell CSS")
    require(css_text, "position: sticky !important", "sticky positioning")
    require(css_text, "max-height: calc(100vh - .7rem)", "viewport height constraint")
    require(css_text, "overflow-y: auto !important", "independent vertical scrolling")
    require(css_text, "@media (max-width: 900px)", "mobile fallback")
    require(db_text, 'APP_VERSION = "v4.7-sticky-compact-navigation"', "V4.7 app version")

    print("V4.7 navigation validation passed.")


if __name__ == "__main__":
    main()
