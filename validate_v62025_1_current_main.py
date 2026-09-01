#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import ast

root = Path(__file__).resolve().parent
runtime = (root / 'published_course_runtime.py').read_text(encoding='utf-8')
css = (root / '.streamlit' / 'app.css').read_text(encoding='utf-8')
checks = {
    'runtime parses': True,
    'card marker': "v62025-pretest-card-marker" in runtime,
    'bordered container': 'with st.container(border=True):' in runtime,
    'pretest loop intact': 'for idx, item in enumerate(questions, start=1):' in runtime,
    'submit intact': 'st.form_submit_button(copy["submit_course_pretest"]' in runtime,
    'concept baseline': 'for name in _concept_names(blueprint).values()' in runtime,
    'outcome fallback': 'for item in blueprint.get("outcomes") or []:' in runtime,
    'lesson fallback': '_display_lesson_title(lesson.get("title"), index)' in runtime,
    'css release marker': 'V6.20.25.1 — CURRENT-MAIN PRE-TEST CARD LAYOUT STABILITY' in css,
    'desktop 2x2 grid': 'grid-template-columns: repeat(2, minmax(0, 1fr)) !important;' in css,
    'mobile 1col grid': 'grid-template-columns: 1fr !important;' in css,
    'no scoring rewrite': 'db.save_published_course_pretest_attempt(' in runtime,
}
ast.parse(runtime, filename='published_course_runtime.py')
passed = sum(bool(v) for v in checks.values())
for name, ok in checks.items():
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
print(f'V6.20.25.1 checks: {passed}/{len(checks)} PASS')
if passed != len(checks):
    raise SystemExit(1)
