# 3alimnIA — V6.20.9 Role Visual Polish

3alimnIA is a multilingual Streamlit learning platform for teacher-authored courses, learner-first attempts, structured learning evidence, adaptive support, AI coaching, evaluator analytics, and research export.

V6.20.9 keeps the complete V6.20.8 visual restoration and applies screenshot-driven consistency improvements across learner, teacher, and evaluator workspaces. It does not change routing, assessment rules, publication logic, evidence collection, or AI-support policy.

## What changed in V6.20.9

- Compact internal page headers so useful workspace content appears earlier in the first viewport.
- Learner progress labels now distinguish module completion from required study-stage completion.
- Internal study codes such as `single_arm` are replaced by learner-facing labels without changing stored data.
- Stronger contrast in the current-module card and learning/AI-coach split view.
- Attempt-first progress text is separated from the progress bar for clearer reading.
- Teacher workspace now includes four live summary KPI cards: projects, published projects, projects in review, and generation runs.
- Evaluator login, command centre, KPI surfaces, and chart containers receive the same visual density as the learner workspace.
- Existing mobile rules and all 85 Quantum/Qiskit educational media files are preserved.

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
- `.streamlit/app.css` — single production stylesheet with the restored visual system plus the final V6.20.9 role-polish layer.
- `assets/lesson_media/` — complete Quantum/Qiskit educational media library.
- `docs/V6_20_9_ROLE_VISUAL_POLISH_AR.md` — screenshot-driven release notes.
