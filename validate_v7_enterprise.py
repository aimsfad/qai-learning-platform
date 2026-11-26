"""Verification suite for 3alimnIA V8.5 Audit-Clean Liquid Glass Edition."""

from __future__ import annotations

import re
from pathlib import Path
import safe_html

ROOT = Path(__file__).resolve().parent


def main() -> None:
    css = (ROOT / ".streamlit" / "app.css").read_text(encoding="utf-8")
    assert "backdrop-filter" in css and "LIQUID GLASS" in css.upper()
    assert "Material Symbols Rounded" in css
    assert "@media (max-width: 1024px)" in css
    assert "@media (max-width: 768px)" in css
    assert "@media (max-width: 480px)" in css
    assert "safe-area-inset-bottom" in css
    v85_tail = css.split("V8.5 DEDUPLICATED LIQUID GLASS LAYER", 1)[1]
    assert "prefers-color-scheme: dark" not in v85_tail, "OS dark media query must not conflict with manual toggle"

    # Single CSS injection in app.py
    app_src = (ROOT / "app.py").read_text(encoding="utf-8")
    assert len(re.findall(r"\bload_css\(\)", app_src)) == 1, "load_css() must be called exactly once in app.py"
    assert "v7_enterprise_hub" not in app_src and "v7_engines" not in app_src

    # Multilingual theme toggle in config.py
    cfg_src = (ROOT / "config.py").read_text(encoding="utf-8")
    assert "Mode nuit" in cfg_src and "Dark mode" in cfg_src and "الوضع الليلي" in cfg_src

    # Version marker updated in db.py
    db_src = (ROOT / "db.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "v8.5.0-liquid-glass-verified"' in db_src

    # XSS protection layer
    assert "&lt;script&gt;" in safe_html.esc("<script>alert(1)</script>")
    assert safe_html.safe_url("javascript:alert(1)") == "#"

    print("PASS validate_v7_enterprise.py — V8.5 single load_css, AR/FR/EN toggle, no OS dark conflict, and version verified.")


if __name__ == "__main__":
    main()
