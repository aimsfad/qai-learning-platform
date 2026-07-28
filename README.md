# 3alimnIA V6.7.3 — Bidirectional Hero Gutters

The homepage hero now keeps English/French copy away from the left edge and Arabic RTL copy away from the right edge, with responsive spacing on tablets and phones.

# 3alimnIA V6.7.2 — Classic White Header Logo

3alimnIA is a multilingual generative-AI learning platform for difficult concepts, beginning with Quantum Computing and Qiskit.


## V6.7.2 classic white header logo

- Restored the earlier white rounded header logo treatment requested for the public navigation.
- Added a dedicated `3alimnia_header_logo_white.png` asset so browser caching cannot reuse the dark treatment.
- Preserved the official blue/cyan/gold horizontal wordmark, full RTL/LTR visibility, and responsive sizing.
- No learning, database, assessment, AI Coach, LPQS, or export logic was changed.
- Static validation: `python validate_v672_white_header_logo.py`.

V6 redesigns the public experience after benchmarking Edraak, Brilliant, IBM Quantum Learning, and DataCamp, while preserving the platform's research and pedagogical differentiators:

- learner-first attempts before AI assistance;
- visual and practice-based learning;
- a constrained AI Coach;
- a controlled Concept Builder for educational materials;
- LPQS evaluation of AI responses;
- learner analytics and anonymized research export.

## V6.7 prominent home hero and persistent learner tools

- The approved square 3alimnIA visual with the large wordmark is now the actual homepage hero asset.
- A persistent native learner-tool dock restores direct access to the dashboard, modules/Qiskit, AI Coach, and adaptive plan.
- Assessment and research destinations remain visible in a compact expandable section, including locked-state guidance.
- Navigation continues to use the native Streamlit router; no HTML links or simulated clicks are used.
- The layout remains responsive and supports Arabic RTL, French, and English.


## V6.6 student learning workspace

- Rebuilt the module page as a focused two-column learning workspace.
- Added a compact stage header, collapsible module map, four-step lesson flow, and embedded formative AI coach.
- Preserved research logging, study groups, assessments, LPQS, and database schema.
- Added responsive stacking, RTL support, and dark-mode-compatible surfaces.
- Static validation: `python validate_v66_student_workspace.py`.

## V6.0.1 production UI hotfix

- Professional public header with working native Streamlit callbacks.
- Hidden native navigation registration instead of the visible collapsed menu.
- Cloud-safe official logo rendering through `st.image`.
- Compact hero optimized for 1366×768 and multilingual typography.
- Static validation: `python validate_v601_production_ui.py`.

## Main experiences

### Public platform

- Home
- Programs and learning paths
- Generative AI Studio
- Universities and research
- Learner access
- Evaluator access

### Learner workspace

- Research notice and consent
- Pre-test and adaptive plan
- Six Qiskit learning modules
- AI Tutor Lab and Concept Builder
- Post-test and satisfaction survey
- Progress and completion evidence

### Evaluator and research workspace

- Study protocol
- Participant and registration management
- Learner details
- AI interaction logs
- LPQS response evaluation
- Learning analytics
- Anonymized and administrative exports

## Languages

- العربية — full RTL interface and localized learning content
- Français
- English

Qiskit code, Python syntax, and necessary technical identifiers remain in English.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud

- Main file: `app.py`
- Python dependencies: `requirements.txt`
- Copy `.streamlit/secrets_example.toml` into Streamlit Cloud Secrets and replace placeholder values.
- Do not commit `.streamlit/secrets.toml`, `.env`, or local database files.

## Validation

```bash
python validate_v6_global_academy.py
python -m py_compile app.py ui_v6.py config.py main_app.py router.py
```

Expected result:

```text
V6 global AI academy validation passed.
```

## V6 design files

- `ui_v6.py` — public pages and reusable V6 components
- `.streamlit/v6_theme.css` — V6 visual system and responsive rules
- `V6_GLOBAL_BENCHMARK_AND_REDESIGN_AR.md` — benchmark and design rationale
- `assets/branding/v6_global_academy_preview.html` — static design preview

## Data safety

V6 does not intentionally modify database schemas, participant records, test data, LPQS ratings, AI interaction logs, or research exports. Back up the current database before deployment.

## V6.2 — Evaluator Intelligence Dashboard

The evaluator home now uses live platform data in a modern dashboard: native KPI metrics, analytical tabs, Plotly charts, progress-enabled learner tables, LPQS quality views, and direct anonymized CSV/Excel exports. No mock learner data or server-time theme switching is used.

## V6.3 — Responsive typography and mobile stacking

The interface now uses Tajawal/Alexandria for Arabic and Inter for French/English across native Streamlit controls. On screens up to 720 px, all `st.columns` groups become vertical full-width sections, including the public header, hero actions, cards, filters, metrics, and evaluator layouts. Analytical tabs are also vertical on phones, while wide tables retain controlled horizontal scrolling.

Validation:

```bash
python validate_v63_responsive_ui.py
```


## V6.4 — AI Studio and responsive evidence cards

The Generative AI Studio now opens with a localized premium banner that explains the platform's content-generation, guided-coaching, and LPQS evaluation roles. The home and AI Studio evidence cards use a CSS auto-fit grid: four cards on wide screens, two on tablets, and one on phones.

Validation:

```bash
python validate_v64_ai_studio.py
```

## V6.8 Student Command Workspace

The learner module now uses a 60/40 lesson-and-coach split on desktop, a sticky internally scrollable AI coach, contextual quick-support controls, and the official white 3alimnIA logo across authenticated workspaces. Mobile remains vertically stacked.
