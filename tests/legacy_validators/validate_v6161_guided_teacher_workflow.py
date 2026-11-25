"""Static and behavioral checks for V6.16.1 Guided Teacher Workflow UI."""
from pathlib import Path

import guided_teacher_workflow as workflow

ROOT = Path(__file__).resolve().parent

base_project = {
    "id": 1,
    "project_name": "Python course",
    "domain": "Programming",
    "unit_title": "Python fundamentals",
    "target_concept": "Python basics",
    "target_learners": "Beginners",
    "source_material": "Teacher notes",
    "status": "draft",
}

state = workflow.evaluate_workflow(base_project)
assert state["statuses"]["setup"] == "completed"
assert state["statuses"]["resources"] == "in_progress"
assert state["statuses"]["evidence"] == "locked"
assert state["statuses"]["blueprint"] == "locked"
assert state["current_key"] == "resources"

review_state = workflow.evaluate_workflow(
    base_project,
    research_runs=[{"status": "completed", "source_count": 6, "approved_by_teacher": 1}],
    evidence={"approved_by_teacher": 0, "status": "needs_review"},
)
assert review_state["statuses"]["resources"] == "completed"
assert review_state["statuses"]["evidence"] == "review"
assert review_state["current_key"] == "evidence"

complete_project = dict(base_project, status="published")
complete_state = workflow.evaluate_workflow(
    complete_project,
    research_runs=[{"status": "completed", "source_count": 8, "approved_by_teacher": 1}],
    evidence={"approved_by_teacher": 1, "status": "approved"},
    blueprint={"approved_by_teacher": 1, "status": "approved"},
    lesson_progress={"required": 18, "available": 18, "approved": 18},
    quality_ready=True,
)
assert all(value == "completed" for value in complete_state["statuses"].values())
assert complete_state["progress_pct"] == 100

teacher = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
assert "import guided_teacher_workflow" in teacher
assert "def _render_guided_workflow" in teacher
assert "def render_project_quality_summary" in teacher
assert any(label in teacher for label in ("التوليد التقني المرحلي — خيارات متقدمة", "السجل التقني المتقدم للتوليد"))
assert "guided_workflow_step_" in teacher
assert "render_project_workspace" in teacher
assert "Project workspace section" not in teacher
assert "v6162-workflow-marker" in css
assert "v6162-step-completed" in css
assert "v6162-step-locked" in css
assert "@media (max-width:980px)" in css
print("V6.16.1 guided teacher workflow validation passed.")
