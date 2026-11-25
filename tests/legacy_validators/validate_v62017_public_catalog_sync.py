"""Static regression checks for V6.20.17 public catalog synchronization."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    main_src = read("main_app.py")
    ui_src = read("ui_v6.py")
    brand_src = read("branding.py")
    db_src = read("db.py")

    for filename in ("app.py", "main_app.py", "ui_v6.py", "branding.py", "db.py"):
        ast.parse(read(filename))

    require('APP_VERSION = "v6.20.17-public-catalog-sync"' in db_src, "release marker missing")
    require("import db" in ui_src, "public UI must read the published course catalog")
    require("db.published_teacher_projects_df()" in ui_src, "public UI does not query published projects")
    require("db.teacher_project_runtime_readiness" in ui_src, "public UI must hide runtime-incomplete courses")
    require("_render_teacher_published_courses(direction, compact=True)" in ui_src, "home page catalog missing")
    require("_render_teacher_published_courses(direction, compact=False)" in ui_src, "programs page catalog missing")
    require("pending_published_course_project_id" in ui_src, "public course deep link is not preserved")
    require("pending_published_course_project_id" in main_src, "learner auth does not know the pending course")
    require("_student_destination_after_auth(student)" in main_src, "sign-in/registration redirect missing")
    require("Published Courses" in main_src, "published-course learner route missing")
    require("status_override" in brand_src, "roadmap card cannot become available dynamically")
    require("machine learning" in ui_src and "تعلم الآلة" in ui_src, "ML matching rules missing")
    require("python\"" not in ui_src.split("def _teacher_course_matches_track", 1)[1].split("def _queue_teacher_course", 1)[0].lower(), "Python course must not be mislabeled as ML")
    print("V6.20.17 static regression PASS")


if __name__ == "__main__":
    main()
