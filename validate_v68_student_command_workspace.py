from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent

for name in ["app.py", "main_app.py", "db.py"]:
    ast.parse((ROOT / name).read_text(encoding="utf-8"), filename=name)

app = (ROOT / "app.py").read_text(encoding="utf-8")
main = (ROOT / "main_app.py").read_text(encoding="utf-8")
css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
db = (ROOT / "db.py").read_text(encoding="utf-8")

checks = {
    "internal logo toolbar": "v68_workspace_toolbar" in app and "HEADER_WHITE_LOGO_PATH" in app,
    "60/40 columns": 'st.columns([3, 2], gap="large")' in main,
    "quick support container": "v68_quick_support_" in main,
    "attempt-first control": "need_attempt" in main and "len((attempt or" in main and ".strip()) < 8" in main,
    "sticky coach": "max-height:calc(100vh - 1.4rem)" in css and "position:sticky" in css,
    "desktop ratio": "calc(60% - .6rem)" in css and "calc(40% - .6rem)" in css,
    "mobile stack": "@media (max-width:820px)" in css and "flex-direction:column" in css,
    "version": ('APP_VERSION = "v6.8-student-command-workspace"' in db or 'APP_VERSION = "v6.8.1-student-ux-hotfix"' in db or 'APP_VERSION = "v6.8.2-attempt-first-gate"' in db or 'APP_VERSION = "v6.18.6-unified-premium-platform-design"', 'APP_VERSION = "v6.10-gemini-file-analyzer-router"' in db),
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("V6.8 validation failed: " + ", ".join(failed))

logo = ROOT / "assets" / "branding" / "3alimnia_header_logo_white.png"
if not logo.exists() or logo.stat().st_size < 10_000:
    raise SystemExit("Missing or invalid official white header logo")

print("V6.8 student command workspace validation passed.")
