from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
files = {
    'teacher': ROOT / 'teacher_studio.py',
    'db': ROOT / 'db.py',
    'simple': ROOT / 'simple_teacher_journey.py',
    'guided': ROOT / 'guided_teacher_workflow.py',
}
texts = {k: p.read_text(encoding='utf-8') for k, p in files.items()}
for p in files.values():
    ast.parse(p.read_text(encoding='utf-8'), filename=str(p))

checks = {
    'version': 'APP_VERSION = "v6.20.14-final-review-publish-workflow"' in texts['db'],
    'five_step_review_map': 'step_states = [' in texts['teacher'] and 'labels["step5"]' in texts['teacher'],
    'lesson_source_review': 'course_lessons' in texts['teacher'] and 'course_sources' in texts['teacher'],
    'learner_preview': 'preview_title' in texts['teacher'] and 'render_project_student_preview' in texts['teacher'],
    'teacher_final_approval': 'اعتماد النسخة النهائية للمقرر' in texts['teacher'],
    'publish_ui_requires_approval': 'not final_review_fresh' in texts['teacher'],
    'db_requires_runtime_ready_on_review': 'if clean_status in {"review", "published"} and runtime_required' in texts['db'],
    'db_requires_final_approval': 'Approve the final course version before publication.' in texts['db'],
    'stale_review_detection': 'The course changed after final review.' in texts['db'] and 'reviewed_at < updated_at' in texts['db'],
    'no_old_send_for_review_ar': '"review_action": "إرسال للمراجعة"' not in texts['teacher'],
    'simple_review_copy': 'المراجعة والاعتماد والنشر' in texts['simple'],
    'review_status_semantics': '"review": "معتمد للنشر"' in texts['simple'] and '"review": "معتمد للنشر"' in texts['guided'],
}
failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}: {name}")
if failed:
    raise SystemExit('Validation failed: ' + ', '.join(failed))
print(f"PASS: {len(checks)}/{len(checks)} V6.20.14 checks")
