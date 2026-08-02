from pathlib import Path

root = Path(__file__).resolve().parent
teacher = (root / "teacher_studio.py").read_text(encoding="utf-8")
css = (root / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")

checks = {
    "premium header marker": "v6162-studio-header-marker" in teacher,
    "connected workflow nodes": "v6162-step-node" in teacher,
    "single custom progress track": "v6162-progress-track" in teacher,
    "primary current action": "v6162-current-action-marker" in teacher,
    "quick summary card": "v6162-summary-card" in teacher,
    "no duplicate header st.progress": "def _project_header" in teacher and "st.progress(pct / 100" not in teacher.split("def _project_header",1)[1].split("def _render_phase_map",1)[0],
    "premium css": "3alimnIA V6.16.2 - Premium Teacher AI Studio UI" in css,
    "responsive workflow": "overflow-x:auto" in css and "@media (max-width:700px)" in css,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("V6.16.2 validation failed: " + ", ".join(failed))
print("V6.16.2 professional teacher UI validation passed.")
