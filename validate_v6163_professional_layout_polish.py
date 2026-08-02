"""Static validation for V6.16.3 professional frontend polish."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
teacher = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
ui = (ROOT / "ui_v6.py").read_text(encoding="utf-8")
css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")

checks = {
    "invalid stretch alignment removed": 'vertical_alignment="stretch"' not in teacher,
    "centered login card": 'v6163_teacher_login_card' in teacher and 'st.columns([1, 1.55, 1]' in teacher,
    "adaptive project grid": 'def _render_project_card' in teacher and 'if len(rows) == 1' in teacher and 'column_count = 3 if len(rows) >= 3 else 2' in teacher,
    "grouped project header": 'v6163_project_header' in teacher and 'v6163-title-row' in teacher,
    "grouped overview cards": 'v6163_course_identity_card' in teacher and 'v6163_learning_design_card' in teacher,
    "minimal public navbar": 'v6163-nav-active-marker' in ui and 'type="primary" if cta else "secondary"' in ui,
    "frameless logo": 'v6163-header-logo-marker' in ui and 'OFFICIAL_LOGO_PATH' in ui,
    "frontend css present": '3alimnIA V6.16.3 - Professional layout' in css,
    "responsive rules present": '@media (max-width:720px)' in css and 'v6163-project-facts' in css,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("V6.16.3 validation failed: " + ", ".join(failed))
print("V6.16.3 professional layout polish validation passed.")
