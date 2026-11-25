"""Dependency-light validation for V6.20.27 AI-generated course pre-tests."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from course_pretest_contract import (  # noqa: E402
    REQUIRED_QUESTION_COUNT,
    SCHEMA_VERSION,
    extract_payload,
    validate_generated_pretest,
)

FILES = {
    name: (ROOT / name).read_text(encoding="utf-8")
    for name in (
        "db.py",
        "published_course_runtime.py",
        "teacher_studio.py",
        "course_pretest_engine.py",
        "course_pretest_contract.py",
        "validate_current_release.py",
        "prompts/educational_content_production_master.md",
    )
}

for name in ("db.py", "published_course_runtime.py", "teacher_studio.py", "course_pretest_engine.py", "course_pretest_contract.py", "validate_current_release.py"):
    ast.parse(FILES[name], filename=name)

sample = {
    "schema_version": SCHEMA_VERSION,
    "course_pretest": [
        {
            "id": "Q1", "question_type": "prerequisite", "concept": "variables",
            "question": "Which statement assigns the integer 3 to x?",
            "options": ["x = 3", "3 = x", "x == 3", "x := '3'"], "correct_index": 0,
            "explanation": "Assignment places the value on the right into the variable on the left.",
            "difficulty": "easy", "cognitive_level": "remember",
        },
        {
            "id": "Q2", "question_type": "prerequisite", "concept": "data types",
            "question": "Which value is a Boolean value in Python?",
            "options": ["True", "'True'", "1.0", "[True]"], "correct_index": 0,
            "explanation": "True is one of Python's two Boolean literals.",
            "difficulty": "easy", "cognitive_level": "remember",
        },
        {
            "id": "Q3", "question_type": "core_concept", "concept": "conditional execution",
            "question": "What does an if statement decide in a program?",
            "options": ["Whether a block runs", "How a file is saved", "How a list is sorted automatically", "Which package is installed"], "correct_index": 0,
            "explanation": "An if statement controls whether its block executes based on a condition.",
            "difficulty": "easy", "cognitive_level": "understand",
        },
        {
            "id": "Q4", "question_type": "misconception", "concept": "comparison operators",
            "question": "Which operator checks whether two Python values are equal?",
            "options": ["==", "=", "!=", ">="], "correct_index": 0,
            "explanation": "Double equals compares values; a single equals sign performs assignment.",
            "difficulty": "medium", "cognitive_level": "understand",
        },
        {
            "id": "Q5", "question_type": "application", "concept": "loops",
            "question": "Which construct is most suitable for repeating an action once for every item in a list?",
            "options": ["for loop", "if statement", "import statement", "class definition"], "correct_index": 0,
            "explanation": "A for loop iterates over each item of an iterable such as a list.",
            "difficulty": "medium", "cognitive_level": "apply",
        },
        {
            "id": "Q6", "question_type": "transfer", "concept": "functions",
            "question": "A calculation is repeated in several places with different inputs. What is the best basic refactoring?",
            "options": ["Put the calculation in a function with parameters", "Duplicate the code again", "Replace every variable with a constant", "Remove the calculation"], "correct_index": 0,
            "explanation": "A parameterized function packages reusable behavior while allowing different inputs.",
            "difficulty": "medium", "cognitive_level": "apply",
        },
    ],
}

raw = "```json\n" + json.dumps(sample) + "\n```"
rows = extract_payload(raw)
normalized, quality = validate_generated_pretest(rows, blocked_titles=["Python basics"])
assert len(normalized) == REQUIRED_QUESTION_COUNT
assert quality["ready"] is True
assert len({q["concept"] for q in normalized}) >= 4

bad = [dict(item) for item in sample["course_pretest"]]
bad[0] = dict(bad[0], question="How familiar are you with Python basics?", concept="$Untitled")
_, bad_quality = validate_generated_pretest(bad, blocked_titles=["Python basics"])
assert bad_quality["ready"] is False
assert any("self_report" in item or "invalid_concept" in item for item in bad_quality["errors"])

checks = {
    "engine version marker": 'COURSE_PRETEST_ENGINE_VERSION = "v6.20.27-ai-generated-course-pretest"' in FILES["db.py"],
    "shared package table": "CREATE TABLE IF NOT EXISTS published_course_pretest_packages" in FILES["db.py"],
    "course version uniqueness": "UNIQUE(project_id, blueprint_run_id)" in FILES["db.py"],
    "content fingerprint persisted": "content_fingerprint TEXT" in FILES["db.py"] and "package_is_current" in FILES["course_pretest_engine.py"],
    "package getter": "def get_published_course_pretest_package" in FILES["db.py"],
    "package saver": "def save_published_course_pretest_package" in FILES["db.py"],
    "runtime uses AI engine": "course_pretest_engine.ensure_course_pretest_package" in FILES["published_course_runtime.py"],
    "runtime preserves emergency fallback": "self_report_baseline" in FILES["published_course_runtime.py"],
    "teacher publish auto generation": "teacher_publish_project" in FILES["teacher_studio.py"] and "ensure_course_pretest_package" in FILES["teacher_studio.py"],
    "teacher regeneration control": "teacher_prepare_pretest_" in FILES["teacher_studio.py"],
    "provider routed generation": "content_generation_engine.generate_content" in FILES["course_pretest_engine.py"],
    "one bounded repair": "_repair_prompt" in FILES["course_pretest_engine.py"],
    "phase8 reuse": "phase8_ai_assessment" in FILES["course_pretest_engine.py"],
    "six-question master contract": "exactly six objective diagnostic multiple-choice questions" in FILES["prompts/educational_content_production_master.md"],
    "release suite includes validator": "validate_v62027_ai_course_pretest.py" in FILES["validate_current_release.py"],
}

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + ": " + name)
if failed:
    raise SystemExit("V6.20.27 validation failed: " + ", ".join(failed))
print(f"V6.20.27 checks: {len(checks)}/{len(checks)} PASS + behavioral contract tests")
