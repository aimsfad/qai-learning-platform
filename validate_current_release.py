"""Run the supported regression suite for the current 3alimnIA release."""

from __future__ import annotations

import compileall
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VALIDATORS = [
    "validate_v6165_ui_stability_design_system.py",
    "validate_v616_lesson_block_generation.py",
    "validate_v617_hybrid_background_production.py",
    "validate_v6171_unified_guided_production_journey.py",
    "validate_v6172_simplified_guided_research_flow.py",
    "validate_v6173_blueprint_action_feedback.py",
    "validate_v618_global_design_system.py",
    "validate_v6181_blueprint_api_contract.py",
    "validate_v6182_blueprint_editor_runtime_ui.py",
    "validate_v6183_guided_blueprint_lesson_flow.py",
    "validate_v6184_simple_teacher_journey.py",
    "validate_v6185_premium_lesson_workspace.py",
    "validate_v6186_unified_premium_platform_design.py",
    "validate_v6187_frictionless_ui_contract.py",
    "validate_v6188_teacher_workspace_screenshot_polish.py",
    "validate_v6189_lesson_identity_content_hygiene.py",
    "validate_v6190_pedagogical_quality_adaptive_coach.py",
    "validate_v6191_learner_evidence_misconception_tracing.py",
    "validate_v620_published_course_runtime.py",
    "validate_v6201_responsive_visual_polish.py",
    "validate_v6202_visual_qa_stabilization.py",
    "validate_v6203_mobile_public_shell.py",
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
            print(f"\n--- {name} ---\n{output[-3000:]}")
        raise SystemExit(f"Current release validation failed: {len(failures)}/{len(VALIDATORS)}")
    print(f"Current release validation passed: {len(VALIDATORS)}/{len(VALIDATORS)} validators + compileall.")


if __name__ == "__main__":
    main()
