"""Validation for 3alimnIA V6.17.1 unified guided production journey."""
from __future__ import annotations

from pathlib import Path

import guided_teacher_workflow as workflow


ROOT = Path(__file__).resolve().parent


def _project() -> dict:
    return {
        "id": 1,
        "project_name": "Learn Python",
        "domain": "Programming",
        "unit_title": "Python fundamentals",
        "target_concept": "Python basics",
        "target_learners": "Beginners",
        "source_material": "",
        "status": "draft",
    }


def main() -> None:
    project = _project()

    unapproved_research = [{
        "status": "completed",
        "source_count": 6,
        "approved_by_teacher": 0,
        "phase_number": 1,
    }]
    out_of_order_evidence = {"approved_by_teacher": 1, "phase_number": 1}
    state = workflow.evaluate_workflow(
        project,
        research_runs=unapproved_research,
        evidence=out_of_order_evidence,
    )
    assert state["current_key"] == "resources", state
    assert state["statuses"]["resources"] == "review", state
    assert state["statuses"]["evidence"] == "locked", state
    assert state["statuses"]["blueprint"] == "locked", state

    approved_research = [{
        "status": "completed",
        "source_count": 6,
        "approved_by_teacher": 1,
        "phase_number": 1,
    }]
    state = workflow.evaluate_workflow(project, research_runs=approved_research)
    assert state["statuses"]["resources"] == "completed", state
    assert state["statuses"]["evidence"] == "available", state
    assert state["current_key"] == "evidence", state

    approved_evidence = {"approved_by_teacher": 1, "phase_number": 1}
    state = workflow.evaluate_workflow(
        project,
        research_runs=approved_research,
        evidence=approved_evidence,
    )
    assert state["statuses"]["evidence"] == "completed", state
    assert state["statuses"]["blueprint"] == "available", state
    assert state["current_key"] == "blueprint", state

    teacher_source = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
    db_source = (ROOT / "db.py").read_text(encoding="utf-8")
    css_source = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")

    assert "latest_approved_teacher_research" in teacher_source
    assert "phase_number = 1" in teacher_source
    assert any(marker in teacher_source for marker in ("Canonical course research dossier", "Research results and source review", "نتائج البحث ومراجعة المصادر"))
    assert any(marker in teacher_source for marker in ("v6171-stage-flow", "v6172-current-stage-card"))
    assert any(marker in css_source for marker in ("v6171-stage-flow", "v6172-current-stage-card"))
    assert "def approve_teacher_research_run" in db_source
    assert "approved_by_teacher INTEGER DEFAULT 0" in db_source
    assert any(v in db_source for v in ('APP_VERSION = "v6.17.1-unified-guided-production-journey"', 'APP_VERSION = "v6.17.2-simplified-guided-research-flow"', 'APP_VERSION = "v6.17.3-blueprint-action-feedback-hotfix"', 'APP_VERSION = "v6.18-global-professional-design-system"', 'APP_VERSION = "v6.20.3-mobile-public-shell"', 'APP_VERSION = "v6.20.1-responsive-visual-polish"', 'APP_VERSION = "v6.20.0-published-course-runtime"', 'APP_VERSION = "v6.19.1-learner-evidence-misconception-tracing"', 'APP_VERSION = "v6.19.0-pedagogical-quality-adaptive-coach"', 'APP_VERSION = "v6.18.9-lesson-identity-content-hygiene"', 'APP_VERSION = "v6.18.8-teacher-workspace-screenshot-polish"', 'APP_VERSION = "v6.18.7-frictionless-ui-contract"', 'APP_VERSION = "v6.18.6-unified-premium-platform-design"', 'APP_VERSION = "v6.18.5-premium-lesson-workspace"', 'APP_VERSION = "v6.18.4-simple-teacher-journey"', 'APP_VERSION = "v6.18.3-guided-blueprint-lesson-production"', 'APP_VERSION = "v6.18.2-blueprint-editor-runtime-and-ui-polish"'))
    assert 'vertical_alignment="stretch"' not in teacher_source

    print("V6.17.1 unified guided production journey validation passed.")


if __name__ == "__main__":
    main()
