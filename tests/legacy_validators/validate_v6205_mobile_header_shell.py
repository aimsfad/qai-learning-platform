"""Static regression checks for V6.20.5 deterministic mobile header shell."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ui = (ROOT / "ui_v6.py").read_text(encoding="utf-8")
css = (ROOT / ".streamlit" / "v6205_mobile_header_shell.css").read_text(encoding="utf-8")
config = (ROOT / "config.py").read_text(encoding="utf-8")
db = (ROOT / "db.py").read_text(encoding="utf-8")
package = (ROOT / "package_release.py").read_text(encoding="utf-8")

checks = {
    "column-free mobile header": 'key="v6205_mobile_public_header"' in ui and 'mobile_logo_col' not in ui,
    "dedicated logo class": "v6205-mobile-logo-img" in ui and "branding.official_logo_data_uri()" in ui,
    "new css loaded last": "V6205_STYLE_PATH" in config and "v6205_mobile_header_shell.css" in config,
    "absolute menu trigger": "position: absolute" in css and '[data-testid="stPopover"]' in css,
    "logo crop neutralized": "img.v6205-mobile-logo-img" in css and "object-fit: contain" in css and "border-radius: 0" in css,
    "no mobile columns": "grid-template-columns" not in css,
    "release version": 'APP_VERSION = "v6.20.5-mobile-header-shell"' in db,
    "sanitized package name": "3alimnIA_V6.20.5_Mobile_Header_Shell.zip" in package,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("V6.20.5 validation failed: " + ", ".join(failed))
print("V6.20.5 deterministic mobile header shell validation passed.")
