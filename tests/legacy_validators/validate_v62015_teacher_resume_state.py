from pathlib import Path
import sys

root = Path(__file__).resolve().parent
teacher = (root / 'teacher_studio.py').read_text(encoding='utf-8')
db = (root / 'db.py').read_text(encoding='utf-8')
simple = (root / 'simple_teacher_journey.py').read_text(encoding='utf-8')

checks = {
    'version': 'APP_VERSION = "v6.20.15-teacher-resume-state-hotfix"' in db,
    'pending_project_open': 'teacher_pending_project_open' in teacher and 'def _queue_project_open' in teacher,
    'callback_open_button': 'on_click=_queue_project_open' in teacher,
    'pending_consumed_before_nav': 'pending_open = st.session_state.pop("teacher_pending_project_open", None)' in teacher,
    'simple_progress_uses_five_steps': 'simple_teacher_journey.build_simple_state(base_state)' in teacher and 'total_steps' in teacher,
    'legacy_review_truthful': 'Needs completion / re-approval' in teacher and 'def _final_review_display' in teacher,
    'batch_approval_touches_project': 'Any lesson-content approval changes the publishable course version' in db,
    'single_approval_touches_project': 'UPDATE teacher_projects SET updated_at=:updated_at' in db,
    'five_step_journey_preserved': 'SIMPLE_STEPS' in simple and '"review", "section": "review"' in simple,
    'final_review_workflow_preserved': 'اعتماد النسخة النهائية للمقرر' in teacher and 'نشر في فضاء المتعلم' in teacher,
}
failed = []
for name, ok in checks.items():
    print(('PASS' if ok else 'FAIL') + ': ' + name)
    if not ok:
        failed.append(name)
if failed:
    print('Validation failed:', ', '.join(failed))
    sys.exit(1)
print(f'All {len(checks)}/{len(checks)} V6.20.15 checks passed.')
