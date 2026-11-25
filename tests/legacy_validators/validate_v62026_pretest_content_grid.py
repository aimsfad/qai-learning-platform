from pathlib import Path
import ast
root=Path(__file__).resolve().parent
py=(root/"published_course_runtime.py").read_text(encoding="utf-8")
css=(root/".streamlit/app.css").read_text(encoding="utf-8")
ast.parse(py)
checks={
"placeholder guard":"invalid_placeholders" in py,
"dollar guard":"clean.lstrip().startswith(\"$\")" in py,
"untitled blocked":"\"untitled\"" in py,
"form grid marker":"V6.20.26 — PRE-TEST CONTENT + GRID RELIABILITY" in css,
"desktop grid":"grid-template-columns: repeat(2, minmax(0, 1fr)) !important;" in css,
"max width removed":"max-width: none !important;" in css,
"mobile grid":"grid-template-columns: 1fr !important;" in css,
}
for k,v in checks.items(): print(("PASS" if v else "FAIL")+": "+k)
if not all(checks.values()): raise SystemExit(1)
print(f"V6.20.26 checks: {len(checks)}/{len(checks)} PASS")
