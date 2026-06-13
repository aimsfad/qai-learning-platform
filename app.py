from __future__ import annotations

import streamlit as st

from config import APP_ICON, APP_TITLE, load_css
from main_app import main


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()
main()
