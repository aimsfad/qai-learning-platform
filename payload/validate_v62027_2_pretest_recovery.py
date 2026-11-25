#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
checks = {
    "third recovery helper": "def _final_recovery_prompt(" in (ROOT / "course_pretest_engine.py").read_text(encoding="utf-8"),
    "three attempts": "attempts = 3" in (ROOT / "course_pretest_engine.py").read_text(encoding="utf-8"),
    "provider shape choices": 'row.get("choices")' in (ROOT / "course_pretest_contract.py").read_text(encoding="utf-8"),
    "provider shape answer index": 'row.get("answer_index")' in (ROOT / "course_pretest_contract.py").read_text(encoding="utf-8"),
    "teacher failure details": "Generation failure details" in (ROOT / "teacher_studio.py").read_text(encoding="utf-8"),
}
failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + ": " + name)
if failed:
    raise SystemExit("V6.20.27.2 validation failed: " + ", ".join(failed))
print(f"V6.20.27.2 checks: {len(checks)}/{len(checks)} PASS")
