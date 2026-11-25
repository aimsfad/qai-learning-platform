"""Validation for V6.20.3 mobile public shell and first-viewport stabilization."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    ui_path = ROOT / "ui_v6.py"
    config_path = ROOT / "config.py"
    db_path = ROOT / "db.py"
    css_path = ROOT / ".streamlit" / "v6203_mobile_public_shell.css"

    ui = ui_path.read_text(encoding="utf-8")
    config = config_path.read_text(encoding="utf-8")
    db = db_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")

    ast.parse(ui, filename=str(ui_path))
    ast.parse(config, filename=str(config_path))
    ast.parse(db, filename=str(db_path))

    require(css_path.exists() and css_path.stat().st_size > 7000, "V6.20.3 mobile stylesheet missing or unexpectedly small")
    require(('key="v6203_mobile_public_header"' in ui) or ('key="v6205_mobile_public_header"' in ui), "dedicated mobile public header missing")
    require("st.popover(" in ui and 'icon=":material/menu:"' in ui, "mobile navigation is not a native compact menu")
    require(('key="v6203_mobile_language"' in ui) or ('key="v6205_mobile_language"' in ui), "mobile language selector missing")
    require(('key="v6203_mobile_start"' in ui) or ('key="v6205_mobile_start"' in ui), "mobile primary CTA missing")
    require("V6203_STYLE_PATH" in config and "v6203_mobile_public_shell.css" in config, "V6.20.3 style not registered")
    require("V6202_STYLE_PATH, V6203_STYLE_PATH" in config, "V6.20.3 must load after V6.20.2")
    require(any(v in db for v in ('APP_VERSION = "v6.20.3-mobile-public-shell"', 'APP_VERSION = "v6.20.4-mobile-header-first-viewport"', 'APP_VERSION = "v6.20.5-mobile-header-shell"')), "V6.20.3-compatible app version missing")

    for token in (
        ".st-key-v61_public_header",
        ".st-key-v6203_mobile_public_header",
        "@media (max-width: 700px)",
        "[data-testid=\"stMainBlockContainer\"]",
        ":has(.v61-hero-copy):has(.v67-home-brand-marker)",
        "grid-template-columns: 1fr 1fr",
        "overflow-x: clip",
    ):
        require(token in css, f"Expected V6.20.3 responsive contract missing: {token}")

    print("V6.20.3 mobile public shell validation passed.")


if __name__ == "__main__":
    main()
