3alimnIA V6.20.27.1 - Current-Main AI Course Pre-test Compatibility Patch

Why this package exists
-----------------------
The first V6.20.27 installer correctly refused to overwrite the repository because
published_course_runtime.py on the real current main had the V6.20.26 reliability
hotfix with SHA256 e4d98f3d3631..., while the first installer expected an earlier
V6.20.26 fixture (0233aee4b240...). No tracked runtime files were changed by that
failed attempt.

This package is rebuilt against the exact current-main runtime and preserves that
V6.20.26 fix while adding the V6.20.27 AI-generated course pre-test engine.

Apply
-----
1. Extract this ZIP into the repository root.
2. Run:
   call APPLY_V62027_1_CURRENT_MAIN.cmd

Expected end:
   V6.20.27 checks: 15/15 PASS + behavioral contract tests
   V6.20.26 checks: 7/7 PASS
   V6.20.25.1 checks: 12/12 PASS
   V6.20.27.1 applied and validated.

Then commit only the runtime/project files, not installer files or payload/.
