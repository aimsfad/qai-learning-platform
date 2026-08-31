"""Regression validation for V6.20.16 final publish consistency.

Reproduces the exact V6.20.15 failure mode: an approved legacy blueprint uses
``concept_explanation`` while generated lesson blocks persist ``explanation``.
A fully approved 4-lesson course must therefore report 4/4 ready, permit final
teacher approval, and permit publication. Removing one canonical block must
reliably return the course to 3/4 and block publication.
"""
from __future__ import annotations

import os
import sys
import tempfile
import types
from pathlib import Path


def _install_streamlit_stub() -> None:
    """Provide only the Streamlit import surface needed by offline DB tests."""
    if "streamlit" in sys.modules:
        return

    class _Secrets(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    def _cache_decorator(*args, **kwargs):
        def wrap(func):
            func.clear = lambda: None
            return func
        return wrap

    module = types.ModuleType("streamlit")
    module.secrets = _Secrets()
    module.cache_resource = _cache_decorator
    module.cache_data = _cache_decorator
    sys.modules["streamlit"] = module


def main() -> None:
    _install_streamlit_stub()
    with tempfile.TemporaryDirectory(prefix="3alimnia_v62016_") as td:
        db_path = Path(td) / "regression.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

        import db
        import lesson_block_generation_engine as blocks

        db.init_db()

        project_id = db.save_teacher_project(
            {
                "teacher_username": "teacher",
                "project_name": "Publish consistency regression",
                "domain": "Programming",
                "program_name": "Python",
                "unit_title": "Python basics",
                "target_concept": "Functions",
                "target_learners": "Beginners",
                "learner_level": "beginner",
                "target_languages": ["Arabic"],
                "primary_language": "Arabic",
                "primary_language_code": "ar",
                "expected_duration": "300 minutes",
                "status": "draft",
            }
        )

        lessons = []
        for index in range(1, 5):
            lessons.append(
                {
                    "lesson_id": f"L{index}",
                    "unit_id": "U1",
                    "title": f"Lesson {index}",
                    "sequence_order": index,
                    # Exact legacy sequence that caused V6.20.15 to report 0/4.
                    "lesson_sequence": [
                        "activation",
                        "concept_explanation",
                        "worked_example",
                        "guided_practice",
                        "independent_practice",
                        "formative_assessment",
                        "summary",
                    ],
                    "concept_ids": [f"C{index}"],
                    "source_ids": [],
                    "prerequisites": [],
                    "misconceptions": [],
                    "activities": [],
                    "assessments": [],
                    "status": "teacher_review",
                }
            )

        blueprint = {
            "units": [
                {
                    "unit_id": "U1",
                    "title": "Unit 1",
                    "description": "",
                    "sequence_order": 1,
                    "lesson_ids": [f"L{i}" for i in range(1, 5)],
                    "concept_ids": [f"C{i}" for i in range(1, 5)],
                    "source_ids": [],
                }
            ],
            "lessons": lessons,
            "outcomes": [],
            "concept_edges": [],
            "concepts": [],
        }
        blueprint_run_id = db.save_teacher_blueprint_bundle(
            project_id=project_id,
            evidence_run_id=0,
            blueprint=blueprint,
            quality={"status": "ready"},
            status="needs_review",
            edited_by="teacher",
        )
        db.approve_teacher_blueprint_run(blueprint_run_id, project_id, "teacher")

        canonical = blocks.ordered_block_types()
        assert canonical == [
            "activation",
            "explanation",
            "worked_example",
            "guided_practice",
            "independent_practice",
            "misconceptions",
            "formative_assessment",
            "summary",
            "resources",
        ], canonical

        for lesson in lessons:
            lesson_id = lesson["lesson_id"]
            for sequence_order, block_type in enumerate(canonical, start=1):
                run_id = db.save_teacher_lesson_block(
                    project_id=project_id,
                    blueprint_run_id=blueprint_run_id,
                    lesson_id=lesson_id,
                    block_type=block_type,
                    sequence_order=sequence_order,
                    prompt_text="test",
                    content_text=f"{block_type} content",
                    provider="test",
                    model="test",
                    status="completed",
                    diagnostic="",
                    validation={"word_count": 10},
                    edited_by="teacher",
                )
                db.exec_sql(
                    "UPDATE teacher_lesson_block_runs SET approved_by_teacher=1, approved_at=:now WHERE id=:id",
                    {"now": db.utc_now(), "id": run_id},
                )

        legacy_expected = db._blueprint_expected_block_types(lessons[0])
        assert "concept_explanation" not in legacy_expected, legacy_expected
        assert "explanation" in legacy_expected, legacy_expected
        assert legacy_expected == canonical, (legacy_expected, canonical)

        readiness = db.teacher_project_runtime_readiness(project_id)
        assert readiness["ready"] is True, readiness
        assert readiness["ready_lesson_count"] == 4, readiness
        assert readiness["lesson_count"] == 4, readiness
        assert readiness["missing_lessons"] == [], readiness

        # End-to-end final teacher approval and publish must now succeed.
        db.set_teacher_project_status(project_id, "teacher", "review")
        project = db.get_teacher_project(project_id, "teacher")
        assert project and project["status"] == "review", project
        db.set_teacher_project_status(project_id, "teacher", "published")
        project = db.get_teacher_project(project_id, "teacher")
        assert project and project["status"] == "published", project

        # Removing one canonical approval must make readiness truthful again.
        db.exec_sql(
            """UPDATE teacher_lesson_block_runs SET approved_by_teacher=0, approved_at=NULL
               WHERE project_id=:project_id AND blueprint_run_id=:blueprint_run_id
                 AND lesson_id='L4' AND block_type='resources'""",
            {"project_id": project_id, "blueprint_run_id": blueprint_run_id},
        )
        readiness = db.teacher_project_runtime_readiness(project_id)
        assert readiness["ready"] is False, readiness
        assert readiness["ready_lesson_count"] == 3, readiness
        assert any(
            item.get("lesson_id") == "L4" and "resources" in (item.get("missing_block_types") or [])
            for item in readiness["missing_lessons"]
        ), readiness

        # Visible project-grid progress must use the actual five-step denominator.
        studio_source = Path(__file__).with_name("teacher_studio.py").read_text(encoding="utf-8")
        assert "{completed}/{total_steps}" in studio_source
        assert "{completed}/{len(PHASES)}" not in studio_source
        assert "teacher_return_to_incomplete_lessons" in studio_source

        blueprint_source = Path(__file__).with_name("lesson_blueprint_engine.py").read_text(encoding="utf-8")
        seq_start = blueprint_source.index("def _lesson_sequence")
        seq_chunk = blueprint_source[seq_start: seq_start + 700]
        assert '"concept_explanation"' not in seq_chunk.replace("``concept_explanation``", "")
        assert '"explanation"' in seq_chunk

        print("V6.20.16 regression PASS")
        print("legacy blueprint alias -> canonical runtime contract: PASS")
        print("fully approved 4-lesson course -> readiness 4/4: PASS")
        print("final teacher approval -> publication: PASS")
        print("missing canonical block -> readiness 3/4: PASS")
        print("five-step card denominator + non-dead-end return path: PASS")


if __name__ == "__main__":
    main()
