from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
UI = (ROOT / "ui_v6.py").read_text(encoding="utf-8")
CSS = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
BRANDING = (ROOT / "branding.py").read_text(encoding="utf-8")
DB = (ROOT / "db.py").read_text(encoding="utf-8")
ASSET = ROOT / "assets" / "branding" / "3alimnia_header_logo_white.png"

assert ASSET.exists(), "Missing white header logo asset"
with Image.open(ASSET) as im:
    assert im.width >= 900 and im.height >= 200, "Header logo asset is too small"
    assert im.mode in {"RGBA", "RGB"}, "Unexpected image mode"
assert "HEADER_WHITE_LOGO_PATH" in BRANDING
assert "v672-header-logo-marker" in UI
assert "3alimnia_header_logo_white.png" in BRANDING
assert "background:#fff!important" in CSS
assert "mix-blend-mode:normal!important" in CSS
assert "v6.7.2-white-header-logo" in DB
print("V6.7.2 white header logo validation passed.")
