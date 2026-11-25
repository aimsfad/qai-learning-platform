from __future__ import annotations

from pathlib import Path
import streamlit as st

APP_TITLE = "3alimnIA | علّمنيا"
APP_ICON = "🧠"
ROOT_DIR = Path(__file__).resolve().parent
APP_STYLE_PATH = ROOT_DIR / ".streamlit" / "app.css"
LESSON_MEDIA_DIR = ROOT_DIR / "assets" / "lesson_media"


def load_css() -> None:
    """Inject the unified V7.1 Ultra Liquid Glass stylesheet reliably across all Streamlit versions."""
    if APP_STYLE_PATH.exists():
        css_text = APP_STYLE_PATH.read_text(encoding="utf-8")
        st.html(APP_STYLE_PATH)
        return
    st.warning("Theme stylesheet was not found; the app will use Streamlit defaults.")
