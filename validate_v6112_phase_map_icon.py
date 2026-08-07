"""Static validation for the V6.11.2 phase-map icon hotfix."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
source = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")

assert 'icon="✓"' not in source, "Unsupported check-mark glyph is still used as a Streamlit icon."
assert 'st.success(copy["ready"], icon="✅")' in source, "Valid emoji icon is missing from the completed-phase callout."
assert 'def _render_phase_map' in source, "Phase-map renderer is missing."

print("V6.11.2 phase-map icon hotfix validation passed.")
