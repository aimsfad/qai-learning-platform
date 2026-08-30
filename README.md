# 3alimnIA — V6.20.8 Visual Restoration

3alimnIA is a multilingual Streamlit learning platform for teacher-authored courses, learner-first attempts, structured learning evidence, adaptive support, AI coaching, evaluator analytics, and research export.

V6.20.8 restores the complete pre-V6.20.7 visual system after screenshot QA detected a major visual regression in the unified redesign. The runtime and pedagogical code remain current, while the full Quantum/Qiskit educational media library is preserved.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Windows users can also use `INSTALL_AND_RUN_WINDOWS.bat` or `INSTALL_AND_RUN_WINDOWS.ps1`.

Copy `.streamlit/secrets_example.toml` to `.streamlit/secrets.toml` for local credentials and provider keys. Never commit `secrets.toml`.

## Core structure

- `app.py` — Streamlit entry point and application routing.
- `main_app.py` — learner and evaluator flows.
- `teacher_studio.py` — teacher course-production workspace.
- `db.py` — persistence and data-access layer.
- `ui_v6.py` — public product shell and current mobile header.
- `lesson_*`, `pedagogical_*`, `learner_model_engine.py`, `adaptive_support_engine.py` — pedagogical runtime.
- `published_course_runtime.py` — runtime for teacher-published courses.
- `.streamlit/app.css` — single production stylesheet, preserving the complete V6.20.5 visual cascade.
- `assets/lesson_media/` — complete Quantum/Qiskit educational media library.
- `docs/V6_20_8_VISUAL_RESTORATION_AR.md` — release rationale and restoration details.
