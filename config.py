from __future__ import annotations

from pathlib import Path
import streamlit as st

APP_TITLE = "3alimnIA | علّمنيا"
APP_ICON = "🧠"
ROOT_DIR = Path(__file__).resolve().parent
APP_STYLE_PATH = ROOT_DIR / ".streamlit" / "app.css"
LESSON_MEDIA_DIR = ROOT_DIR / "assets" / "lesson_media"

_ST_KEY_CONTAINERS = """
html body .stApp .st-key-v61_public_header,
html body .stApp .st-key-v61_hero,
html body .stApp .st-key-v6203_mobile_public_header,
html body .stApp .st-key-v6205_mobile_public_header,
html body .stApp .st-key-v618_student_auth_card,
html body .stApp .st-key-v618_student_registration_card,
html body .stApp .st-key-v618_evaluator_auth_card,
html body .stApp .st-key-v6163_teacher_login_card,
html body .stApp .st-key-v67_student_tool_dock,
html body .stApp .st-key-v68_workspace_toolbar,
html body .stApp .st-key-v681_chat_composer,
html body .stApp .st-key-v681_roadmap,
html body .stApp .st-key-blueprint_editor_workspace,
html body .stApp .st-key-v6163_project_header,
html body .stApp .st-key-v6163_course_identity_card,
html body .stApp .st-key-v6163_learning_design_card,
html body .stApp .st-key-v6163_empty_projects
"""

_DAY_MODE_CALIBRATION_CSS = f"""
/* === 3alimnIA V8.2 PRECISION DAY MODE (PEARL LIQUID GLASS) === */
{_ST_KEY_CONTAINERS} {{
  background: linear-gradient(138deg, rgba(255, 255, 255, 0.72) 0%, rgba(242, 248, 255, 0.44) 100%) !important;
  backdrop-filter: blur(30px) saturate(210%) !important;
  -webkit-backdrop-filter: blur(30px) saturate(210%) !important;
  border: 1.5px solid rgba(255, 255, 255, 0.90) !important;
  border-radius: 26px !important;
  box-shadow: 0 20px 52px rgba(15, 23, 42, 0.09), inset 0 1.5px 0 rgba(255, 255, 255, 0.96) !important;
}}
html body .stApp h1, html body .stApp h2, html body .stApp h3,
html body .stApp .v65-program-head, html body .stApp .v66-panel-heading {{
  color: #0A1428 !important;
}}
html body .stApp p, html body .stApp li, html body .stApp label,
html body .stApp .v65-program-desc, html body .stApp .v65-program-audience {{
  color: #24344F !important;
}}
html body .stApp small, html body .stApp .v65-program-meta,
html body .stApp [data-testid="stCaptionContainer"],
html body .stApp [data-testid="stMetricLabel"] {{
  color: #475569 !important;
}}
html body .stApp [data-testid="stMetricValue"] {{
  color: #1E3A8A !important;
}}
html body .stApp .qai-pill,
html body .stApp .v64-ai-chip,
html body .stApp .v65-program-status,
html body .stApp .v61-eyebrow,
html body .stApp .v61-section-kicker,
html body .stApp .v61-benefit-row span,
html body .stApp article .material-symbols-rounded {{
  background: rgba(37, 99, 235, 0.11) !important;
  color: #1E3A8A !important;
  border: 1px solid rgba(37, 99, 235, 0.22) !important;
}}
html body .stApp .st-key-v8_theme_switch_btn button {{
  min-height: 36px !important;
  padding: 0.32rem 0.95rem !important;
  font-size: 0.85rem !important;
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%) !important;
  border: 1px solid rgba(255, 255, 255, 0.35) !important;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.22) !important;
}}
html body .stApp .st-key-v8_theme_switch_btn button,
html body .stApp .st-key-v8_theme_switch_btn button p,
html body .stApp .st-key-v8_theme_switch_btn button span {{
  color: #F8FAFC !important;
}}
"""

_NIGHT_MODE_CALIBRATION_CSS = f"""
/* === 3alimnIA V8.2 PRECISION NIGHT MODE (OBSIDIAN LIQUID GLASS) === */
html, body, .stApp, [data-testid="stAppViewContainer"] {{
  background-color: #050914 !important;
  color: #F8FAFC !important;
}}
html body .stApp [data-testid="stAppViewContainer"]::before,
[data-testid="stAppViewContainer"]::before {{
  background:
    radial-gradient(ellipse 58% 48% at 10% 10%, rgba(56, 189, 248, 0.26) 0%, transparent 62%),
    radial-gradient(ellipse 56% 48% at 90% 8%, rgba(129, 140, 248, 0.28) 0%, transparent 62%),
    radial-gradient(ellipse 54% 48% at 84% 88%, rgba(16, 185, 129, 0.20) 0%, transparent 60%),
    radial-gradient(ellipse 50% 46% at 14% 88%, rgba(37, 99, 235, 0.24) 0%, transparent 58%),
    linear-gradient(160deg, #050914 0%, #0A1224 50%, #071522 100%) !important;
}}

/* Override ALL white .st-key-* containers (Header, Hero, Auth, Studio, Docks) */
{_ST_KEY_CONTAINERS},
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
html body .stApp article,
html body .stApp .v6-pillar-grid article,
html body .stApp .v65-capabilities-grid article,
html body .stApp .v6-engine-grid article,
html body .stApp .v6-institution-grid article,
html body .stApp .v6-studio-flow article,
html body .stApp .v620-course-card,
html body .stApp .v620-support-card,
html body .stApp .v6189-safe-content-renderer,
html body .stApp .v6163-overview-field,
html body .stApp .v6162-summary-row,
html body .stApp [data-testid="stExpander"],
html body .stApp [data-testid="stMetric"],
html body .stApp [data-testid="stForm"],
html body .stApp [data-testid="stChatMessage"],
html body .stApp [data-testid="stFileUploader"],
html body .stApp [data-testid="stAlert"],
html body .stApp [data-testid="stDataFrame"],
html body .stApp [data-testid="stSidebar"],
html body .stApp [data-testid="stSidebar"] > div:first-child {{
  background: linear-gradient(138deg, rgba(16, 25, 46, 0.82) 0%, rgba(9, 15, 30, 0.66) 100%) !important;
  backdrop-filter: blur(32px) saturate(200%) !important;
  -webkit-backdrop-filter: blur(32px) saturate(200%) !important;
  border: 1.5px solid rgba(148, 163, 184, 0.24) !important;
  border-radius: 26px !important;
  color: #F8FAFC !important;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.56), inset 0 1px 0 rgba(255, 255, 255, 0.16) !important;
}}

/* High-Contrast Typography on Dark Glass */
html body .stApp h1, html body .stApp h2, html body .stApp h3,
html body .stApp .v65-program-head, html body .stApp .v66-panel-heading,
html body .stApp .qai-v11-section-title {{
  color: #F8FAFC !important;
}}
html body .stApp p, html body .stApp li, html body .stApp label,
html body .stApp span, html body .stApp .v65-program-desc,
html body .stApp .v65-program-audience {{
  color: #CBD5E1 !important;
}}
html body .stApp small, html body .stApp .v65-program-meta,
html body .stApp [data-testid="stCaptionContainer"],
html body .stApp [data-testid="stMetricLabel"] {{
  color: #94A3B8 !important;
}}
html body .stApp a,
html body .stApp [data-testid="stMetricValue"] {{
  color: #7DD3FC !important;
}}

/* Dark Glass Badges & Eyebrow Pills */
html body .stApp .qai-pill,
html body .stApp .v64-ai-chip,
html body .stApp .v65-program-status,
html body .stApp .v61-eyebrow,
html body .stApp .v61-section-kicker {{
  background: rgba(56, 189, 248, 0.16) !important;
  color: #BAE6FD !important;
  border: 1px solid rgba(125, 211, 252, 0.34) !important;
}}

/* Dark Glass Buttons (INCLUDING Navbar buttons inside .st-key-v61_public_header!) */
html body .stApp .st-key-v61_public_header .stButton > button,
html body .stApp .st-key-v61_public_header [data-testid="stVerticalBlock"]:has(.v6163-nav-active-marker) .stButton > button,
html body .stApp .stButton > button,
html body .stApp .stDownloadButton > button,
html body .stApp .stFormSubmitButton > button,
html body .stApp [data-testid="stPopover"] > button {{
  background: linear-gradient(145deg, rgba(30, 41, 59, 0.88) 0%, rgba(15, 23, 42, 0.72) 100%) !important;
  border: 1.5px solid rgba(148, 163, 184, 0.30) !important;
  color: #F8FAFC !important;
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.42), inset 0 1px 0 rgba(255, 255, 255, 0.16) !important;
}}
html body .stApp .st-key-v61_public_header .stButton > button p,
html body .stApp .stButton > button p,
html body .stApp .stButton > button span {{
  color: #F8FAFC !important;
}}
html body .stApp .st-key-v61_public_header [data-testid="stVerticalBlock"]:has(.v6163-nav-active-marker) .stButton > button {{
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.32) 0%, rgba(14, 165, 233, 0.24) 100%) !important;
  border-color: rgba(96, 165, 250, 0.65) !important;
}}
html body .stApp .stButton > button[kind="primary"],
html body .stApp .stFormSubmitButton > button[kind="primary"] {{
  background: linear-gradient(135deg, #2563EB 0%, #0EA5E9 100%) !important;
  border-color: rgba(255, 255, 255, 0.42) !important;
  color: #FFFFFF !important;
}}
html body .stApp .stButton > button[kind="primary"] p {{
  color: #FFFFFF !important;
}}

/* Dark Glass Selectbox (العربية) & Inputs */
html body .stApp [data-testid="stSelectbox"] > div > div,
html body .stApp [data-testid="stTextInput"] input,
html body .stApp [data-testid="stTextArea"] textarea,
html body .stApp [data-testid="stNumberInput"] input,
html body .stApp [data-testid="stChatInput"] {{
  background: rgba(15, 23, 42, 0.88) !important;
  border: 1.5px solid rgba(148, 163, 184, 0.34) !important;
  color: #F8FAFC !important;
}}
html body .stApp [data-testid="stSelectbox"] div,
html body .stApp [data-testid="stSelectbox"] span,
html body .stApp [data-testid="stSelectbox"] svg {{
  color: #F8FAFC !important;
  fill: #F8FAFC !important;
}}

/* Dark Dropdown Menu */
div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"], [data-testid="stPopoverBody"] {{
  background: rgba(15, 23, 42, 0.96) !important;
  border: 1.5px solid rgba(148, 163, 184, 0.28) !important;
}}
ul[role="listbox"] li[role="option"], div[data-baseweb="menu"] li {{
  color: #F1F5F9 !important;
}}
ul[role="listbox"] li[role="option"]:hover, div[data-baseweb="menu"] li:hover {{
  background: rgba(56, 189, 248, 0.18) !important;
  color: #FFFFFF !important;
}}

/* Crisp Gold Day-Mode Switch Button with Dark Ink */
html body .stApp .st-key-v8_theme_switch_btn button {{
  min-height: 36px !important;
  padding: 0.32rem 0.95rem !important;
  font-size: 0.85rem !important;
  background: linear-gradient(135deg, #FEF08A 0%, #FACC15 100%) !important;
  border: 1.5px solid rgba(255, 255, 255, 0.78) !important;
  box-shadow: 0 10px 24px rgba(250, 204, 21, 0.28) !important;
}}
html body .stApp .st-key-v8_theme_switch_btn button,
html body .stApp .st-key-v8_theme_switch_btn button p,
html body .stApp .st-key-v8_theme_switch_btn button span {{
  color: #0F172A !important;
  font-weight: 800 !important;
}}
"""


def is_dark_glass_mode() -> bool:
    return bool(st.session_state.get("v8_dark_glass_mode", False))


_THEME_TOGGLE_LABELS = {
    "ar": ("☀️ الوضع النهاري", "🌙 الوضع الليلي"),
    "fr": ("☀️ Mode jour", "🌙 Mode nuit"),
    "en": ("☀️ Light mode", "🌙 Dark mode"),
}


def render_theme_toggle() -> None:
    """Render a localized (AR/FR/EN) instant Day/Night Liquid Glass pill button."""
    import i18n
    lang = i18n.current_lang(st)
    light_lbl, dark_lbl = _THEME_TOGGLE_LABELS.get(lang, _THEME_TOGGLE_LABELS["en"])
    dark = is_dark_glass_mode()
    label = light_lbl if dark else dark_lbl
    cols = st.columns([7.5, 1.5])
    with cols[1]:
        if st.button(label, key="v8_theme_switch_btn", use_container_width=True):
            st.session_state["v8_dark_glass_mode"] = not dark
            st.rerun()


def load_css() -> None:
    """Inject unified V8.2 Liquid Glass CSS with precision Day/Night calibration via st.html."""
    if APP_STYLE_PATH.exists():
        css_text = APP_STYLE_PATH.read_text(encoding="utf-8")
        calibration = _NIGHT_MODE_CALIBRATION_CSS if is_dark_glass_mode() else _DAY_MODE_CALIBRATION_CSS
        st.html(f"<style>{css_text}\n{calibration}</style>")
        return
    st.warning("Theme stylesheet was not found; the app will use Streamlit defaults.")