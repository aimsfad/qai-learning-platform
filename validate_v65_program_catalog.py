from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
ui = (ROOT / "ui_v6.py").read_text(encoding="utf-8")
css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
db = (ROOT / "db.py").read_text(encoding="utf-8")

ast.parse(ui)
ast.parse(db)
required_ui = [
    "v65-program-card", "v65-program-status", "v65-program-audience",
    "v65-institution-banner", "institution_bullets", "capabilities_title"
]
required_css = [
    ".v65-program-card", ".v65-program-meta", ".v65-institution-banner",
    "repeat(auto-fit", "@media (max-width: 720px)"
]
for token in required_ui:
    assert token in ui, token
for token in required_css:
    assert token in css, token
assert "v6.5-program-catalog-institutional-trust" in db
assert ui.count('\"capabilities_title\"') >= 3
assert ui.count('"institution_bullets"') >= 3
print("V6.5 program catalog and institutional trust validation passed.")
