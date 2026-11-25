3alimnIA V6.20.27 — AI-generated course pre-test engine

WHAT IT DOES
- Generates one objective 6-question pre-test automatically for each approved course version.
- Uses the existing AI provider router (Groq/Gemini/OpenRouter/OpenAI/Anthropic fallback chain).
- Pins the same validated package to all learners in that course version.
- Rejects self-report questions, $Untitled/Untitled/TBD placeholders, duplicate options, weak concept coverage, and invalid answer keys.
- Regenerates automatically if approved course content changes (content fingerprint).
- Gives the teacher Generate/Regenerate controls in final review and auto-prepares the package before publication.
- Existing published courses can generate lazily on first learner access.
- Keeps the old familiarity baseline only as an emergency provider-failure fallback.

APPLY
1. Extract this ZIP into the ROOT of the current V6.20.26 repository.
2. Run:
   call APPLY_V62027.cmd

The installer verifies the current V6.20.26 tracked baseline before replacing files and makes a backup outside the repository.

EXPECTED VALIDATION
V6.20.27 checks: 15/15 PASS + behavioral contract tests
V6.20.26 checks: 7/7 PASS
V6.20.25.1 checks: 12/12 PASS

GIT AFTER SUCCESS
  git status
  git diff --stat
  git add db.py published_course_runtime.py teacher_studio.py validate_current_release.py prompts/educational_content_production_master.md CHANGELOG.md course_pretest_contract.py course_pretest_engine.py validate_v62027_ai_course_pretest.py V6_20_27_AI_GENERATED_COURSE_PRETEST.md
  git commit -m "feat: generate validated AI pretests per course version"
  git pull --rebase origin main
  git push origin main
  git status

DO NOT ADD INSTALLER FILES
- APPLY_V62027.cmd
- apply_v62027_ai_pretest.py
- README_V62027.txt
- payload/
