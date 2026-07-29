from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main_app.py"
DB = ROOT / "db.py"

text = MAIN.read_text(encoding="utf-8")
db_text = DB.read_text(encoding="utf-8")

required = [
    'pending_key = f"pending_chat_prompt_{student_state_id}"',
    'editor_key = f"pending_chat_prompt_editor_{student_state_id}"',
    'clear_key = f"pending_chat_prompt_clear_{student_state_id}"',
    'if st.session_state.pop(clear_key, False):',
    'st.session_state[clear_key] = True',
    'prompt = st.session_state.get(editor_key, "")',
]
for marker in required:
    if marker not in text:
        raise AssertionError(f"Missing expected marker: {marker}")

for forbidden in [
    'key="pending_chat_prompt"',
    'st.session_state.pending_chat_prompt = ""',
]:
    if forbidden in text:
        raise AssertionError(f"Unsafe legacy state mutation still present: {forbidden}")

if 'APP_VERSION = "v6.10.1-ai-tutor-state-hotfix"' not in db_text:
    raise AssertionError("Version marker was not updated")

py_compile.compile(str(MAIN), doraise=True)
py_compile.compile(str(DB), doraise=True)
print("V6.10.1 AI Tutor state hotfix validation passed.")
