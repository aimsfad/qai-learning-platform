from pathlib import Path

ROOT = Path(__file__).resolve().parent
ui = (ROOT / "ui_v6.py").read_text(encoding="utf-8")
css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
logo = ROOT / "assets" / "branding" / "3alimnia_logo.png"
assert "v671-header-logo-marker" in ui
assert "_render_official_logo(214)" in ui
assert "v671-header-logo-marker" in css
assert "width:214px!important" in css
assert logo.exists() and logo.stat().st_size > 1000
compile(ui, str(ROOT / "ui_v6.py"), "exec")
print("V6.7.1 header logo restoration validation passed.")
