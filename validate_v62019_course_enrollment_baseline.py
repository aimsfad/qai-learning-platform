from pathlib import Path

root = Path(__file__).resolve().parent
db = (root / 'db.py').read_text(encoding='utf-8')
runtime = (root / 'published_course_runtime.py').read_text(encoding='utf-8')
css = (root / '.streamlit' / 'app.css').read_text(encoding='utf-8')
prompt = (root / 'prompts' / 'educational_content_production_master.md').read_text(encoding='utf-8')

checks = {
    'version': 'APP_VERSION = "v6.20.19-course-enrollment-baseline-gate"' in db,
    'pretest_table': 'CREATE TABLE IF NOT EXISTS published_course_pretest_attempts' in db,
    'pretest_get': 'def get_published_course_pretest_attempt' in db,
    'pretest_save': 'def save_published_course_pretest_attempt' in db,
    'explicit_enroll': 'v62019_enroll_' in runtime and 'enroll_action' in runtime,
    'baseline_gate': 'if not _render_course_pretest' in runtime,
    'course_json_contract': '"course_pretest"' in prompt,
    'legacy_fallback': 'self_report_baseline' in runtime,
    'header_reset': '.v618-page-header::after{' in css and 'width:auto !important;' in css,
    'course_flow_css': '.v62019-course-flow' in css,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit('FAIL: ' + ', '.join(failed))
print(f'V6.20.19 checks: {len(checks)}/{len(checks)} PASS')
