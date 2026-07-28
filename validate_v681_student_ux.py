from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
main = (ROOT / "main_app.py").read_text(encoding="utf-8")
css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
db = (ROOT / "db.py").read_text(encoding="utf-8")

ast.parse(main)
ast.parse(db)

assert 'key="v681_chat_composer"' in main
assert 'st.form("v681_chat_composer_form"' in main
assert 'st.chat_input("Ask about the current module' not in main
assert 'key="v681_roadmap"' in main
assert 'APP_VERSION = "v6.8.1-student-ux-hotfix"' in db
assert '.v43-resume-card *' in css
assert '.st-key-v681_chat_composer' in css
assert '.st-key-v681_roadmap' in css

print("V6.8.1 student UX hotfix validation passed.")
