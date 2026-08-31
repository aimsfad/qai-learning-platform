> Current release: **V6.20.15 — Teacher Resume & State Hotfix**

# 3alimnIA V6.20.14 — Final Review & Publish Workflow

V6.20.14 turns the fifth teacher stage into a real, teacher-owned final-review workflow. The former ambiguous **Send for review** state change is replaced by an explicit sequence: readiness check → lesson/source review → learner preview → teacher final approval → publication.

## V6.20.14 highlights

- real final-review workspace instead of a silent status change;
- approved sources and per-lesson readiness are visible in the same screen;
- missing lesson sections are shown with pedagogical labels rather than internal block codes;
- learner preview is embedded before final approval;
- final approval is explicitly the teacher's decision and is not sent to the research evaluator account;
- publication is blocked until the course is runtime-ready **and** the teacher has approved the final version;
- if the course changes after final review, approval becomes stale and must be renewed;
- preserves the V6.20.13 lesson-approval hotfix, V6.20.12 navigation fix, and V6.20.11 temporary demo AI-Coach unlock.

# 3alimnIA — V6.20.10 Label Candidate

V6.20.10 is the presentation and project-label candidate built on the stable V6.20.9 role-polish release. It freezes the current learning, teacher-production, evaluator-research, publication, evidence, and AI-support logic and applies only final screenshot-driven density and spacing corrections.

## Release purpose

This build is intended for:
- project demonstrations and pitch presentations;
- screenshots and recorded walkthroughs;
- project-label / innovation-label submission dossiers;
- stakeholder review before the next functional development cycle.

## Final visual corrections

- compact learner and evaluator authentication headers so the form is visible earlier on common laptop screens;
- reduce remaining dead space in teacher/evaluator internal headers;
- replace the oversized Streamlit divider between the five-step journey and the active production task with a compact branded separator;
- improve visibility of workflow status captions and secondary text;
- preserve the V6.20.5 mobile public header and V6.20.8 visual restoration;
- preserve all Quantum/Qiskit educational media.

## Functional freeze

No routing, database schema, assessment rule, publication gate, learner-evidence logic, adaptive-support policy, LPQS calculation, or teacher-production workflow was intentionally changed in this release.

## Key files

- `.streamlit/app.css` — single production stylesheet including the final label-candidate polish layer.
- `main_app.py` — explicit compact authentication page headers.
- `teacher_studio.py` — compact visual separator in the five-step production journey.
- `db.py` — release identifier only.
- `docs/V6_20_10_LABEL_CANDIDATE_AR.md` — release summary.
- `docs/LABEL_DEMO_CHECKLIST_AR.md` — recommended presentation/demo sequence.
- `docs/VALIDATION_V6_20_10_AR.md` — technical validation summary.



## V6.20.12 — Teacher Navigation Hotfix

- Fixed teacher top navigation so **New project** and **Project workspace** can be selected normally.
- Preserved programmatic Open / Continue / Back navigation for existing projects.
- Preserved the V6.20.11 temporary AI Coach demo unlock.
- No database schema, pedagogical workflow, or media changes.

## V6.20.11 — Demo Coach Unlock

For the label/demo recording, AI Coach access is temporarily available even when the learner has not yet satisfied the attempt-first threshold. The validation rules, evidence model, attempt saving rules, and course-completion requirements remain intact. Restore the original policy by setting `DEMO_BYPASS_ATTEMPT_GATE = False` in `attempt_gate.py`.
