from __future__ import annotations

import ast
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    ui = (ROOT / "ui_v6.py").read_text(encoding="utf-8")
    css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
    db = (ROOT / "db.py").read_text(encoding="utf-8")

    for filename in ("app.py", "ui_v6.py", "db.py", "branding.py", "router.py", "main_app.py"):
        ast.parse((ROOT / filename).read_text(encoding="utf-8"), filename=filename)

    require('position="hidden"' in app, "Native Streamlit navigation must be hidden from the public UI")
    require("render_public_header" in app, "The production public header is not called")
    require("def render_public_header" in ui, "The public header renderer is missing")
    require("st.image(str(branding.OFFICIAL_LOGO_PATH)" in ui, "Official logo must use st.image")
    require("v601-engine-badge" in ui, "The hero-safe engine badge is missing")
    require("<div class='v6-visual-logo'>{_logo_img()}</div>" not in ui, "Hero still embeds the fragile logo data URI")
    require("v601-footer-brand" in ui, "Footer safe wordmark is missing")
    require("v601-header-marker" in css, "Header styles are missing")
    require('header[data-testid="stHeader"]' in css, "Streamlit chrome suppression is missing")
    require("min-height:372px" in css, "Compact hero height rule is missing")
    require('APP_VERSION = "v6.0.1-production-header-hero"' in db, "Instrumented version was not updated")

    logo = ROOT / "assets" / "branding" / "3alimnia_logo.png"
    require(logo.exists() and logo.stat().st_size > 10_000, "Official logo is missing")
    with Image.open(logo) as image:
        image.verify()

    # Basic CSS structural sanity.
    require(css.count("{") == css.count("}"), "CSS braces are unbalanced")
    print("V6.0.1 production header and hero validation passed.")


if __name__ == "__main__":
    main()
