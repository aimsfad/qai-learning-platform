# QAI Learning Evaluation Platform - v8.0 Structural Cleanup

This package is a safe structural cleanup of the previous Streamlit application.

## Main changes
- `app.py` is now a small entry point.
- The previous large app body is moved to `main_app.py` as a stability bridge.
- CSS is externalized to `.streamlit/style.css`.
- New helper modules are added: `config.py`, `state.py`, `ui_components.py`, `media_utils.py`.
- A `pages/` structure is prepared for the next full refactor.
- Old version-change Markdown clutter and `app_original.py` are not included.

## Deployment
Upload the package files to the existing GitHub branch, merge, and reboot Streamlit Cloud.

## Next step
In v8.1, page functions can be gradually moved from `main_app.py` into `pages/student/` and `pages/evaluator/` without changing the database layer.


## v8.1 update

CSS is now fully externalized and the AI Tutor Lab uses a continuous chat interface while preserving research logging.
