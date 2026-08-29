# 3alimnIA — V6.20.7 Unified Design Merge

3alimnIA is a multilingual Streamlit learning platform for teacher-authored courses, learner-first attempts, structured learning evidence, adaptive support, AI coaching, evaluator analytics, and research export.

This release merges the colleague redesign into the current functional codebase without regressing the V6.20.2–V6.20.6 runtime fixes. It keeps the current mobile public header, Material icons, compact AI Tutor, teacher lesson-review hygiene, published-course runtime, and the cleaned Python core while adopting the unified navy/digital-blue visual system, native Streamlit palette, documentation organization, and Windows launch helpers.

## Preserved educational media

The complete Quantum/Qiskit lesson-media library is retained under `assets/lesson_media/`, including animations, interactive simulators, clean visuals, four-frame concept sequences, legacy segments, professional visuals, and microvideos. These assets are educational content and are not treated as disposable UI files.

## Run locally

```bash
python -m pip install -r requirements.txt
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
- `.streamlit/theme.css` — single unified production design system.
- `assets/lesson_media/` — preserved Quantum/Qiskit educational media.
- `docs/DESIGN_SYSTEM_AR.md` — design-system rationale and tokens.
