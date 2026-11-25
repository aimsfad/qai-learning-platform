3alimnIA V6.20.27.2 — AI pre-test recovery and diagnostics

This patch is for a clean V6.20.27.1 tracked baseline.
It adds a third schema-first recovery pass, provider-output normalization, and visible Teacher Studio diagnostics when the quality gate rejects a generated pre-test.

Apply:
  call APPLY_V62027_2.cmd

Then review:
  git status
  git diff -- course_pretest_contract.py course_pretest_engine.py teacher_studio.py validate_current_release.py

Commit tracked files only. Do not add this installer, manifest.json, or payload/.
