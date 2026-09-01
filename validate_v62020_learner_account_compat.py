#!/usr/bin/env python3
"""V6.20.20 regression checks for learner-account compatibility and UI density."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

db_text = (ROOT / "db.py").read_text(encoding="utf-8")
css_text = (ROOT / ".streamlit" / "app.css").read_text(encoding="utf-8")
runtime_text = (ROOT / "published_course_runtime.py").read_text(encoding="utf-8")

checks = {
    "version": 'APP_VERSION = "v6.20.20-learner-account-compat-ui-density"' in db_text,
    "global_student_auth": "def authenticate_student" in db_text and "published_course_enrollments" not in db_text[db_text.find("def authenticate_student"):db_text.find("def get_student_by_email")],
    "identifier_normalization": "def normalize_student_identifier" in db_text,
    "safe_auth_diagnostic": "def student_auth_diagnostic" in db_text,
    "password_policy_restored": "password_policy_error(new_password)" in db_text,
    "course_enrollment_per_project": "UNIQUE(student_id, project_id)" in db_text,
    "course_pretest_per_version": "UNIQUE(student_id, project_id, blueprint_run_id)" in db_text,
    "explicit_enrollment_gate_preserved": "v62019_enroll_" in runtime_text and "enroll_action" in runtime_text,
    "baseline_gate_preserved": "if not _render_course_pretest" in runtime_text,
    "compact_css": "V6.20.20 COMPACT DENSITY LAYER" in css_text,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("FAIL static: " + ", ".join(failed))

# Behavioral DB test: one pre-existing learner account can authenticate and enroll
# independently in more than one published course, with course-local pretests.
with tempfile.TemporaryDirectory(prefix="v62020_") as td:
    db_path = Path(td) / "test.db"
    os.environ["DATABASE_URL"] = "sqlite:///" + db_path.as_posix()
    import db

    for cached in (getattr(db, "get_engine", None), getattr(db, "init_db", None)):
        clear = getattr(cached, "clear", None)
        if callable(clear):
            clear()
    db.init_db()

    student = db.create_student(
        full_name="Existing Learner",
        email="existing@example.test",
        institution="Test",
        academic_level="Test",
        prior_python_level=1,
        prior_quantum_level=0,
        password="StrongPass8",
        participant_code="QAI-OLD001",
    )
    sid = int(student["id"])
    assert db.authenticate_student(" QAI-OLD001 ", "StrongPass8")["id"] == sid
    assert db.authenticate_student("\u200bQAI-OLD001\u200b", "StrongPass8")["id"] == sid

    first = db.start_published_course_enrollment(sid, 101, 1001, "L1")
    second = db.start_published_course_enrollment(sid, 202, 2002, "L1")
    assert int(first["student_id"]) == sid and int(second["student_id"]) == sid
    rows = db.query_df("SELECT * FROM published_course_enrollments WHERE student_id=:sid", {"sid": sid})
    assert len(rows) == 2, rows

    questions = [{"id": "q1", "correct_index": 0, "options": ["A", "B"]}]
    db.save_published_course_pretest_attempt(sid, 101, 1001, answers={"q1": 0}, questions=questions)
    assert db.get_published_course_pretest_attempt(sid, 101, 1001) is not None
    assert db.get_published_course_pretest_attempt(sid, 202, 2002) is None

    weak = db.create_password_reset_token("existing@example.test")
    assert weak is not None
    _, token, _ = weak
    ok, _ = db.reset_student_password(token, "short1")
    assert not ok

    engine = db.get_engine()
    engine.dispose()

print(f"V6.20.20 checks: {len(checks)}/{len(checks)} static PASS + behavioral PASS")
