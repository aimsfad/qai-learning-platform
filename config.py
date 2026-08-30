from __future__ import annotations

from pathlib import Path
import streamlit as st

APP_TITLE = "3alimnIA | علّمنيا"
APP_ICON = "🧠"
ROOT_DIR = Path(__file__).resolve().parent
APP_STYLE_PATH = ROOT_DIR / ".streamlit" / "app.css"
LESSON_MEDIA_DIR = ROOT_DIR / "assets" / "lesson_media"


def load_css() -> None:
    """Load the single production stylesheet at app startup."""
    if APP_STYLE_PATH.exists():
        st.markdown(
            f"<style>{APP_STYLE_PATH.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )
        return
    st.warning("Theme stylesheet was not found; the app will use Streamlit defaults.")
