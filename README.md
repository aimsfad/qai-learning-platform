## V6.20.3 — Mobile public shell and first-viewport stabilization

The current release replaces the compressed desktop public navigation on phones with a dedicated compact mobile app bar and native Streamlit popover menu. It also removes mobile top-chrome spacing, forces the home hero into a true single-column hierarchy, prioritizes the primary CTA, constrains the branded visual, and blocks accidental horizontal page scrolling. This pass is based on the live 390px mobile screenshot. See `V6_20_3_MOBILE_PUBLIC_SHELL_AR.md`.

## V6.20.2 - Screenshot-driven visual QA stabilization

The current release applies a screenshot-driven laptop visual QA pass on top of V6.20.1: denser 1366px layouts, stronger text contrast, cleaner learner-tool icons, a wider single-project teacher card, a compact AI Tutor entry, duplicate section-heading cleanup, and a final isolated responsive layer. See `V6_20_2_VISUAL_QA_STABILIZATION.md`.

## V6.20.1 — Responsive visual polish

The current release keeps the V6.20 published-course runtime and adds a final responsive typography/device layer for Arabic, French, and English across desktop, laptop, tablet, and phone. See `V6_20_1_RESPONSIVE_VISUAL_POLISH_AR.md`.

# 3alimnIA V6.20.0 — Published Teacher-Course Runtime

This release closes the gap between the teacher production pipeline and the learner experience. Published teacher projects now run from the teacher-approved blueprint and approved lesson blocks, with blueprint-version pinning, persisted enrollment/progress, an attempt-first lesson gate, end-of-lesson reflection, conservative adaptive support, and a domain-neutral AI coach grounded in approved lesson content. The native learner route for Teacher Courses is registered explicitly, teacher publication now checks runtime readiness, and post-publication delivery metrics are aggregated without exposing raw learner chats. Release packaging excludes `.streamlit/secrets.toml`, `.git`, runtime databases, and caches. See `V6_20_PUBLISHED_COURSE_RUNTIME_AR.md` and `PROJECT_AUDIT_V6_20_AR.md`.

# 3alimnIA V6.19.1 — Learner Evidence Model + Misconception Tracing

This milestone adds a transparent learner-evidence layer without turning the platform into an automated mastery judge. It summarizes observable assessment responses, independent attempts, reflection, transfer evidence, and AI-support context into an interpretable stage and a recommended next pedagogical move. Explicit misconception hypotheses are created only when a wrong distractor carries curated diagnostic metadata; repeated untagged errors remain recurring error patterns that require diagnosis. The Adaptive AI Coach can use these signals conservatively while the teacher retains final authority. A new research surface exposes auditable learner-evidence events without storing raw free-text responses in event metadata. V6.19.0 pedagogical-quality and adaptive-support safeguards remain intact. See `V6_19_1_LEARNER_EVIDENCE_MISCONCEPTION_TRACING_AR.md`.

# 3alimnIA V6.19.0 — Pedagogical Quality Gate + Adaptive AI Coach

This milestone adds a deterministic pedagogical quality gate for teacher-built lessons and a transparent adaptive-support policy for the learner AI Coach. Lesson quality is inspected across outcome alignment, learner activation, scaffolding, practice/transfer, assessment/feedback, misconception repair, metacognition, and representation/access signals. Pedagogical weaknesses remain advisory so the teacher retains final authority; structural/integrity blockers must be repaired before approval. The student coach now estimates the next support level from available pre-test concept evidence, a validated learner attempt, and recent support history, while explicitly avoiding any claim of true mastery. Adaptive decisions are logged for later research/evaluator analysis. V6.18.9 lesson-identity and content-hygiene protections remain intact. See `V6_19_0_PEDAGOGICAL_QUALITY_ADAPTIVE_COACH_AR.md`.

# 3alimnIA V6.18.9 — Lesson Identity & Content Hygiene

This release fixes two live teacher-workspace defects discovered after V6.18.8: bibliographic/source titles leaking into lesson identity and raw model-generated HTML such as `<details><summary>...</summary></details>` appearing literally in lesson review. V6.18.9 introduces a reusable lesson-identity contract, filters source-like concepts before blueprint construction, prevents project-brief fallbacks from claiming traceability to rejected sources, blocks plan approval when every evidence concept is contaminated, blocks contaminated lesson generation/approval, scopes lesson blocks to the approved blueprint version, and renders model content through safe Markdown plus native Streamlit disclosures. Historical blueprint and lesson-block versions are preserved; no database migration or new Secrets are required. See `V6_18_9_LESSON_IDENTITY_CONTENT_HYGIENE_AR.md`.

# 3alimnIA V6.18.8 — Teacher Workspace Screenshot QA & Clarity Polish

This release is a non-destructive visual and presentation hotfix built from the live V6.18.7 teacher-workspace screenshots. It compacts the project header, localizes teacher-facing metadata, removes `Untitled`/placeholder leakage from lesson titles, clarifies lesson-position wording, improves section-chip accessibility, and reduces the footprint of the sticky lesson action bar. Existing AI generation, evidence synthesis, lesson blueprinting, pedagogical orchestration, database schema, routing, and production engines remain intact. See `V6_18_8_TEACHER_WORKSPACE_SCREENSHOT_POLISH_AR.md`.

# 3alimnIA V6.18.7 — Frictionless UI Contract

This release hardens the V6.18.6 premium integration without replacing prior work. It distinguishes researcher and evaluator visual contexts, enforces a calm underlined tab pattern, strengthens keyboard focus and target sizing, restricts Simple Teacher mode to approved/current lessons, and makes the lesson approval action bar reliably sticky. AI engines, database schema, evidence synthesis, blueprints, lesson generation, pedagogical orchestration, LPQS, exports, and routing remain intact. See `V6_18_7_FRICTIONLESS_UI_CONTRACT_AR.md`.

# 3alimnIA V6.18.6 — Unified Premium Platform Design

This release integrates the premium SaaS design shell directly into the existing 3alimnIA application without replacing prior work. Public, learner, teacher, researcher, and evaluator experiences now share one design language while the database, AI engines, evidence pipeline, blueprint workflow, lesson generation, AI Coach, LPQS evaluation, and research exports remain intact. See `V6_18_6_UNIFIED_PREMIUM_PLATFORM_DESIGN_AR.md`.

# 3alimnIA V6.17.1 — Unified Guided Production Journey

This release makes the teacher workflow strictly sequential and approval-driven. It separates the seven-stage teacher journey from the eleven internal production jobs, introduces teacher approval for the canonical research dossier, fixes phase-number collisions in evidence synthesis, and automatically advances after research, evidence, and blueprint approval. See `V6_17_1_UNIFIED_GUIDED_PRODUCTION_JOURNEY_AR.md`.

# 3alimnIA V6.16.5 — UI Stability & Shared Design System

This release consolidates the professional frontend into a safer shared UI layer: validated Streamlit layouts, centralized status semantics, localized error cards, accessible focus states, and reduced-motion support. It preserves the V6.16.4 research export and analytics features and does not alter databases or AI-generation workflows. See `V6_16_5_UI_STABILITY_DESIGN_SYSTEM_AR.md`.

# 3alimnIA V6.16.3 - Professional Layout & Frontend Polish

This release fixes the invalid Streamlit column alignment and upgrades the teacher-facing frontend: centered authentication, adaptive project grids, a minimalist navbar, grouped project metadata, and calmer responsive spacing. It preserves the V6.12-V6.16 research, evidence, blueprint, and lesson-generation engines. See `V6_16_3_PROFESSIONAL_LAYOUT_POLISH_AR.md`.

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

### V6.8.1 learner UX hotfix
V6.8.1 keeps the AI Coach composer inline with the conversation, restores readable contrast in the current-module card, and groups the study roadmap into a professional native Streamlit panel.


## V6.8.2 Attempt-First Gate

The learner workspace now requires a meaningful first attempt before hint, simplification, Qiskit bridge, understanding-check, guided support, or full AI conversation controls are enabled. Validation is multilingual and attempts are stored per learner and module for continuity and research export.

## Teacher Content Studio (V6.9)

The platform now includes a dedicated teacher workspace for producing educational units from a structured brief. Teachers can define the subject, target learners, preferred pedagogy, assessment approach, source material, languages, media requirements, and additional constraints. The platform compiles these inputs with the phase-gated master prompt in `prompts/educational_content_production_master.md`, then generates and stores one approved production phase at a time.

Configure teacher access in `.streamlit/secrets.toml`:

```toml
TEACHER_USERNAME = "teacher"
TEACHER_PASSWORD = "replace-with-a-strong-password"
```

For production, prefer `TEACHER_PASSWORD_HASH`. The studio can reuse the existing LLM provider or use an optional `CONTENT_LLM_PROVIDER` override.


## V6.9.1 — Teacher self-registration

Teachers can now create individual database-backed accounts from the Teacher workspace and sign in with a username or email. Passwords are hashed with PBKDF2-SHA256. Registration is enabled by default and can be controlled with `TEACHER_ALLOW_REGISTRATION`; an optional invitation code can be required with `TEACHER_REGISTRATION_CODE`. Legacy secret-based teacher credentials remain optional and no implicit default teacher password is accepted.

Validation:

```bash
python validate_v691_teacher_accounts.py
```


## V6.9.2 — Project workspaces and learner publication

Every saved teacher project now appears as an independent card in **My educational projects**. Opening a card launches a dedicated project workspace with overview, production, outputs, learner preview, and publication controls. Projects follow a draft → review → published lifecycle, and Phase 3 core educational content is required before publication. Published projects appear in the learner navigation under **Teacher Courses**; drafts and archived projects remain private to their owner.

Validation:

```bash
python validate_v692_project_workspaces.py
```

### V6.9.3 teacher save/prompt reliability
The Teacher Content Studio now saves the project, reloads the canonical database record, compiles the selected phase prompt, and opens the prompt preview immediately. A dedicated **Rebuild prompt** action and persistent success/error feedback are included.


### V6.9.4 branding and teacher prompt stability

The platform now uses `assets/branding/3alimnia_logo_premium.png` as the canonical frameless logo on all major pages. The teacher project save flow also uses a queued workspace-section state, preventing Streamlit from modifying a widget-bound session-state key after instantiation.


## V6.10 — Gemini File Analyzer & Model Router

- Added `model_router.py` for task-aware provider selection and automatic fallback.
- Teacher content generation uses the configured content provider, then can fall back to Gemini, OpenRouter, OpenAI, or Anthropic when their keys are present.
- Added `gemini_file_analyzer.py` for multimodal analysis of PDF, images, audio, and video.
- DOCX, TXT, Markdown, CSV, JSON, and text-readable PDFs retain deterministic local extraction as a fallback.
- Uploaded-source analyses are stored in the project source context with provider/model provenance.
- Updated active defaults to `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, and `gemini-3.6-flash`.
- Deprecated Groq/Gemini model IDs are migrated in code when they remain in an older Secrets configuration.
- Added optional OpenRouter fallback detection; Cohere and Cloudflare credentials are detected for later RAG/serverless modules but are not required for V6.10 file analysis.

Recommended Secrets:

```toml
LLM_PROVIDER = "groq"
GROQ_MODEL = "openai/gpt-oss-20b"
CONTENT_LLM_PROVIDER = "groq"
CONTENT_GROQ_MODEL = "openai/gpt-oss-120b"

FILE_ANALYSIS_PROVIDER = "gemini"
GEMINI_MODEL = "gemini-3.6-flash"
FILE_ANALYSIS_GEMINI_MODEL = "gemini-3.6-flash"
ENABLE_MODEL_FALLBACK = "true"
```

Validation:

```bash
python validate_v610_gemini_router.py
```

### V6.10.1 AI Tutor state safety
Quick-support drafts now use learner-scoped storage and editor keys. Draft cleanup is deferred to the next Streamlit rerun, preventing widget-state mutation exceptions while preserving chat logging and research analytics.

### V6.16 Lesson Blocks
Approved course blueprints can now drive independent generation, review, versioning, and approval of nine lesson blocks. See `V6_16_LESSON_BLOCK_GENERATION_AR.md`.
## V6.16.3.1 frontend runtime hotfix

This hotfix imports the branding module used by the centered teacher login and restores the learner-safe project preview function used by publishing views. Run `python validate_v61631_frontend_runtime_hotfix.py` before deployment.

## V6.16.4 research export and analytics polish

- Strict research-safe export without direct identifiers or high-risk raw free text.
- Unified filters for study group, academic level, completion status, and date range.
- Styled multi-sheet Excel workbook, selected-dataset CSV, data dictionary, and dataset inventory.
- Reproducibility ZIP with CSV copies, codebook, analysis template, manifest, and SHA-256 sums.
- Protected administrative backup with explicit confirmation and export audit log.
- Daily/weekly and line/grouped-bar controls for generative-coach activity.
- Lightweight production-phase cards with compact status badges.

## V6.17 Hybrid Background Production
Long-running teacher production can use an RQ/Redis worker. See `V6_17_HYBRID_BACKGROUND_PRODUCTION_AR.md`.


## V6.17.2 — Simplified Guided Research Flow
- Removed duplicate research actions and clarified the three-step research-review-approval flow.
- Approval now remains the single gate that opens evidence synthesis.

## V6.17.3 — Blueprint action feedback
The course-blueprint build action now shows progress and results in place. It no longer performs an unconditional rerun that made the button appear inactive. Validate before deployment with:

```bash
python validate_v6173_blueprint_action_feedback.py
```

## V6.18 global interface refresh

The platform now uses a shared visual design layer across public pages and the learner, evaluator, and teacher workspaces. See `V6_18_GLOBAL_PROFESSIONAL_DESIGN_SYSTEM_AR.md` for the Arabic implementation guide and run:

```bash
python validate_v618_global_design_system.py
```

## V6.18.2 — Blueprint editor runtime and teacher UI polish

This maintenance release fixes the blueprint editor end to end and removes the visible `</div>` artifact from the teacher workspace header. It also adds the missing unit, lesson, and learning-outcome editing API, aligns manual revision persistence with the database contract, and improves teacher navigation styling.

Validation:

```bash
python validate_v6182_blueprint_editor_runtime_ui.py
python validate_v6181_blueprint_api_contract.py
python validate_v615_blueprint_editor_versioning.py
```

See `V6_18_2_BLUEPRINT_EDITOR_RUNTIME_UI_POLISH_AR.md` for deployment instructions.

## V6.18.3 — Guided blueprint approval and lesson production

The teacher workflow now validates runtime API contracts before rendering, exposes a four-step blueprint review/approval path, and presents the nine lesson blocks as a sequential status map. Approval automatically advances to the next incomplete block. See `V6_18_3_GUIDED_BLUEPRINT_LESSON_PRODUCTION_AR.md`.

Validation:

```bash
python validate_v6183_guided_blueprint_lesson_flow.py
```

## V6.18.4 — Simple Teacher Journey

The teacher workspace now defaults to five clear decisions: course setup, sources, course plan, lesson creation, and review/publishing. A complete lesson can be generated with one action, reviewed as one coherent artifact, and approved before moving to the next lesson. The previous detailed workflow remains available through Advanced mode. See `V6_18_4_SIMPLE_TEACHER_JOURNEY_AR.md`.

## V6.18.5 — Premium Lesson Workspace & Pedagogical Orchestrator

The simple teacher journey now renders generated lessons as a clean learning document instead of exposing raw generation formatting. A dedicated pedagogical orchestration module constrains each lesson section with explicit learning-science intentions (retrieval, scaffolding, worked examples, formative feedback, metacognition, and human approval). The teacher remains the final instructional decision-maker.

Validation:

```bash
python validate_v6185_premium_lesson_workspace.py
```

See `V6_18_5_PREMIUM_LESSON_WORKSPACE_PEDAGOGICAL_ORCHESTRATOR_AR.md` for the research basis, deployment steps, and live-test checklist.
