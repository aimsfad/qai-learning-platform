"""Static regression checks for V6.20.4 mobile header/first viewport hotfix."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ui = (ROOT / "ui_v6.py").read_text(encoding="utf-8")
css = (ROOT / ".streamlit" / "v6204_mobile_header_first_viewport.css").read_text(encoding="utf-8")
config = (ROOT / "config.py").read_text(encoding="utf-8")
db = (ROOT / "db.py").read_text(encoding="utf-8")
package = (ROOT / "package_release.py").read_text(encoding="utf-8")

checks = {
    "mobile embedded logo marker": "v6204-mobile-logo-marker" in ui,
    "mobile logo avoids st.image in dedicated block": "branding.logo_lockup_html(compact=True, language=lang)" in ui,
    "new css loaded last": "V6204_STYLE_PATH" in config and "v6204_mobile_header_first_viewport.css" in config,
    "mobile header forced to grid": "grid-template-columns: minmax(0,1fr) 48px" in css,
    "logo crop override": ".brand-approved-logo-img" in css and "object-fit: contain" in css,
    "compact icon trigger": "width: 46px" in css and "button[aria-haspopup=\"dialog\"]" in css,
    "first viewport tightening": ".st-key-v61_hero" in css and "margin-top: .18rem" in css,
    "release version": 'APP_VERSION = "v6.20.4-mobile-header-first-viewport"' in db,
    "sanitized package name": "3alimnIA_V6.20.4_Mobile_Header_First_Viewport.zip" in package,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("V6.20.4 validation failed: " + ", ".join(failed))
print("V6.20.4 mobile header + first viewport validation passed.")
