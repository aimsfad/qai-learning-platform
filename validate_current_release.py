"""Run the supported regression and security suite for 3alimnIA V7.0 Enterprise."""

from __future__ import annotations

import compileall
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VALIDATORS = [
    "validate_release_security.py",
    "validate_v7_enterprise.py",
    "validate_v6190_pedagogical_quality_adaptive_coach.py",
    "validate_v6191_learner_evidence_misconception_tracing.py",
    "validate_v62020_security_hotfix.py",
    "validate_v62027_ai_course_pretest.py",
    "validate_v62027_2_pretest_recovery.py",
    "validate_v62027_3_prompt_budget_fix.py",
    "validate_v62027_4_structured_pretest_output.py",
]


def main() -> None:
    if not compileall.compile_dir(ROOT, quiet=1):
        raise SystemExit("Python compileall failed.")
    failures = []
    for name in VALIDATORS:
        result = subprocess.run(
            [sys.executable, str(ROOT / name)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            failures.append((name, (result.stdout + result.stderr).strip()))
            print(f"FAIL {name}")
        else:
            print(f"PASS {name}")
    if failures:
        for name, output in failures:
            print(f"\n--- {name} ---\n{output[-2000:]}")
        raise SystemExit(f"Current release validation failed: {len(failures)}/{len(VALIDATORS)}")
    print(f"Current release validation passed: {len(VALIDATORS)}/{len(VALIDATORS)} validators + compileall.")


if __name__ == "__main__":
    main()
