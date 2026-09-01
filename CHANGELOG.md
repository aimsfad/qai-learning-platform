# V6.20.21 — Published course entry routing

- Fixed the public teacher-course entry path so a selected course survives sign-in/account creation and opens the teacher-published runtime instead of the controlled Qiskit study.
- Added a general learner account mode for teacher-published courses without Qiskit-specific self-rating, study access code, or pilot consent.
- Existing emails are directed to sign in rather than create duplicate learner accounts.
- General-course accounts no longer render the Qiskit study progress bar/home by default.
- Added V6.20.21 routing regression checks and wired V6.20.19–V6.20.21/security validators into the current release chain.

# V6.20.20.1 — Security import compatibility hotfix

- Restored `password_policy_error` and `password_is_strong` in `security.py` so the V6.20.20 `db.py` import contract is valid in production.
- Unified new/reset password validation at 8+ characters with at least one letter and one digit while preserving verification of existing password hashes.
- No database schema, learner enrollment, course progress, or published-course data is changed.

# V6.20.20 - Learner account compatibility and UI density

- Kept learner accounts global while preserving per-course enrollment and per-version course baselines.
- Hardened identifier normalization and added non-secret learner-account diagnostics.
- Restored the R2 password-reset policy contract.
- Added a compact density layer for shared headers, cards, forms, and published-course flow.
- Added behavioral regression coverage for one learner enrolling in multiple courses.

# V6.20.5 — Mobile Header Shell

- Rebuilt the mobile public header without Streamlit columns to prevent Cloud responsive stacking.
- Added a dedicated uncropped HTML logo class isolated from legacy brand/image CSS.
- Pinned the native Streamlit popover menu inside the same compact app bar.
- Reduced first-viewport header height while preserving the V6.20.2 desktop/laptop visual system.
- Added V6.20.5 regression validation and sanitized release packaging.

# V6.20.4 — Mobile Header & First-Viewport Hotfix

- Replaced the mobile public-header `st.image` logo with the embedded official data-URI lockup to eliminate the 390px square crop.
- Forced the mobile app bar into a stable logo + 48px menu grid so legacy column rules cannot stack the header.
- Reduced the menu trigger to an icon-sized touch target while preserving accessible label content.
- Removed residual mobile header minimum heights and tightened the gap before the home hero.
- Refined first-viewport Arabic typography without changing public routing or learning logic.
- Added `validate_v6204_mobile_header_first_viewport.py` to the supported regression suite.

# V6.20.3 — Mobile Public Shell & First-Viewport Stabilization

- Replaced the squeezed desktop public header on phones with a dedicated mobile logo + menu shell.
- Added native Streamlit popover navigation and moved public routes, login routes, and language selection into the mobile menu.
- Removed mobile top-chrome spacing across current Streamlit DOM variants.
- Rebuilt the home hero as a true single-column mobile hierarchy with a full-width primary CTA.
- Constrained the mobile hero visual and prevented accidental horizontal page overflow.
- Added `validate_v6203_mobile_public_shell.py`; current regression suite passes 22/22 validators plus compileall.

# V6.20.2 - Screenshot-driven Visual QA Stabilization

- Added a final screenshot-driven visual stabilization layer after V6.20.1.
- Tightened laptop density, navigation, hero scale, program cards, teacher workspace, and lesson review.
- Replaced learner-tool typographic glyphs with Material icons.
- Widened the single-project state and compacted the AI Tutor entry header.
- Prevented duplicate leading generated headings in teacher lesson preview.
- Added and passed the V6.20.2 visual QA validator.

# V6.20.0 — Published Teacher-Course Runtime

- Connected learner-facing Teacher Courses to the teacher-approved blueprint and approved lesson blocks instead of legacy phase previews.
- Added runtime publication readiness and blocked new-format publication until every declared lesson has its required approved blocks.
- Added `published_course_enrollments`, `published_course_lesson_progress`, and `published_course_ai_interactions`.
- Pinned each learner enrollment to the blueprint version active at course start to prevent silent mid-course content drift.
- Added sequential lesson unlocking, persistent position/progress, independent attempt, reflection, and completion state.
- Preserved the attempt-first policy before AI support and reused the transparent learner-evidence/adaptive-support engines without introducing automated mastery claims.
- Added a separate domain-neutral course tutor contract while preserving the controlled Qiskit tutor contract.
- Registered `Published Courses` in the native Streamlit learner router and exposed it in the persistent learner tool dock.
- Added aggregate teacher delivery signals for enrollment, course/lesson completion, and AI-support usage.
- Added `package_release.py`; sanitized releases now exclude local Secrets, VCS history, runtime databases, caches, and editor artifacts.
- Removed accidental repository artifacts (`-v3-9` and malformed pager/output files) from the release.
- Added `validate_v620_published_course_runtime.py` and `validate_current_release.py`; current supported regression suite passes 19/19 validators plus `compileall`.

# V6.19.1 — Learner Evidence Model + Misconception Tracing

- Added `learner_model_engine.py`, an interpretable evidence model that summarizes observed learning signals without claiming true or final mastery.
- Separated evidence coverage from observed assessment performance so missing data is not silently converted into a low ability estimate.
- Added six learner-evidence stages: insufficient, starting, developing, supported, demonstrated, and transfer signal.
- Added conservative next-move recommendations: diagnose, retrieval, guided practice, fade scaffolds, independent retrieval, transfer, and misconception diagnosis.
- Added curated distractor-level diagnostic metadata for selected Qiskit pre/post assessment items.
- Explicit wrong-distractor tags create unconfirmed misconception hypotheses that require human review; generic repeated errors remain recurring error patterns and are never promoted automatically to misconceptions.
- Extended `question_responses` with additive `misconception_code` and `misconception_label` columns. Existing historical responses are preserved and are not retrospectively labelled.
- Added append-only `learner_evidence_events` for assessment responses, attempt-before-support evidence, lesson-completion reflection, and quick self-explanation events.
- Deliberately excluded raw learner free text from learner-evidence event metadata; events store compact structural metadata such as counts, outcome, independence, and support context.
- Connected the Adaptive AI Coach to learner-evidence stages and diagnostic hypotheses conservatively: hypotheses can increase scaffolding, while demonstrated/transfer evidence can reduce support when appropriate.
- Added a prompt guardrail requiring the AI Coach to test a diagnostic hypothesis with a discrimination or contrast question before treating it as fact.
- Added the student-facing “Learner evidence / أدلة تعلمي” panel with evidence chips, next move, and an explicit statement that this is not an automated mastery score.
- Added a Researcher Analytics learner-evidence tab and anonymized strict CSV export surface.
- Added `ENABLE_LEARNER_EVIDENCE_MODEL` and `ENABLE_MISCONCEPTION_TRACING` feature flags, enabled by default in the example Secrets file.
- Added `validate_v6191_learner_evidence_misconception_tracing.py` and updated backward-compatibility validators.

# V6.19.0 — Pedagogical Quality Gate + Adaptive AI Coach

- Added a deterministic `pedagogical_quality_gate.py` so the lesson is not graded by the same LLM that generated it.
- Added eight inspectable quality dimensions: alignment, learner activation, scaffolding, practice/transfer, assessment/feedback, misconception repair, metacognition, and representation/access signals.
- Kept pedagogical-quality scores advisory and teacher-controlled; only structural/integrity blockers prevent approval.
- Added unsafe generated-HTML blocking outside fenced educational code while preserving legitimate code examples.
- Added `adaptive_support_engine.py` with four transparent support levels from transfer challenge to a micro-explanation plus analogous example.
- Preserved the V6.8.2 attempt-first gate: adaptive support is available only after a valid learner attempt.
- Added an adaptive-support prompt contract that prioritizes one next instructional move, productive effort, diagnosis before explanation, and no answer dumping.
- Made the offline/provider-error fallback preserve the same adaptive support level and localize the fallback notice in Arabic/French/English.
- Logged adaptive level, mode, evidence-coverage confidence, and reason on AI interactions for later research/evaluator analysis.
- Added `adaptive_support_analytics_df()` and lesson-level AI support-history retrieval.
- Extended `ai_interactions` through lightweight additive migrations; existing records remain valid.
- Added compact teacher quality-gate and learner adaptive-support UI surfaces with Arabic/French/English copy.
- Added optional `ENABLE_PEDAGOGICAL_QUALITY_GATE` and `ENABLE_ADAPTIVE_AI_COACH` flags, both enabled by default.
- Added `validate_v6190_pedagogical_quality_adaptive_coach.py` and updated compatibility validators.

# V6.18.9 — Lesson Identity & Content Hygiene

- Added `lesson_identity.py` to keep teachable concepts and lesson identity separate from bibliographic/source metadata.
- Reject source/publication titles, file-like names, catalogues, regulations, policies, and source-registry matches when constructing evidence concepts and lesson identities.
- Removed the evidence fallback behavior that could promote source titles into concepts; deterministic fallback now uses safe teacher project concepts only.
- Added blueprint identity diagnostics and an approval boundary that rejects contaminated course plans.
- When every evidence concept is rejected as source metadata, the provisional project-brief outline carries no inherited source IDs, is marked `evidence_rebuild_required`, and cannot be approved until evidence is rebuilt.
- Added a lesson-generation and lesson-approval identity gate so legacy contaminated plans cannot silently create or approve new content.
- Scoped lesson-block reads and approval supersession by `blueprint_run_id`, preserving historical drafts while preventing blocks from an older blueprint version from appearing in a rebuilt course plan.
- Added safe rendering for model-generated `<details>/<summary>` markup: teacher review uses native Streamlit expanders, while general previews/download-oriented normalization uses safe Markdown.
- Kept arbitrary model HTML disabled; HTML is parsed as content rather than rendered with `unsafe_allow_html=True`.
- Preserved HTML/code examples inside fenced code blocks and retained legitimate Python `None` values inside code.
- Improved Arabic heading normalization, including `Case-study` → `دراسة حالة`, without changing persisted model output.
- Added a teacher-facing recovery path from a contaminated lesson back to course-plan rebuild while preserving prior versions in history.
- Added `validate_v6189_lesson_identity_content_hygiene.py` and updated backward-compatibility validators.
- No database migration or new Secrets are required.

# V6.18.8 — Teacher Workspace Screenshot QA & Clarity Polish

- Reviewed the live Streamlit teacher workspace screenshots after V6.18.7 deployment.
- Compacted the project hero to remove excessive vertical whitespace while preserving status, metadata, progress, and project navigation.
- Localized teacher-facing level and duration metadata (for example, `Beginner` → `مبتدئ`, `300 minutes` → `300 دقيقة` in Arabic).
- Removed visible placeholder artifacts such as `Untitled`, `None`, and `null` from lesson titles without rewriting persisted blueprint versions.
- Replaced duplicated/awkward lesson-position copy with natural localized wording such as `الدرس 2 من 4`.
- Added accessible tooltip/ARIA labels to compact lesson-section chips.
- Reduced the visual footprint of the five-step journey and current-stage card while retaining sequential gating.
- Made the sticky lesson decision bar narrower and less intrusive on short laptop viewports.
- Kept Streamlit rerun/stale content visibly distinct while preventing the lesson from becoming almost unreadable during refresh.
- Verified protected AI, evidence, blueprint, pedagogical, and production engines are byte-for-byte unchanged from V6.18.7.
- No database migration or new Secrets are required.

# V6.18.7 — Frictionless UI Contract & Accessibility QA

- Added a distinct researcher visual context inside the existing evaluator/research workspace without changing authentication or permissions.
- Made text-and-underline tabs authoritative over legacy pill-tab CSS, including nested selected-label colors.
- Raised core interaction targets to a 44px comfortable minimum and strengthened visible keyboard focus.
- Limited Simple Teacher lesson navigation to approved lessons plus the current unfinished lesson; future lessons unlock automatically.
- Replaced the incidental sticky lesson-action selector with a keyed, reliable sticky approval/download action bar.
- Added calmer maximum reading width and mobile-safe typography for generated lesson review.
- Preserved all AI, pedagogical, research, database, routing, and generation engines with no schema migration.
- Added `validate_v6187_frictionless_ui_contract.py` and retained backward-compatibility tests.

# V6.18.6 — Unified Premium Platform Design Integration

- Merged the premium SaaS visual shell into the real 3alimnIA application instead of creating a parallel app.
- Standardized the full platform on Tajawal, Midnight/Royal Blue tokens, quiet white surfaces, compact rectangular actions, semantic status badges, and low-noise shadows.
- Added role-scoped visual markers for public, learner, teacher, and evaluator workspaces without changing routing or business logic.
- Preserved the learner split-pane and AI Coach while harmonizing its surfaces with the global design system.
- Restyled the teacher five-step journey as a clear workflow while preserving all V6.18.5 pedagogical orchestration and lesson-generation logic.
- Rebuilt the evaluator response-review screen into a true side-by-side response + LPQS rubric layout.
- Kept research analytics on transparent Plotly surfaces and switched chart typography to Tajawal.
- Added V6.18.6 static validation and updated backward-compatibility validators.

# V6.17.1 — Unified guided production journey

- Enforced one strict seven-stage teacher journey: setup → research → evidence → blueprint → lessons → quality → publish.
- Added teacher approval for the canonical phase-01 research dossier before evidence synthesis can unlock.
- Forced the guided research and evidence workspaces to use the canonical course dossier instead of the legacy current production phase.
- Prevented multiple stages from appearing active or under review at the same time.
- Added automatic navigation after research, evidence, and blueprint approval.
- Added an explicit Now / Completion rule / Next panel for the current stage.
- Reclassified the eleven production phases as an advanced technical log rather than the teacher-facing journey.
- Added lightweight database migration fields for research approval and a dedicated V6.17.1 validation suite.

# V6.16.5 — UI stability and shared design system

- Added `ui_stability.py` for validated Streamlit columns, localized safe errors, incident fingerprints, and centralized status semantics.
- Routed critical teacher, public-navbar, and evaluator layouts through backwards-compatible column handling.
- Replaced raw teacher-workspace exception messages with friendly error cards and collapsed diagnostics.
- Added shared design tokens, semantic status badges, keyboard focus visibility, reduced-motion support, and responsive error/empty states.
- Added repository-wide validation for unsupported `vertical_alignment` values and unresolved global names.

# V6.16.4 — Research export and analytics polish

- Added strict anonymized research exports that exclude direct identifiers and high-risk raw free text.
- Added consistent cohort, level, completion, and date filters across export datasets.
- Added styled Excel workbooks, specialized CSV downloads, data dictionary, dataset inventory, and reproducibility ZIP bundles.
- Added SHA-256 manifests and an evaluator export audit log.
- Added explicit confirmation before preparing full administrative backups.
- Added daily/weekly and line/grouped-bar controls to the AI activity chart.
- Replaced heavy production-map status blocks with compact SaaS-style status badges.

# V6.16.3.1 — Frontend runtime hotfix

- Imported `branding` in `teacher_studio.py` to fix the teacher-login `NameError`.
- Restored `render_project_student_preview` used by publication and learner catalogue views.
- Added unresolved-global-name validation to prevent similar runtime regressions.

# V6.16.3 - Professional Layout & Frontend Polish

- Fixed `StreamlitInvalidVerticalAlignmentError` by replacing unsupported `vertical_alignment="stretch"` with `"top"`.
- Centered the teacher login in a constrained professional card.
- Added an adaptive projects grid: centered single project, two-column pair, and three-column catalog for larger sets.
- Rebuilt the public navbar as a frameless, flat header with one primary CTA.
- Grouped project title, metadata, status, progress, and navigation into one coherent header.
- Reworked project overview metadata into chips and structured cards.
- Added responsive rules for desktop, tablet, and mobile without changing databases or generation engines.

# V6.16.2 - Professional Teacher AI Studio UI

- Replaced duplicate project progress bars with one compact premium header.
- Added a connected seven-stage workflow stepper with clear completed, active, review, available, and locked states.
- Added one dominant current-stage action and a compact project summary panel.
- Introduced a light academic design system using navy, blue, cyan, and restrained gold accents.
- Improved responsive behavior without replacing native Streamlit controls.
- Added `validate_v6162_professional_teacher_ui.py`.

# V6.16.1 - Guided Teacher Workflow UI

- Replaced the flat project-section selector with a seven-stage guided course-building journey.
- Added state-driven completed, current, review, available, and locked workflow statuses.
- Added a current-step card and resume action that returns teachers to the first unfinished stage.
- Added project-level and lesson-block progress indicators.
- Moved phase prompt, token-budget, provider, and export controls into an advanced expander.
- Added a compact review-and-quality readiness dashboard.
- Added friendly provider and rendering error messages with collapsible technical details.
- Added responsive desktop/tablet/mobile workflow styling.
- Added `guided_teacher_workflow.py` and `validate_v6161_guided_teacher_workflow.py`.

# V6.15 — Blueprint Editor and Immutable Versioning

- Added a session-based teacher editor for units, lessons, learning outcomes, concept/source links, durations, prerequisites, and misconceptions.
- Added add, update, delete, and reorder operations while preserving stable identifiers.
- Added immutable blueprint versions with parent links, version numbers, revision type, change summary, editor identity, and restore provenance.
- Added automatic approval invalidation after generation, manual edits, or restoration so stale blueprints cannot constrain later generation.
- Added version comparison and a teacher-facing audit trail.
- Added recomputed integrity, alignment, source-traceability, and readiness checks for every draft and saved version.
- Added `validate_v615_blueprint_editor_versioning.py`.

# V6.14 — Evidence-to-Lesson Blueprint

- Added a provider-independent concept graph and course-blueprint compiler.
- Converts approved evidence into units, lessons, measurable outcomes, activities, and assessments.
- Adds traceable `[U#]`, `[L#]`, and `[LO#]` identifiers to downstream prompts.
- Adds quality gates for concept coverage, prerequisite cycles, source traceability, and alignment.
- Adds teacher review, JSON export, and approval before phase 3 or later generation.
- Added normalized blueprint tables for future research analytics.

# V6.13.1 — Provider Quota Resilience Hotfix

- Classified Gemini quota exhaustion separately from temporary rate limits and stopped useless immediate retries for hard quota failures.
- Added sanitized, teacher-friendly provider diagnostics without billing URLs or organization identifiers.
- Bounded Groq research prompts and output tokens, with one strict `groq/compound-mini` retry after HTTP 413.
- Preserved the latest usable research dossier when a refresh attempt fails.
- Added cached-research fallback metadata and a warning instead of invalidating the project workflow.
- Added deterministic evidence-card and concept fallback when all writing providers are unavailable.
- Added `latest_usable_teacher_research` so failed refresh attempts no longer hide completed research.
- Added `validate_v6131_provider_quota_resilience.py`.

# V6.13 — Evidence Synthesis Foundation

- Added a traceable evidence layer between web research and educational generation.
- Added canonical URL normalization and duplicate-source removal.
- Added multidimensional source scoring for authority, relevance, freshness, pedagogical utility, accessibility, and licence clarity.
- Added normalized persistence for evidence runs, scored sources, evidence cards, and concept/prerequisite candidates.
- Added strict source-ID validation and deterministic fallbacks when structured LLM extraction is unavailable.
- Added a teacher-facing Evidence Synthesis workspace with source assessment, evidence cards, concepts, quality gates, approval, and JSON export.
- Added optional teacher-approval gating before educational generation.
- Replaced oversized raw research dossiers with compact teacher-approved evidence packets in downstream prompts.
- Added `validate_v613_evidence_synthesis.py`.

# V6.12 — Research-Augmented Educational Content Builder

- Added a separate phase-aware web research pass before educational generation.
- Added Gemini Google Search grounding with Groq Compound/Compound Mini fallback.
- Added quick, balanced, and deep research modes, plus preferred/excluded domain controls.
- Added stored research dossiers, query plans, source registries, latency, diagnostics, and fallback metadata.
- Added source authority/diversity checks and `[S1]` citation validation.
- Added a teacher-facing research panel with report, source registry, query list, and JSON export.
- Preserved research evidence during provider prompt compaction.
- Added prompt-injection boundaries for untrusted web content and licensing/freshness rules.
- Prevented automatic phase advancement whenever the research dossier requires teacher review.
- Added `validate_v612_research_augmented_builder.py`.

# V6.11.1 — Prompt Budget and RTL Hotfix

- Added provider-aware runtime prompt budgeting for constrained Groq tiers.
- Preserved the full downloadable prompt while compacting only the provider runtime request.
- Added one strict Groq retry for HTTP 413/token-allowance failures before fallback.
- Sanitized provider diagnostics to remove URLs and organization identifiers.
- Added prompt-budget visibility to the Teacher Content Studio.
- Normalized Arabic phase headings and separated English technical terms from RTL headings.
- Added scoped RTL/LTR output styles for headings, tables, and code blocks.
- Added `validate_v6111_prompt_budget_rtl.py`.

# V6.11 — Educational Content Builder

- Added a phase-specific educational content builder that generates one production phase at a time.
- Chained accepted outputs from previous phases into later prompts.
- Fixed project progress regression after a failed regeneration attempt.
- Added structural output validation, `needs_review`, latency logging, and fallback metadata.
- Advanced projects automatically after a validated generation.
- Added teacher editing and approval of generated phase outputs.
- Added bounded retries and optional Groq GPT-OSS browser research for evidence-sensitive phases.
- Added `validate_v611_content_builder.py`.

# V6.9.2 — Teacher project workspaces and publishing

- Replaced the saved-project selector with responsive project cards and production progress.
- Added a dedicated workspace for each teacher-authored project.
- Added project overview, editing, phase outputs, learner preview, and lifecycle controls.
- Added draft, review, published, and archived states.
- Required a completed Phase 3 output before publication.
- Added a read-only learner catalogue for published teacher projects.
- Added published-course previews for lesson, activity, assessment, AI Coach, and references.
- Preserved teacher ownership and hid drafts from learners.

# V6.9.1 — Teacher accounts

- Added database-backed teacher self-registration.
- Added sign-in with username or email.
- Added secure PBKDF2-SHA256 password hashing.
- Added optional registration invitation code and registration toggle.
- Removed reliance on an implicit default teacher password.
- Preserved optional legacy secret-based administrator access.
- Added multilingual registration UI and per-teacher project ownership.

# Changelog

## V6.8.2 — Attempt-First Gate

- Enforced a genuine learner attempt before any quick-support mode or full AI conversation becomes available.
- Added multilingual validation for minimum detail, word count, lexical diversity, and common low-effort answers.
- Stored the latest valid attempt per learner and lesson before an AI request is submitted.
- Logged the requested support mode and attempt statistics for research analysis.
- Added research-safe attempt metadata to anonymized exports and full attempt text only to protected administrative exports.
- Kept all existing learner, evaluator, assessment, LPQS, and navigation behavior intact.


## V6.8 — Student Command Workspace

- Rebalanced the learning page into a 60/40 lesson and AI-coach workspace.
- Added a sticky, internally scrollable coach panel on desktop.
- Restyled quick-support actions as a compact contextual grid.
- Preserved attempt-first pedagogy and research logging.
- Added the official white brand logo to authenticated learner and evaluator toolbars.
- Preserved vertical mobile stacking and all previous V6.7 tools.

# V6.7.3 — Bidirectional Hero Text Gutters

- Added a clear left gutter for English and French homepage hero text.
- Added the matching right gutter for Arabic RTL hero text.
- Preserved desktop, tablet, and mobile responsive behavior.
- Updated the application version to `v6.7.3-bidirectional-hero-gutters`.

# V6.7.2 — Classic White Header Logo

- Restored the previous white rounded logo design in the right side of the Arabic public header.
- Added a dedicated flattened white logo asset to prevent stale dark versions from browser cache.
- Preserved the full official wordmark and responsive placement in Arabic, French, and English.
- Updated the instrumented application version to `v6.7.2-white-header-logo`.

# V6.7 — Home Brand Hero & Student Tools

- Replaced the homepage's generated CSS illustration with the approved large 3alimnIA brand panel.
- Added a persistent learner tool dock with native buttons for dashboard, modules/Qiskit, AI Coach, and adaptive plan.
- Added a compact assessment/research section with visible locked destinations and localized guidance.
- Preserved the native Streamlit router and learner permission rules.
- Updated the instrumented application version to `v6.7-home-hero-student-tools`.

# V6.6 — Student Learning Workspace

- Rebuilt the learner module page into a two-column lesson-and-coach workspace.
- Added a compact stage header and collapsible module map to reduce vertical page length.
- Added four learner-facing stages: understand, visual experiment, Qiskit bridge, and understanding check.
- Added a compact AI coach that requires a learner attempt before support.
- Added responsive mobile stacking, RTL-aware layout, dark-mode surfaces, and clearer completion controls.
- Updated the instrumented application version to `v6.6-student-learning-workspace`.

# V6.2 — Evaluator Intelligence Dashboard

- Rebuilt the evaluator home with Streamlit-native metrics and tabs.
- Added real-data Plotly charts for pre/post outcomes, daily AI activity, progress distribution, coach modes, and LPQS dimensions.
- Added a progress-enabled learner table using `st.column_config`.
- Added direct anonymized CSV and Excel research exports.
- Added Plotly 6 dependency and a coordinated chart palette.
- Updated the application version to `v6.2-evaluator-intelligence-dashboard`.

# V6.0.1 - Production header and compact hero

- Replaced the visible native navigation dropdown with a professional Streamlit-native public header.
- Kept native page registration in hidden mode for reliable routing.
- Rendered the official logo through `st.image` to prevent broken Cloud images.
- Removed fragile logo data URIs from the hero and footer.
- Reduced hero height, Arabic title scale, top spacing, and first-screen overflow.
- Added direct public navigation to programs, AI Studio, institutions, learner access, and evaluator access.
- Updated the instrumented app version without changing the database schema.

# V5.0.1 - Branding startup hotfix

- Fixed the startup `AttributeError` caused by an obsolete `branding.BRAND_NAME_LATIN` reference.
- Added a backward-compatible brand-name alias.
- Made toolbar fallback resolution safe even when the user role is not set.
- Added a static validation that checks all `branding.*` references against exported symbols.

## V4.8 - Native Docked Navigation

- Replaced the page-column navigation shell with Streamlit's native sidebar.
- Docked the rail by language direction: right for Arabic, left for French/English.
- Added a dedicated viewport-height scroll area for navigation.
- Decoupled navigation height from document height and removed main-page scroll dependency.
- Added responsive drawer behaviour below 900px.
- Updated the instrumented app version to `v4.8-native-docked-navigation`.

## V4.7.1 - Study Protocol Hotfix

- Fixed the evaluator Study Protocol crash caused by outdated PRE_TEST_QUESTIONS and POST_TEST_QUESTIONS attribute names.
- Added backward-compatible assessment collection lookup.
- Localized the full Study Protocol page in Arabic, French, and English.
- Preserved database, assessment content, research exports, and stable Excel sheet names.


## V4.7 - Sticky Compact Navigation

- Applied the same compact sticky navigation shell across learner and evaluator workspaces.
- Added independent sidebar scrolling for laptop screens.
- Reorganized navigation into accessible collapsible groups that keep the active group open.
- Reduced evaluator page-header height and excess vertical whitespace.
- Added responsive fallback to normal page flow on tablet and mobile devices.
- Preserved all multilingual, research, LPQS, database, and export behavior.

# Changelog

## V4.0 - Premium UI & Typography Refresh
- Rebuilt the public landing page with the approved official logo rendered reliably through Streamlit.
- Added Alexandria/Tajawal typography for Arabic and Inter for French/English.
- Added premium RTL/LTR-aware visual hierarchy, responsive layout, cards, forms, tabs, metrics, and evaluator surfaces.
- Added `.streamlit/v4_theme.css`, Streamlit theme configuration, and `.gitattributes`.
- Added `validate_v4_ui.py` and multilingual static previews.
- Preserved all learning, research, database, AI, LPQS, and export behavior.

## V3.1 - Streamlit Cloud display fix

- Fixed raw HTML appearing inside the landing hero.
- Replaced the fragile embedded PNG logo with a self-contained inline SVG lockup.
- Removed the duplicate landing-page language selector.
- Replaced the narrow horizontal radio control with a sidebar-friendly language selectbox.

# سجل تعديلات 3alimnIA

## V3 - التدويل الكامل للمنصة

### اختيار اللغة

- إضافة اختيار عالمي للعربية والفرنسية والإنجليزية.
- تطبيق الاختيار على الصفحة العامة، حساب المتعلم، جميع صفحات الدراسة، والتقييم البحثي.
- إعادة تحميل الواجهة فور تغيير اللغة لتطبيق RTL/LTR بصورة صحيحة.
- حفظ `preferred_language` داخل حساب المتعلم واستعادتها عند تسجيل الدخول.

### المحتوى والتعلمات

- ترجمة الوحدات الست كاملة: الأهداف، المفاهيم، الشرح، الأهمية، الفكرة الكبرى، خطوات التصور، جسر Qiskit، سوء الفهم، المهمة، التحقق، التأمل، ومعايير الإنجاز.
- ترجمة المخططات النصية وتسلسل Observe/Model/Code/Interpret.
- ترجمة الوسائط التعليمية وتعليمات المحاكيات.
- ترجمة 36 سؤال تقييم مع الخيارات والتغذية الراجعة.
- ترجمة الاستبيان والأسئلة المفتوحة.

### الذكاء التوليدي

- مزامنة اللغة المختارة مع AI Coach وAI Tutor والخطة التكيفية.
- إضافة الفرنسية إلى Concept Builder.
- تحسين كشف لغة سؤال المتعلم ليشمل الفرنسية.
- توطين بطاقات Concept Builder والرسائل البريدية لإعادة تعيين كلمة المرور.

### سلامة البحث

- الإبقاء على مفاتيح المفاهيم والوحدات والأسئلة بالإنجليزية داخليًا.
- عدم تغيير بنية السجلات البحثية الحالية.
- إضافة ترحيل تلقائي لحقل `preferred_language` للحسابات الموجودة.

### التحقق

- اجتازت جميع ملفات Python فحص `py_compile`.
- اجتاز فحص المحتوى: 6 وحدات و18 سؤالًا قبليًا و18 سؤالًا بعديًا لكل لغة.
- اجتاز اختبار SQLite لإنشاء الحساب وحفظ اللغة وتغييرها واستعادتها عند المصادقة.

## V3.2 - Official logo restoration
- Restored the approved blue/cyan/gold horizontal 3alimnIA logo.
- Embedded the logo as a base64 data URI to prevent broken paths on Streamlit Cloud.
- Removed the replacement SVG wordmark from the visible interface.
- Added responsive sizing for hero and sidebar use.

## V4.3 - Learning Experience & Navigation
- Grouped learner navigation and adaptive-plan access.
- Premium learner dashboard and progress topbar.
- Assessment cards with question progress.
- Unified lesson selector cards.
- Localized AI Coach quick-start actions.

## V4.5 - Evaluator & Research Dashboard
- Rebuilt the evaluator sidebar into grouped research navigation with system-status visibility.
- Added a multilingual global analysis filter for study group, academic level, learner language, and completion status.
- Added six evaluator KPI cards: learners, complete cases, paired tests, mean gain, AI interactions, and mean LPQS.
- Added tabbed dashboard views for completion workflow, learning outcomes, AI usage, LPQS quality, and system readiness.
- Redesigned learner/account management, participant details, AI logs, response inspection, and LPQS evaluation.
- Added a safer two-track export interface for anonymized research data and full administrative backup.
- Exposed `preferred_language` in evaluator data while preserving the database schema and existing records.
- Added responsive evaluator styling and `validate_v45_evaluator.py`.


## V4.6 - Evaluator localization
- Fixed mixed Arabic/English evaluator headings and learner-detail metrics.
- Added RTL-safe typography for evaluator heroes, metrics, and export cards.

## V4.10 - Compact top alignment and active analysis tabs
- Removed the residual top reserve above the landing and operational pages across Streamlit DOM variants.
- Added a clear segmented-control treatment for horizontal tabs.
- The selected evaluator analysis category now uses a blue-cyan gradient with white text.
- Preserved responsive horizontal scrolling for tabs on narrow screens.

## V4.11 - Escape navigation
- Added an always-visible in-app navigation bar independent of the Streamlit sidebar.
- Added page switcher, Back, Home, Change account, Sidebar open, and Exit actions.
- Prevented users from becoming trapped when the native sidebar is collapsed.
- Added responsive RTL/LTR styling for the safety navigation bar.

## V5 - Native top navigation and reliable account controls

- Replaced custom sidebar routing and the V4.11 escape strip with `st.Page` and `st.navigation(position="top")`.
- Added dynamic role- and permission-aware page registration.
- Added a compact global account toolbar with native callbacks for Home, Change account, Switch workspace, and Sign out.
- Routed internal learning actions through `st.switch_page` via a queued router, preventing stale page state after reruns.
- Restored the Streamlit header required by native top navigation.
- Removed dependence on DOM-click JavaScript for opening navigation.
- Added multilingual navigation sections and active-page styling.
- Updated the application version to `v5-native-top-navigation`.

## V6 — Global AI Academy

- Rebuilt the public experience after benchmarking Edraak, Brilliant, IBM Quantum Learning, and DataCamp.
- Added public Programs, Generative AI Studio, and Universities & Research pages.
- Added modern program cards with level, duration, module count, and availability.
- Added a four-step generative learning engine explanation.
- Added a dedicated institutional/research value proposition.
- Added `ui_v6.py` and `.streamlit/v6_theme.css`.
- Preserved the existing learner, evaluator, database, LPQS, and research workflows.

## V6.3 — Responsive Typography & Vertical Mobile Layout

- Extended Tajawal/Alexandria typography to native Streamlit controls while preserving Material Symbols icons.
- Added tablet wrapping for dense column groups.
- Converted all Streamlit horizontal column groups to full-width vertical stacks on phones.
- Converted mobile tabs into vertical, finger-friendly selectors.
- Improved mobile hero, navigation, cards, metrics, forms, buttons, and research tables.
- Added touch-safe cards and disabled hover-only movement on touch devices.
- Preserved the desktop academy layout and all existing learning, evaluator, AI, LPQS, and export logic.


## V6.4 — AI Studio Banner & Responsive Evidence Grid

- Replaced the generic AI Studio page hero with a premium multilingual generative-learning banner.
- Added localized AI Studio badges, capability tags, and a compact orbital visual.
- Rebuilt platform evidence statistics as a CSS auto-fit grid shared by the home and AI Studio pages.
- Added responsive 4/2/1-column behavior, touch-safe card interactions, and mobile typography.
- Preserved learner, evaluator, AI, LPQS, database, and research-export logic.

## V6.5.1 — Prominent Brand Panel
- Enlarged and centered the 3alimnIA wordmark inside the main generative-learning visual.
- Added a localized subtitle in Arabic, French, and English.
- Rebalanced the AI core, orbits, and Qiskit card to preserve visual hierarchy.
- Added responsive sizing for tablet and mobile screens.

## V6.8.1 — Student UX Hotfix
- Fixed learner dashboard current-module contrast.
- Rebuilt the study roadmap as a native grouped container.
- Replaced the viewport-pinned root chat input with an inline AI Coach composer.
- Compact learner tool dock and responsive dark/light styling.

## V6.9 — Teacher Content Studio

- Added a dedicated teacher workspace and secure teacher sign-in.
- Stored the phase-gated educational-production master prompt under `prompts/`.
- Added structured project briefs for subject content, pedagogy, assessment, references, languages, and requested assets.
- Added PDF, DOCX, and text-source extraction with bounded context limits.
- Added prompt compilation, JSON/Markdown downloads, phase-specific AI generation, and generation history.
- Added `teacher_projects` and `teacher_generation_runs` database tables.
- Added a teacher entry point to the public header and native router.

## V6.9.3 — Save & Prompt Hotfix
- Fixed the teacher project save action appearing inactive after Streamlit reruns.
- Compiles prompts from the canonical project record reloaded from the database.
- Opens the Production section and expands the compiled prompt immediately after saving.
- Added persistent flash feedback, explicit error reporting, and a Rebuild prompt action.
- Scoped form keys per project to prevent stale widget values across projects.


## V6.9.4 — Premium Logo & Prompt State Hotfix
- Adopted the approved frameless quiet-luxury 3alimnIA logo across public and authenticated workspaces.
- Replaced pill/badge styling with transparent negative space and restrained midnight-blue / champagne-gold branding.
- Fixed `StreamlitAPIException` triggered when saving an existing project from the Production section.
- Queued workspace navigation and applies it before the section radio widget is instantiated.

## V6.10 — Gemini File Analyzer & Model Router
- Added task-aware routing for teacher content generation.
- Added automatic fallback across configured Groq, Gemini, OpenRouter, OpenAI, and Anthropic providers.
- Added Gemini multimodal analysis for PDF, image, audio, and video teacher sources.
- Preserved local PDF/DOCX/text extraction when Gemini is unavailable or fails.
- Added source provenance markers to the project prompt context.
- Updated active model defaults and migrated deprecated model IDs safely in code.
- Expanded teacher uploads to include PNG, JPG, WEBP, MP3, WAV, M4A, MP4, and MOV.
- Added sanitized detection for OpenRouter, Cohere, and Cloudflare configuration without exposing secrets.


## V6.10.1 — AI Tutor State Hotfix
- Fixed `StreamlitAPIException` when sending a selected quick-support draft.
- Separated stored draft state from the text-area widget state.
- Deferred draft cleanup until the next rerun, before widget instantiation.
- Scoped AI Tutor draft keys per learner and added a safe cancel action.

## V6.16 - Lesson Block Generation and Versioning
- Added independent generation for nine lesson blocks per approved lesson.
- Added blueprint-constrained prompts, source-ID validation, and attempt-first pedagogy.
- Added immutable block versions, teacher editing, approval, progress tracking, and audit events.
- Added a dedicated Lesson Blocks workspace in Teacher Content Studio.

## V6.17 — Hybrid Background Production
- Added persistent production jobs, RQ/Redis worker support, phase dependency DAG, and batch generation for phases 04–09.


## V6.17.2 — Simplified Guided Research Flow
- Removed duplicate research actions and clarified the three-step research-review-approval flow.
- Approval now remains the single gate that opens evidence synthesis.

## V6.17.3 — Blueprint Action Feedback Hotfix
- Fixed the course-blueprint action appearing inactive after a click.
- Removed the unconditional rerun that moved success and error feedback to the top of the teacher workspace.
- Added an inline progress spinner, immediate success confirmation, and inline safe error reporting.
- Renders the newly created blueprint in the same interaction without requiring a second click or manual page navigation.

## V6.18 — Global Professional Design System

- Added `global_design_system.py` for shared page headers, KPI cards, section headers, action cards, notices, and Plotly styling.
- Unified learner, evaluator, and teacher page headers.
- Centered and constrained learner/evaluator authentication forms.
- Rebuilt evaluator KPI cards and normalized units such as `+30.0 pp`.
- Added transparent dashboard charts with lighter horizontal grids and no vertical grids.
- Replaced filled Streamlit tabs with clean text tabs and an active underline.
- Polished the public navbar, internal toolbar, learner dashboard, teacher project cards, forms, tables, expanders, and alerts.
- Added responsive and accessibility refinements without changing the database schema.

## V6.18.2 — Blueprint Editor Runtime & Teacher UI Polish

- Restored the complete blueprint-editor API used by the teacher workspace.
- Added draft preparation, normalization, comparison, quality recomputation, and CRUD helpers for units, lessons, and outcomes.
- Aligned manual-revision saving with the current database contract while preserving backward compatibility with older calls.
- Invalidates prior blueprint approvals when a new manual revision is saved and records detailed audit events.
- Fixed the teacher header rendering a literal `</div>` after Streamlit reruns by emitting one balanced HTML payload.
- Added a defensive API readiness check before opening the blueprint editor.
- Refined the teacher workspace header, metadata chips, navigation control, KPI typography, and mobile behavior.
- Added a new behavioral/static validation and updated compatibility validators through V6.18.2.
- No database schema migration and no new Secrets are required.

## V6.18.3 — Guided Blueprint & Lesson Production

- Added centralized runtime contracts for blueprint and lesson-block workspaces.
- Added a four-step blueprint build/review/approval/lesson transition.
- Moved blueprint approval to a prominent primary action above long tabs.
- Added a nine-card lesson-block status map with approved, review, running, failed, locked, and not-started states.
- Added optional sequential lesson-block gating through `LESSON_BLOCK_REQUIRE_SEQUENCE`.
- Automatically advances to the next incomplete block after teacher approval.
- Added next-lesson navigation after all required blocks are approved.
- Reused the global design system for blueprint and lesson-production KPIs.
- Added V6.18.3 behavioral/static validation and updated compatibility validators.
- No database migration is required.

## V6.18.4 — Simple Teacher Journey

- Made the five-stage teacher journey the default experience.
- Grouped research and evidence review into one teacher-facing Sources stage.
- Added a simplified course-plan review with one prominent approval action.
- Added one-click complete-lesson generation while preserving immutable section versions.
- Added whole-lesson review and one-click teacher approval before moving to the next lesson.
- Moved provider, model, latency, versions, and technical logs into optional advanced views.
- Kept the existing seven-stage and block-level workflow available through Advanced mode.
- Added responsive five-step navigation, complete-lesson preview cards, and a sticky action area.
- No database migration is required.

## V6.18.5 — Premium Lesson Workspace & Pedagogical Orchestrator

- Added a pedagogical orchestration layer shared by lesson prompts and validation.
- Grounded the canonical lesson sequence in retrieval, worked examples, scaffolding, formative feedback, metacognition, and teacher oversight.
- Added learner-agency rules that preserve attempt-first interaction before hints and full solutions.
- Added a presentation-safe lesson renderer that removes empty `None`/`null` metadata while preserving valid programming values inside code blocks.
- Localized duplicated generated headings in the Arabic teacher view and improved French lesson-section labels.
- Added deterministic checks for unclosed code blocks, attempt/hint/solution structure, retrieval prompts, feedback criteria, and metacognitive reflection.
- Rebuilt the simple lesson workspace around one compact lesson header, course/lesson progress, pedagogical design chips, section navigation, and plain-language quality notes.
- Kept provider/model/latency and raw validation details inside the advanced view.
- No database migration or new Secrets are required.

## V6.20.1 — Responsive Typography & Device UI Polish

- Added an authoritative final responsive stylesheet for desktop, laptop, tablet, phone, and very small phone widths.
- Switched Arabic body UI typography to Noto Sans Arabic with Alexandria headings; retained Inter for Latin UI.
- Improved Arabic line-height, reading measure, touch targets, mobile input sizing, focus visibility, table/tab overflow, and device-aware spacing.
- Reworked the public header, internal toolbar, teacher step flow, and sidebar behavior for narrow screens without changing business logic.
- Added reduced-motion and increased-contrast accessibility preferences.
