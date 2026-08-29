from __future__ import annotations

from pathlib import Path
import streamlit as st

APP_TITLE = "3alimnIA | علّمنيا"
APP_ICON = "🧠"
ROOT_DIR = Path(__file__).resolve().parent
STYLE_PATH = ROOT_DIR / ".streamlit" / "style.css"
V4_STYLE_PATH = ROOT_DIR / ".streamlit" / "v4_theme.css"
V6_STYLE_PATH = ROOT_DIR / ".streamlit" / "v6_theme.css"
V6201_STYLE_PATH = ROOT_DIR / ".streamlit" / "v6201_responsive_visual_system.css"
V6202_STYLE_PATH = ROOT_DIR / ".streamlit" / "v6202_visual_qa_stabilization.css"
V6203_STYLE_PATH = ROOT_DIR / ".streamlit" / "v6203_mobile_public_shell.css"
LESSON_MEDIA_DIR = ROOT_DIR / "assets" / "lesson_media"


def load_css() -> None:
    """Load the external stylesheet once at app startup."""
    loaded = False
    for path in (STYLE_PATH, V4_STYLE_PATH, V6_STYLE_PATH, V6201_STYLE_PATH, V6202_STYLE_PATH, V6203_STYLE_PATH):
        if path.exists():
            st.markdown(f"<style>{path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
            loaded = True
    if not loaded:
        st.warning("Theme styles were not found; the app will use Streamlit defaults.")
