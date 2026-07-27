from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

required_files = [
    ROOT / "app.py",
    ROOT / "ui_v6.py",
    ROOT / "config.py",
    ROOT / ".streamlit" / "v6_theme.css",
    ROOT / "assets" / "branding" / "3alimnia_logo.png",
]
for path in required_files:
    assert path.exists(), f"Missing {path.relative_to(ROOT)}"

for path in ROOT.glob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

app = (ROOT / "app.py").read_text(encoding="utf-8")
ui = (ROOT / "ui_v6.py").read_text(encoding="utf-8")
config = (ROOT / "config.py").read_text(encoding="utf-8")
css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")

for route in ["programs", "ai_studio", "institutions", "student", "evaluator"]:
    assert f'router.route_key("public", "{route}")' in app, f"Public route not registered: {route}"

assert "ui_v6.render_home()" in app
assert "ui_v6.render_public_utility_bar()" in app
assert "V6_STYLE_PATH" in config and "v6_theme.css" in config

for lang in ["ar", "fr", "en"]:
    assert re.search(rf'"{lang}"\s*:\s*\{{', ui), f"Missing V6 copy for {lang}"

for marker in [
    ".v6-hero-copy",
    ".v6-program-card",
    ".v6-engine-grid",
    ".v6-institution-strip",
    ".v6-page-hero",
    "button[role=\"tab\"][aria-selected=\"true\"]",
]:
    assert marker in css, f"Missing CSS marker {marker}"

content = (ROOT / "content.py").read_text(encoding="utf-8")
assert "LESSONS" in content
assert "PRE_TEST" in content and "POST_TEST" in content

print("V6 global AI academy validation passed.")
