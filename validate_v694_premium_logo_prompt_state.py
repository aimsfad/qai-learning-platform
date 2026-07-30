"""Validation for V6.9.4 premium logo and prompt-state hotfix."""
from __future__ import annotations

import py_compile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    for name in ["app.py", "main_app.py", "db.py", "branding.py", "ui_v6.py", "teacher_studio.py"]:
        py_compile.compile(str(ROOT / name), doraise=True)

    branding = (ROOT / "branding.py").read_text(encoding="utf-8")
    ui = (ROOT / "ui_v6.py").read_text(encoding="utf-8")
    css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
    teacher = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
    db = (ROOT / "db.py").read_text(encoding="utf-8")

    asset = ROOT / "assets" / "branding" / "3alimnia_logo_premium.png"
    require(asset.exists(), "Premium logo asset is missing")
    with Image.open(asset) as image:
        require(image.mode == "RGBA", "Premium logo must preserve transparency")
        require(image.width >= 1200 and image.height >= 300, "Premium logo resolution is insufficient")
        require(image.getpixel((0, 0))[3] == 0, "Premium logo background is not transparent")

    require("PREMIUM_LOGO_PATH" in branding, "Premium logo constant is missing")
    require("OFFICIAL_LOGO_PATH = PREMIUM_LOGO_PATH" in branding, "Official logo is not using premium asset")
    require("HEADER_WHITE_LOGO_PATH = PREMIUM_LOGO_PATH" in branding, "Header logo is not using premium asset")
    require("v694-premium-logo-marker" in ui, "Premium public-header marker is missing")
    require("V6.9.4 — Frameless quiet-luxury logo system" in css, "Premium logo CSS is missing")
    require("border-radius:0 !important" in css and "box-shadow:none !important" in css, "Legacy framed logo styling is not overridden")

    require('teacher_workspace_section_pending = "production"' in teacher, "Prompt navigation is not queued")
    require('pop("teacher_workspace_section_pending", None)' in teacher, "Queued section is not applied before widget creation")
    require('st.session_state.teacher_workspace_section = "production"' not in teacher, "Unsafe direct widget-state mutation still exists")
    require(any(v in db for v in ('APP_VERSION = "v6.9.4-premium-logo-prompt-state"', 'APP_VERSION = "v6.10-gemini-file-analyzer-router"', 'APP_VERSION = "v6.11-educational-content-builder"')), "Application version is not V6.9.4+")

    print("V6.9.4 premium logo and prompt-state validation passed.")


if __name__ == "__main__":
    main()
