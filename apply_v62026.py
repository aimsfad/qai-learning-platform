#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import shutil, sys
from datetime import datetime

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
py = root / 'published_course_runtime.py'
css = root / '.streamlit' / 'app.css'
changelog = root / 'CHANGELOG.md'
if not py.is_file() or not css.is_file():
    raise SystemExit('ERROR: run this from the repository root (published_course_runtime.py and .streamlit/app.css are required).')

stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
backup=root.parent / f'{root.name}_backup_before_v62026_{stamp}'
backup.mkdir(parents=True, exist_ok=True)
for f in (py, css, changelog):
    if f.exists(): shutil.copy2(f, backup / f.name)

text=py.read_text(encoding='utf-8')
if 'invalid_placeholders = {' not in text:
    old='''    def add(value: Any) -> None:\n        clean = " ".join(str(value or "").strip().split())\n        if not clean:\n            return\n        key = _baseline_key(clean) or clean.casefold()\n'''
    new=r'''    blocked_keys = {
        _baseline_key(value)
        for value in (blueprint.get("course_title"), blueprint.get("title"), blueprint.get("program_name"))
        if _baseline_key(value)
    }

    def add(value: Any) -> None:
        clean = " ".join(str(value or "").strip().split())
        # Never surface generator placeholders or the course title itself as learner-facing concepts.
        placeholder_key = re.sub(r"[^\w\u0600-\u06FF]+", " ", clean.casefold()).strip()
        placeholder_key = " ".join(placeholder_key.split())
        invalid_placeholders = {
            "untitled", "title", "tbd", "to be defined", "none", "null", "n a",
            "sans titre", "بدون عنوان", "غير معنون", "غير معنونة",
        }
        if (not clean) or clean.lstrip().startswith("$") or placeholder_key in invalid_placeholders:
            return
        key = _baseline_key(clean) or clean.casefold()
        if not key or key in blocked_keys:
            return
'''
    if old not in text:
        raise SystemExit('ERROR: current-main fallback baseline anchor not found; no runtime changes written.')
    text=text.replace(old,new,1)
    py.write_text(text,encoding='utf-8')

css_marker='V6.20.26 — PRE-TEST CONTENT + GRID RELIABILITY'
ct=css.read_text(encoding='utf-8')
if css_marker not in ct:
    ct += r'''

/* ============================================================================
   V6.20.26 — PRE-TEST CONTENT + GRID RELIABILITY
   ============================================================================ */
@media (min-width: 761px) {
  [data-testid="stForm"]:has(.v62023-pretest-marker)
    [data-testid="stRadio"] [role="radiogroup"] {
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    grid-auto-flow: row !important;
    width: 100% !important;
    gap: .46rem .52rem !important;
    align-items: stretch !important;
  }
  [data-testid="stForm"]:has(.v62023-pretest-marker)
    [data-testid="stRadio"] [role="radiogroup"] > label {
    width: 100% !important;
    max-width: none !important;
    min-width: 0 !important;
    min-height: 40px !important;
    margin: 0 !important;
    padding: .42rem .62rem !important;
    display: flex !important;
    align-items: center !important;
    white-space: normal !important;
  }
}
@media (max-width: 760px) {
  [data-testid="stForm"]:has(.v62023-pretest-marker)
    [data-testid="stRadio"] [role="radiogroup"] {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: .38rem !important;
  }
}
/* ============================================================================
   END V6.20.26
   ============================================================================ */
'''
    css.write_text(ct,encoding='utf-8')

note='''# V6.20.26 — Pre-test content + grid reliability\n\n- Prevents placeholder concepts such as `$Untitled`, `Untitled`, `TBD`, and equivalent empty labels from reaching learner-facing fallback diagnostics.\n- Applies the desktop 2x2 option grid at pre-test form scope so it is no longer dependent on Streamlit border-wrapper DOM details.\n- Keeps mobile choices in a single column.\n- Does not change authentication, enrollment, scoring, persistence, or course routing.\n\n'''
(root/'V6_20_26_PRETEST_CONTENT_GRID_RELIABILITY.md').write_text(note,encoding='utf-8')
if changelog.exists():
    cc=changelog.read_text(encoding='utf-8')
    if not cc.startswith('# V6.20.26'):
        changelog.write_text(note+cc,encoding='utf-8')

validator='''from pathlib import Path\nimport ast\nroot=Path(__file__).resolve().parent\npy=(root/"published_course_runtime.py").read_text(encoding="utf-8")\ncss=(root/".streamlit/app.css").read_text(encoding="utf-8")\nast.parse(py)\nchecks={\n"placeholder guard":"invalid_placeholders" in py,\n"dollar guard":"clean.lstrip().startswith(\\"$\\")" in py,\n"untitled blocked":"\\"untitled\\"" in py,\n"form grid marker":"V6.20.26 — PRE-TEST CONTENT + GRID RELIABILITY" in css,\n"desktop grid":"grid-template-columns: repeat(2, minmax(0, 1fr)) !important;" in css,\n"max width removed":"max-width: none !important;" in css,\n"mobile grid":"grid-template-columns: 1fr !important;" in css,\n}\nfor k,v in checks.items(): print(("PASS" if v else "FAIL")+": "+k)\nif not all(checks.values()): raise SystemExit(1)\nprint(f"V6.20.26 checks: {len(checks)}/{len(checks)} PASS")\n'''
(root/'validate_v62026_pretest_content_grid.py').write_text(validator,encoding='utf-8')
print('Applied V6.20.26 pre-test content/grid reliability patch.')
print(f'Backup: {backup}')
