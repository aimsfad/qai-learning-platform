from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent

for name in ("app.py", "main_app.py", "i18n.py", "db.py"):
    py_compile.compile(str(ROOT / name), doraise=True)

main = (ROOT / "main_app.py").read_text(encoding="utf-8")
app = (ROOT / "app.py").read_text(encoding="utf-8")
i18n = (ROOT / "i18n.py").read_text(encoding="utf-8")
css = (ROOT / ".streamlit" / "v4_theme.css").read_text(encoding="utf-8")

assert "with st.sidebar:" in main
assert "render_sidebar(st.sidebar)" in main
assert "left_col, right_col = st.columns(shell_ratio" not in main
assert "v48-native-sidebar-marker" in main
assert 'initial_sidebar_state="expanded"' in app
assert "rail_side" in i18n and "main_offset" in i18n
assert "100dvh" in css
assert 'section[data-testid="stSidebar"]:has(.v48-native-sidebar-marker)' in css
assert 'overflow-y: auto !important' in css
assert '--v48-rail-width' in css
assert '@media (max-width: 900px)' in css

print("V4.8 native docked navigation validation passed.")
