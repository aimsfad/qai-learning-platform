#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
css = (ROOT / ".streamlit" / "app.css").read_text(encoding="utf-8")
runtime = (ROOT / "published_course_runtime.py").read_text(encoding="utf-8")
app = (ROOT / "app.py").read_text(encoding="utf-8")

checks = {
    "css release marker": "V6.20.23 — UI DENSITY + HEADER ACCENT SAFETY" in css,
    "rtl local header direction": '.v618-page-header[dir="rtl"] .v618-page-header-accent' in css,
    "ltr local header direction": '.v618-page-header[dir="ltr"] .v618-page-header-accent' in css,
    "rtl safe title gutter": '.v618-page-header[dir="rtl"] .v618-page-header-copy' in css,
    "ltr safe title gutter": '.v618-page-header[dir="ltr"] .v618-page-header-copy' in css,
    "pretest marker css": ':has(.v62023-pretest-marker)' in css,
    "pretest marker runtime": "v62023-pretest-marker" in runtime,
    "question progress runtime": "v62023-pretest-progress" in runtime and "total_questions = len(questions)" in runtime,
    "question bidi safety": "unicode-bidi: plaintext" in css,
    "code ltr safety": "unicode-bidi: isolate" in css and "ui-monospace" in css,
    "secondary tools collapsed": 'with st.expander(copy["more"], expanded=False):' in app,
}

for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'} - {name}")

ast.parse(runtime, filename="published_course_runtime.py")
ast.parse(app, filename="app.py")

failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit(f"V6.20.23 validation failed: {failed}")
print(f"V6.20.23 checks: {len(checks)}/{len(checks)} PASS")
