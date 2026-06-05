# UX update v3.9 - student completion and clarity

This update focuses on the main issue observed in the pilot: many students register and complete the pre-test, but do not reach the post-test and survey.

## Main changes

- Added a clear student roadmap with six required stages: consent, pre-test, learning, AI Tutor, post-test, and survey.
- Added a next-action message so students always know what to do next.
- Relaxed post-test unlock condition from all lessons completed to at least one completed learning reflection plus one AI Tutor interaction, which matches the minimum complete-case criterion used in the pilot protocol.
- Added a visible lesson progress bar and clearer indication that students may complete more sections optionally.
- Added quick-start prompts in the AI Tutor Lab for students who do not know what to ask.
- Added a mini task before using AI in each lesson to encourage prediction and reasoning.
- Improved participant-code instructions to reduce duplicate accounts.
- Added a completion message after the survey.

## Deployment note

Do not commit `.streamlit/secrets.toml` to GitHub. Set secrets in Streamlit Cloud or use `.streamlit/secrets_example.toml` as a template.
