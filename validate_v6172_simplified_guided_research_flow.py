from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent
teacher = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
workflow = (ROOT / "guided_teacher_workflow.py").read_text(encoding="utf-8")
db = (ROOT / "db.py").read_text(encoding="utf-8")
css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")

assert any(v in db for v in ('APP_VERSION = "v6.17.2-simplified-guided-research-flow"', 'APP_VERSION = "v6.17.3-blueprint-action-feedback-hotfix"', 'APP_VERSION = "v6.18-global-professional-design-system"', 'APP_VERSION = "v6.18.6-unified-premium-platform-design"', 'APP_VERSION = "v6.18.5-premium-lesson-workspace"', 'APP_VERSION = "v6.18.4-simple-teacher-journey"', 'APP_VERSION = "v6.18.3-guided-blueprint-lesson-production"', 'APP_VERSION = "v6.18.2-blueprint-editor-runtime-and-ui-polish"'))
assert "v6172-research-steps" in teacher
assert "بدء البحث وجمع المصادر" in teacher
assert "اعتماد المصادر والانتقال إلى تركيب الأدلة" in teacher
assert "أنت داخل هذه المرحلة الآن" in teacher
assert "فتح مساحة المراجع والبحث" in workflow
assert "v6172-current-stage-card" in css
assert "v6172-research-step.active" in css
assert 'vertical_alignment="stretch"' not in teacher

for file_name in ["teacher_studio.py", "guided_teacher_workflow.py", "db.py"]:
    py_compile.compile(str(ROOT / file_name), doraise=True)

print("V6.17.2 simplified guided research flow validation passed.")
