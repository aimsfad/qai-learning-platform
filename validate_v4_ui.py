from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
required = [
    ROOT / ".streamlit" / "v4_theme.css",
    ROOT / ".streamlit" / "config.toml",
    ROOT / "assets" / "branding" / "3alimnia_logo.png",
    ROOT / "branding.py",
    ROOT / "main_app.py",
]
missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
if missing:
    raise SystemExit(f"Missing V4 files: {missing}")

for file_name in ["main_app.py", "branding.py", "config.py", "i18n.py", "db.py"]:
    ast.parse((ROOT / file_name).read_text(encoding="utf-8"), filename=file_name)

css = (ROOT / ".streamlit" / "v4_theme.css").read_text(encoding="utf-8")
for token in ["Alexandria", "Tajawal", "Inter", "v4-landing-marker", "v4-sidebar-marker", "v4-page-hero"]:
    if token not in css:
        raise SystemExit(f"Missing V4 CSS token: {token}")

logo = ROOT / "assets" / "branding" / "3alimnia_logo.png"
if logo.stat().st_size < 100_000:
    raise SystemExit("Official logo file looks incomplete.")

main = (ROOT / "main_app.py").read_text(encoding="utf-8")
if "target.image(str(branding.OFFICIAL_LOGO_PATH)" not in main:
    raise SystemExit("Sidebar does not use the reliable Streamlit logo renderer.")
if "st.image(str(branding.OFFICIAL_LOGO_PATH)" not in main:
    raise SystemExit("Landing page does not use the reliable Streamlit logo renderer.")

print("V4 UI validation passed: assets, syntax, multilingual typography, and logo rendering.")
