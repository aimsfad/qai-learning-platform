# QAI Platform v3.6 - Cloud and Paper Analysis Preparation

This release prepares the platform for the next deployment phase.

## Database additions

- `question_responses`: stores item-level pre-test and post-test responses.
- `consent_records`: stores the consent notice confirmation.
- `events_log`: records sign-in, sign-out, test submissions, lesson completions, and survey submissions.

## Evaluator additions

- New `Paper-ready Analysis` page with:
  - pre/post descriptive indicators,
  - mean learning gain,
  - paired effect size estimate,
  - concept-level gain,
  - LLM usage evidence,
  - usability questionnaire means,
  - Excel export for paper reporting.
- New `Event Logs` page.
- Results export now includes additional datasets for paper analysis.

## Cloud preparation

- Keep SQLite for local testing.
- Use `DATABASE_URL` for PostgreSQL in Streamlit Cloud.
- Do not commit `.streamlit/secrets.toml` or local database files.
