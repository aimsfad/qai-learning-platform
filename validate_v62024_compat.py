#!/usr/bin/env python3
from pathlib import Path
import ast

root = Path(__file__).resolve().parent
checks = []

def check(name, cond):
    checks.append((name, bool(cond)))

app = (root/'app.py').read_text(encoding='utf-8')
runtime = (root/'published_course_runtime.py').read_text(encoding='utf-8')
css = (root/'.streamlit/app.css').read_text(encoding='utf-8')

check('Arabic Qiskit research-path label', '"modules": "مسار Qiskit البحثي"' in app)
check('French Qiskit research-path label', '"modules": "Parcours de recherche Qiskit"' in app)
check('English Qiskit research-path label', '"modules": "Qiskit research path"' in app)
check('lesson display helper', 'def _display_lesson_title(value: Any, index: int)' in runtime)
check('baseline semantic helper', 'def _baseline_key(value: Any) -> str:' in runtime)
check('duplicate-resistant baseline', 'concept_keys: List[str] = []' in runtime)
check('learner title mapping uses display helper', '_display_lesson_title(' in runtime and 'for idx, item in enumerate(lessons)' in runtime)
check('V6.20.23 pretest marker preserved', 'v62023-pretest-marker' in runtime)
check('V6.20.24 CSS layer', 'V6.20.24 — FINAL LEARNER POLISH (CURRENT-MAIN COMPAT)' in css)
check('desktop pretest row layout', 'flex-direction: row !important;' in css)
check('Python syntax app', bool(ast.parse(app, filename='app.py')))
check('Python syntax runtime', bool(ast.parse(runtime, filename='published_course_runtime.py')))

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(('PASS' if ok else 'FAIL') + ' - ' + name)
print(f'V6.20.24 compat checks: {len(checks)-len(failed)}/{len(checks)} PASS')
if failed:
    raise SystemExit(1)
