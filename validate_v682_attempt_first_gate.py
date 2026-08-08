from pathlib import Path
import ast

from attempt_gate import (
    MIN_ATTEMPT_CHARS,
    MIN_ATTEMPT_WORDS,
    MIN_UNIQUE_WORDS,
    build_attempt_key,
    validate_attempt_text,
)

ROOT = Path(__file__).resolve().parent

for filename in ["attempt_gate.py", "main_app.py", "db.py"]:
    ast.parse((ROOT / filename).read_text(encoding="utf-8"), filename=filename)

assert MIN_ATTEMPT_CHARS == 40
assert MIN_ATTEMPT_WORDS == 6
assert MIN_UNIQUE_WORDS == 4
assert not validate_attempt_text("", "ar").is_valid
assert validate_attempt_text("لا أعرف", "ar").reason == "low_effort"
assert validate_attempt_text("Je ne sais pas", "fr").reason == "low_effort"
assert validate_attempt_text("I don't know", "en").reason == "low_effort"
assert not validate_attempt_text("كلمة كلمة كلمة كلمة كلمة كلمة كلمة كلمة كلمة كلمة", "ar").is_valid
assert validate_attempt_text("أتوقع أن بوابة هادامارد تجعل احتمالي القياس متساويين تقريبًا بعد تكرار التجربة مرات كثيرة.", "ar").is_valid
assert validate_attempt_text("I expect the Hadamard gate to create two balanced measurement outcomes after many repeated shots.", "en").is_valid
assert build_attempt_key(12, "hadamard_superposition") == "v682_attempt_student_12_lesson_hadamard_superposition"

main = (ROOT / "main_app.py").read_text(encoding="utf-8")
db = (ROOT / "db.py").read_text(encoding="utf-8")
assert "disabled=disable_support" in main
assert "db.save_learner_attempt" in main
assert "attempt_first_support_request" in main
assert "CREATE TABLE IF NOT EXISTS learner_attempts" in db
assert '"learner_attempts": learner_attempts_df()' in db
assert '"attempt_text"' in db and 'if strict:' in db
assert any(v in db for v in ('APP_VERSION = "v6.8.2-attempt-first-gate"', 'APP_VERSION = "v6.18.8-teacher-workspace-screenshot-polish"', 'APP_VERSION = "v6.18.7-frictionless-ui-contract"', 'APP_VERSION = "v6.18.6-unified-premium-platform-design"', 'APP_VERSION = "v6.10-gemini-file-analyzer-router"'))

print("V6.8.2 attempt-first gate validation passed.")
