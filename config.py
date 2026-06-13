from __future__ import annotations

from pathlib import Path
import streamlit as st

APP_TITLE = "QAI Learning Evaluation Platform"
APP_ICON = "QAI"
ROOT_DIR = Path(__file__).resolve().parent
STYLE_PATH = ROOT_DIR / ".streamlit" / "style.css"
LESSON_MEDIA_DIR = ROOT_DIR / "assets" / "lesson_media"


def load_css() -> None:
    """Load the external stylesheet once at app startup."""
    if STYLE_PATH.exists():
        st.markdown(f"<style>{STYLE_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    else:
        st.warning("style.css not found; the app will use Streamlit defaults.")
