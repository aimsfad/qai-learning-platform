3alimnIA V6.20.27.4 - Structured AI Pre-test Output

Why this patch exists
---------------------
V6.20.27.3 fixed the empty-prompt bug. The new diagnostic proves Groq now receives ~3831 input tokens, but question_count=0 still means the completed model response is not being parsed as the required JSON package.

V6.20.27.4 requests provider-enforced structured output for course pre-tests. Groq GPT-OSS 20B/120B uses strict JSON Schema output. The existing local pedagogical quality gate remains in place after parsing.

Apply
-----
1. Extract this ZIP into the repository root.
2. Run:
   call APPLY_V62027_4.cmd

Expected:
   V6.20.27.4 checks: 11/11 PASS
   V6.20.27.3 checks: 14/14 PASS
   V6.20.27.4 applied and validated.

Git
---
   git status
   git add content_generation_engine.py course_pretest_contract.py course_pretest_engine.py validate_current_release.py validate_v62027_4_structured_pretest_output.py V6_20_27_4_STRUCTURED_PRETEST_OUTPUT.md CHANGELOG.md
   git commit -m "fix: enforce structured AI pretest output"
   git pull --rebase origin main
   git push origin main

Do not add installer files:
- APPLY_V62027_4.cmd
- apply_v62027_4_structured_output.py
- README_V62027_4.txt
- manifest.json
- payload/
