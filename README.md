# V12.7 Control / Experimental Group

This version adds an optional research-design switch for controlled comparisons. By default, `ENABLE_CONTROL_GROUP = "false"`, so the platform keeps the normal single-arm AI-supported workflow. When enabled in Streamlit secrets, new participants are balanced between `control` and `experimental` groups. Control participants use lessons, visual simulators, reflections, pre/post tests, and surveys without AI Coach or Concept Builder. Experimental participants keep AI Coach and Concept Builder. Exports preserve `study_group` for group-level analysis.

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

### v9.2 research instrumentation note
The active learning media are the sequential concept frames in `assets/lesson_media/sequence/` and their matching concept-sequence videos. Legacy duplicate lesson images are intentionally not included in this release.

The platform now logs `lesson_entry` and `ai_request_timing` events. These can be used to estimate whether a participant requested GenAI support immediately or after spending time on the lesson concept.


## V12.1 research cleanup

This package keeps only README.md and CHANGELOG.md in the repository root, removes unused legacy media/cache files, activates the six interactive simulators, adds evaluator analytics for AI task mode and time-before-AI, and adds optional Anthropic/Claude support via Streamlit secrets.
