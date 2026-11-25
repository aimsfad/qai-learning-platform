from __future__ import annotations

from pathlib import Path
import streamlit as st

APP_TITLE = "3alimnIA | علّمنيا"
APP_ICON = "🧠"
ROOT_DIR = Path(__file__).resolve().parent
APP_STYLE_PATH = ROOT_DIR / ".streamlit" / "app.css"
LESSON_MEDIA_DIR = ROOT_DIR / "assets" / "lesson_media"

_OBSIDIAN_DARK_CSS = """
/* === 3alimnIA V8.0 OBSIDIAN DARK LIQUID GLASS THEME === */
html, body, .stApp, [data-testid="stAppViewContainer"] {
  background-color: #050914 !important;
  color: #F8FAFC !important;
}
html body .stApp [data-testid="stAppViewContainer"]::before,
[data-testid="stAppViewContainer"]::before {
  background:
    radial-gradient(ellipse 60% 50% at 10% 10%, rgba(56, 189, 248, 0.30) 0%, transparent 62%),
    radial-gradient(ellipse 58% 50% at 90% 8%, rgba(129, 140, 248, 0.32) 0%, transparent 62%),
    radial-gradient(ellipse 56% 50% at 82% 88%, rgba(16, 185, 129, 0.22) 0%, transparent 60%),
    radial-gradient(ellipse 50% 46% at 16% 86%, rgba(37, 99, 235, 0.28) 0%, transparent 58%),
    linear-gradient(160deg, #050914 0%, #0A1124 50%, #07131F 100%) !important;
}
html body .stApp [data-testid="stVerticalBlockBorderWrapper"],
html body .stApp [data-testid="stVerticalBlockBorderWrapper"]:has(*),
html body .stApp .v6-page-hero,
html body .stApp .v65-program-card,
html body .stApp .v64-stat-card,
html body .stApp .v64-ai-banner,
html body .stApp .v65-institution-banner,
html body .stApp .v61-float-card,
html body .stApp .v6-footer,
html body .stApp .qai-card,
html body .stApp [data-testid="stExpander"],
html body .stApp [data-testid="stMetric"],
html body .stApp [data-testid="stForm"],
html body .stApp [data-testid="stChatMessage"],
html body .stApp [data-testid="stSidebar"],
html body .stApp [data-testid="stSidebar"] > div:first-child {
  background: linear-gradient(138deg, rgba(19, 29, 51, 0.72) 0%, rgba(11, 18, 34, 0.52) 100%) !important;
  border-color: rgba(148, 163, 184, 0.24) !important;
  color: #F8FAFC !important;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.52), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
}
html body .stApp h1, html body .stApp h2, html body .stApp h3,
html body .stApp p, html body .stApp span, html body .stApp label,
html body .stApp .v65-program-head, html body .stApp .v65-program-desc,
html body .stApp .v65-program-audience, html body .stApp .v65-program-meta {
  color: #F1F5F9 !important;
}
html body .stApp .stButton > button,
html body .stApp .stDownloadButton > button {
  background: linear-gradient(145deg, rgba(30, 41, 59, 0.82) 0%, rgba(15, 23, 42, 0.64) 100%) !important;
  border-color: rgba(148, 163, 184, 0.28) !important;
  color: #F8FAFC !important;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.36), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
}
html body .stApp .stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #2563EB 0%, #0EA5E9 100%) !important;
  color: #FFFFFF !important;
}
html body .stApp [data-testid="stSelectbox"] > div > div,
html body .stApp [data-testid="stTextInput"] input,
html body .stApp [data-testid="stTextArea"] textarea {
  background: rgba(15, 23, 42, 0.78) !important;
  border-color: rgba(148, 163, 184, 0.30) !important;
  color: #F8FAFC !important;
}
div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
  background: rgba(15, 23, 42, 0.92) !important;
  border-color: rgba(148, 163, 184, 0.26) !important;
}
ul[role="listbox"] li[role="option"], div[data-baseweb="menu"] li {
  color: #F1F5F9 !important;
}
"""


def is_dark_glass_mode() -> bool:
    return bool(st.session_state.get("v8_dark_glass_mode", False))


def render_theme_toggle() -> None:
    """Render a compact Pearl Light / Obsidian Dark Liquid Glass theme switch."""
    cols = st.columns([6, 2])
    with cols[1]:
        st.toggle("🌙 الزجاج الداكن (Obsidian)", key="v8_dark_glass_mode")


def load_css() -> None:
    """Inject unified V8.0 Liquid Glass CSS (Pearl Light + optional Obsidian Dark) via st.html."""
    if APP_STYLE_PATH.exists():
        css_text = APP_STYLE_PATH.read_text(encoding="utf-8")
        if is_dark_glass_mode():
            css_text = css_text + "\n" + _OBSIDIAN_DARK_CSS
        st.html(f"<style>{css_text}</style>")
        return
    st.warning("Theme stylesheet was not found; the app will use Streamlit defaults.")
