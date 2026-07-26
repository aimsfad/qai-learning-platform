from pathlib import Path
import py_compile

root = Path(__file__).resolve().parent
main = (root / "main_app.py").read_text(encoding="utf-8")
css = (root / ".streamlit" / "v4_theme.css").read_text(encoding="utf-8")
db = (root / "db.py").read_text(encoding="utf-8")

checks = {
    "quick-action renderer": "def render_evaluator_quick_actions" in main,
    "quick actions above filters": main.index("render_evaluator_quick_actions(u)") < main.index("df = evaluator_filtered_progress()"),
    "old bottom quick-action block removed": 'evaluator_section(u["quick_actions"])' not in main,
    "bounded participant table": "height=352" in main and "v49-data-card-marker" in main,
    "Arabic command descriptions": "الوصول المباشر إلى أكثر أدوات المقيّم" in main,
    "French command descriptions": "Accédez immédiatement aux outils" in main,
    "English command descriptions": "Jump directly to the evaluator tools" in main,
    "command center CSS": ".v49-command-center-marker" in css and ".v49-action-card" in css,
    "responsive CSS": "@media(max-width:1100px)" in css and "flex-wrap:wrap" in css,
    "app version": 'APP_VERSION = "v4.9-evaluator-command-center"' in db,
}

for name, ok in checks.items():
    if not ok:
        raise SystemExit(f"Validation failed: {name}")

for filename in ["main_app.py", "db.py", "i18n.py", "feedback_engine.py"]:
    py_compile.compile(str(root / filename), doraise=True)

print("V4.9 evaluator command-center validation passed.")
