3alimnIA V6.20.27.3 - Pre-test Prompt-Budget Reliability

Root cause fixed
----------------
Long course pre-test prompts sent to Groq did not use the Teacher Studio
# Phase / <teacher_project_brief> grammar. The V6.11.1 section-aware prompt
compactor therefore extracted no recognized sections and could return an empty
runtime prompt. Diagnostics showed e.g. ~11708 -> ~0 input tokens.

This patch adds a safe head+tail fallback for arbitrary long prompts. It keeps
the task/schema instructions at the beginning and course context at the end,
while staying inside the provider input budget.

Apply
-----
1. Extract this ZIP into the repository root.
2. Run:
   call APPLY_V62027_3.cmd

Expected validator result:
   V6.20.27.3 checks: 14/14 PASS

Then commit ONLY:
   content_generation_engine.py
   validate_current_release.py
   validate_v62027_3_prompt_budget_fix.py
   V6_20_27_3_PRETEST_PROMPT_BUDGET_FIX.md
   CHANGELOG.md

Do not commit installer files or payload/.
