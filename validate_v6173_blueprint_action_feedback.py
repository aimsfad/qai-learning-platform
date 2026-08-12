"""Validation for V6.17.3 blueprint action feedback hotfix."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
db_source = (ROOT / 'db.py').read_text(encoding='utf-8')
assert any(v in db_source for v in ('APP_VERSION = \"v6.19.1-learner-evidence-misconception-tracing\"', 'APP_VERSION = \"v6.19.0-pedagogical-quality-adaptive-coach\"', 'APP_VERSION = \"v6.18.9-lesson-identity-content-hygiene\"', 'APP_VERSION = \"v6.18.8-teacher-workspace-screenshot-polish\"', 'APP_VERSION = \"v6.18.7-frictionless-ui-contract\"', 'APP_VERSION = \"v6.18.6-unified-premium-platform-design\"', 'APP_VERSION = \"v6.18.5-premium-lesson-workspace\"', 'APP_VERSION = \"v6.18.4-simple-teacher-journey\"', 'APP_VERSION = \"v6.18.3-guided-blueprint-lesson-production\"', 'APP_VERSION = \"v6.18.2-blueprint-editor-runtime-and-ui-polish\"', 'APP_VERSION = \"v6.17.3-blueprint-action-feedback-hotfix\"'))
ui = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")

assert 'build_clicked = st.button(' in ui
assert 'with st.spinner(progress_label):' in ui
assert ('created_bundle = lesson_blueprint_engine.generate_and_persist(' in ui or 'latest = lesson_blueprint_engine.generate_and_persist(' in ui)
assert ('st.success(success_label)' in ui or 'st.success({"ar": "تم إنشاء المخطط.' in ui)
assert 'ui_stability.render_error_card(str(exc), lang=lang)' in ui
assert 'bundle = latest or db.latest_teacher_blueprint' in ui

# The old behavior reran unconditionally and moved feedback to the top of the page,
# making the action appear inactive to users positioned at the blueprint section.
start = ui.index('build_clicked = st.button(')
end = ui.index('bundle = latest or db.latest_teacher_blueprint', start)
block = ui[start:end]
assert 'st.rerun()' not in block
assert 'teacher_flash_success' not in block
assert 'teacher_flash_error' not in block

print('V6.17.3 blueprint action feedback validation passed.')
