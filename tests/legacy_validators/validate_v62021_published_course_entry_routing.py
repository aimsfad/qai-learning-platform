#!/usr/bin/env python3
"""Dependency-light regression checks for V6.20.21 course entry routing."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
main = (ROOT / "main_app.py").read_text(encoding="utf-8")
db_text = (ROOT / "db.py").read_text(encoding="utf-8")
runtime = (ROOT / "published_course_runtime.py").read_text(encoding="utf-8")


def section(text: str, start: str, end: str) -> str:
    a = text.find(start)
    b = text.find(end, a + len(start)) if a >= 0 else -1
    if a < 0 or b < 0:
        return ""
    return text[a:b]


destination = section(main, "def _student_destination_after_auth", "def _render_public_published_courses")
registration = section(main, "def render_student_registration", "# -----------------------------------------------------------------------------\n# Student study flow")
pages_allowed = section(main, "def student_pages_allowed", "# -----------------------------------------------------------------------------\n# Landing and access")
student_app = section(main, "def render_student_app", "def require_student")
study_group = section(main, "def study_group_label", "def ai_features_available")

checks = {
    "version": 'APP_VERSION = "v6.20.21-published-course-entry-routing"' in db_text,
    "pending_course_helper": "def _pending_published_project()" in main,
    "pending_auth_sets_selected_course": "st.session_state.published_course_project_id = project_id" in destination,
    "pending_auth_opens_published_courses": 'return "Published Courses"' in destination,
    "general_course_account_mode": 'study_group="general_course"' in registration,
    "general_course_skips_quantum_self_rating": "if course_registration:" in registration and "prior_python = 0" in registration and "prior_quantum = 0" in registration,
    "general_course_skips_pilot_consent": "if course_registration:\n                    consent = True" in registration,
    "general_course_no_duplicate_account": "course_registration and db.get_student_by_email(email)" in registration,
    "general_course_not_forced_into_research_pages": "if _is_general_course_account(student):\n        return pages" in pages_allowed,
    "general_course_not_auto_randomized": 'if group == "general_course":\n        return group' in study_group,
    "published_courses_hide_quantum_progress_bar": 'page not in {"Sign in", "Create account", "Published Courses"}' in student_app,
    "explicit_course_enrollment_preserved": "v62019_enroll_" in runtime and "start_published_course_enrollment" in runtime,
    "course_local_pretest_preserved": "if not _render_course_pretest" in runtime and "get_published_course_pretest_attempt" in runtime,
    "pilot_pretest_not_used_by_runtime": "get_test_attempt" not in section(runtime, "def render_course", "def _render_lesson_runtime"),
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("FAIL: " + ", ".join(failed))

for filename, source in (("main_app.py", main), ("db.py", db_text), ("published_course_runtime.py", runtime)):
    ast.parse(source, filename=filename)

print(f"V6.20.21 checks: {len(checks)}/{len(checks)} PASS")
