from __future__ import annotations

from pathlib import Path
import streamlit as st

APP_TITLE = "3alimnIA | علّمنيا"
APP_ICON = "🧠"
ROOT_DIR = Path(__file__).resolve().parent
APP_STYLE_PATH = ROOT_DIR / ".streamlit" / "app.css"
LESSON_MEDIA_DIR = ROOT_DIR / "assets" / "lesson_media"

_DAY_MODE_CALIBRATION_CSS = """
/* === 3alimnIA V8.1 PRECISION DAY MODE (PEARL LIQUID GLASS) === */
:root {
  --v8-ink: #0A1428;
  --v8-ink-2: #24344F;
  --v8-mute: #475569;
  --v8-accent: #1D4ED8;
  --v8-accent-2: #0284C7;
  --v8-emerald: #065F46;
}
html, body, .stApp, [data-testid="stAppViewContainer"] {
  color: var(--v8-ink) !important;
}
html body .stApp h1, html body .stApp h2, html body .stApp h3,
html body .stApp .v65-program-head, html body .stApp .v66-panel-heading {
  color: #0A1428 !important;
}
html body .stApp p, html body .stApp li, html body .stApp label,
html body .stApp .v65-program-desc, html body .stApp .v65-program-audience {
  color: #24344F !important;
}
html body .stApp small, html body .stApp .v65-program-meta,
html body .stApp [data-testid="stCaptionContainer"],
html body .stApp [data-testid="stMetricLabel"] {
  color: #475569 !important;
}
html body .stApp [data-testid="stMetricValue"] {
  color: #1E3A8A !important;
}
html body .stApp .qai-pill,
html body .stApp .v64-ai-chip,
html body .stApp .v65-program-status,
html body .stApp .v61-eyebrow,
html body .stApp .v61-section-kicker {
  background: rgba(37, 99, 235, 0.11) !important;
  color: #1E3A8A !important;
  border: 1px solid rgba(37, 99, 235, 0.22) !important;
}
html body .stApp .st-key-v8_theme_switch_btn button {
  min-height: 36px !important;
  padding: 0.32rem 0.9rem !important;
  font-size: 0.84rem !important;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.88) 0%, rgba(30, 41, 59, 0.84) 100%) !important;
  color: #F8FAFC !important;
  border: 1px solid rgba(255, 255, 255, 0.35) !important;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.28) !important;
}
"""

_NIGHT_MODE_CALIBRATION_CSS = """
/* === 3alimnIA V8.1 PRECISION NIGHT MODE (OBSIDIAN LIQUID GLASS) === */
:root {
  --v8-ink: #F8FAFC;
  --v8-ink-2: #CBD5E1;
  --v8-mute: #94A3B8;
  --v8-accent: #60A5FA;
  --v8-accent-2: #38BDF8;
  --v8-emerald: #6EE7B7;
}
html, body, .stApp, [data-testid="stAppViewContainer"] {
  background-color: #050914 !important;
  color: #F8FAFC !important;
}
html body .stApp [data-testid="stAppViewContainer"]::before,
[data-testid="stAppViewContainer"]::before {
  background:
    radial-gradient(ellipse 58% 48% at 10% 10%, rgba(56, 189, 248, 0.26) 0%, transparent 62%),
    radial-gradient(ellipse 56% 48% at 90% 8%, rgba(129, 140, 248, 0.28) 0%, transparent 62%),
    radial-gradient(ellipse 54% 48% at 84% 88%, rgba(16, 185, 129, 0.20) 0%, transparent 60%),
    radial-gradient(ellipse 50% 46% at 14% 88%, rgba(37, 99, 235, 0.24) 0%, transparent 58%),
    linear-gradient(160deg, #050914 0%, #0A1224 50%, #071522 100%) !important;
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
html body .stApp .v618-action-card,
html body .stApp .v6163-overview-card,
html body .stApp .v619-quality-gate,
html body .stApp .v619-adaptive-support-card,
html body .stApp .v6191-evidence-card,
html body .stApp .v6191-next-move,
html body .stApp .qai-card,
html body .stApp .qai-v11-section,
html body .stApp .v6-course-outline,
html body .stApp .v6-comparison-wrap,
html body .stApp .v43-guest-intro,
html body .stApp [data-testid="stExpander"],
html body .stApp [data-testid="stMetric"],
html body .stApp [data-testid="stForm"],
html body .stApp [data-testid="stChatMessage"],
html body .stApp [data-testid="stFileUploader"],
html body .stApp [data-testid="stAlert"],
html body .stApp [data-testid="stDataFrame"],
html body .stApp [data-testid="stSidebar"],
html body .stApp [data-testid="stSidebar"] > div:first-child {
  background: linear-gradient(138deg, rgba(17, 26, 46, 0.78) 0%, rgba(10, 17, 32, 0.58) 100%) !important;
  border-color: rgba(148, 163, 184, 0.24) !important;
  color: #F8FAFC !important;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.54), inset 0 1px 0 rgba(255, 255, 255, 0.16) !important;
}
html body .stApp h1, html body .stApp h2, html body .stApp h3,
html body .stApp .v65-program-head, html body .stApp .v66-panel-heading,
html body .stApp .qai-v11-section-title {
  color: #F8FAFC !important;
}
html body .stApp p, html body .stApp li, html body .stApp label,
html body .stApp span, html body .stApp .v65-program-desc,
html body .stApp .v65-program-audience {
  color: #CBD5E1 !important;
}
html body .stApp small, html body .stApp .v65-program-meta,
html body .stApp [data-testid="stCaptionContainer"],
html body .stApp [data-testid="stMetricLabel"] {
  color: #94A3B8 !important;
}
html body .stApp a,
html body .stApp [data-testid="stMetricValue"] {
  color: #7DD3FC !important;
}
html body .stApp .qai-pill,
html body .stApp .v64-ai-chip,
html body .stApp .v65-program-status,
html body .stApp .v61-eyebrow,
html body .stApp .v61-section-kicker {
  background: rgba(56, 189, 248, 0.14) !important;
  color: #BAE6FD !important;
  border: 1px solid rgba(125, 211, 252, 0.30) !important;
}
html body .stApp .stButton > button,
html body .stApp .stDownloadButton > button,
html body .stApp .stFormSubmitButton > button,
html body .stApp [data-testid="stPopover"] > button {
  background: linear-gradient(145deg, rgba(30, 41, 59, 0.84) 0%, rgba(15, 23, 42, 0.66) 100%) !important;
  border-color: rgba(148, 163, 184, 0.30) !important;
  color: #F8FAFC !important;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.40), inset 0 1px 0 rgba(255, 255, 255, 0.16) !important;
}
html body .stApp .stButton > button:hover,
html body .stApp .stDownloadButton > button:hover {
  border-color: rgba(96, 165, 250, 0.55) !important;
  color: #FFFFFF !important;
}
html body .stApp .stButton > button[kind="primary"],
html body .stApp .stFormSubmitButton > button[kind="primary"] {
  background: linear-gradient(135deg, #2563EB 0%, #0EA5E9 100%) !important;
  border-color: rgba(255, 255, 255, 0.38) !important;
  color: #FFFFFF !important;
}
html body .stApp [data-testid="stTabs"] [role="tablist"] {
  background: rgba(15, 23, 42, 0.66) !important;
  border-color: rgba(148, 163, 184, 0.24) !important;
}
html body .stApp [data-testid="stTabs"] [role="tab"] {
  color: #CBD5E1 !important;
}
html body .stApp [data-testid="stSelectbox"] > div > div,
html body .stApp [data-testid="stTextInput"] input,
html body .stApp [data-testid="stTextArea"] textarea,
html body .stApp [data-testid="stNumberInput"] input,
html body .stApp [data-testid="stChatInput"] {
  background: rgba(15, 23, 42, 0.82) !important;
  border-color: rgba(148, 163, 184, 0.32) !important;
  color: #F8FAFC !important;
}
div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"], [data-testid="stPopoverBody"] {
  background: rgba(15, 23, 42, 0.94) !important;
  border-color: rgba(148, 163, 184, 0.28) !important;
}
ul[role="listbox"] li[role="option"], div[data-baseweb="menu"] li {
  color: #F1F5F9 !important;
}
ul[role="listbox"] li[role="option"]:hover, div[data-baseweb="menu"] li:hover {
  background: rgba(56, 189, 248, 0.16) !important;
  color: #FFFFFF !important;
}
html body .stApp .st-key-v8_theme_switch_btn button {
  min-height: 36px !important;
  padding: 0.32rem 0.9rem !important;
  font-size: 0.84rem !important;
  background: linear-gradient(135deg, rgba(254, 243, 199, 0.95) 0%, rgba(253, 230, 138, 0.92) 100%) !important;
  color: #1E293B !important;
  border: 1px solid rgba(255, 255, 255, 0.72) !important;
  box-shadow: 0 8px 22px rgba(251, 191, 36, 0.26), inset 0 1px 0 rgba(255, 255, 255, 0.9) !important;
}
"""


def is_dark_glass_mode() -> bool:
    return bool(st.session_state.get("v8_dark_glass_mode", False))


def render_theme_toggle() -> None:
    """Render a sleek, instant Day/Night Liquid Glass pill button."""
    dark = is_dark_glass_mode()
    label = "☀️ الوضع النهاري" if dark else "🌙 الوضع الليلي"
    cols = st.columns([7.5, 1.5])
    with cols[1]:
        if st.button(label, key="v8_theme_switch_btn", use_container_width=True):
            st.session_state["v8_dark_glass_mode"] = not dark
            st.rerun()


def load_css() -> None:
    """Inject unified V8.1 Liquid Glass CSS with precision Day/Night color calibration via st.html."""
    if APP_STYLE_PATH.exists():
        css_text = APP_STYLE_PATH.read_text(encoding="utf-8")
        calibration = _NIGHT_MODE_CALIBRATION_CSS if is_dark_glass_mode() else _DAY_MODE_CALIBRATION_CSS
        st.html(f"<style>{css_text}\n{calibration}</style>")
        return
    st.warning("Theme stylesheet was not found; the app will use Streamlit defaults.")