"""Validation for V6.18.9 Lesson Identity & Content Hygiene."""
from __future__ import annotations

import ast
import importlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

fake_st = types.ModuleType("streamlit")
fake_st.secrets = {
    "ENABLE_LESSON_BLUEPRINT": "true",
    "ENABLE_BLUEPRINT_EDITOR": "true",
    "ENABLE_LESSON_BLOCK_GENERATION": "true",
    "LESSON_BLOCK_REQUIRE_SEQUENCE": "true",
}
fake_st.cache_resource = lambda *args, **kwargs: (lambda fn: fn)
sys.modules["streamlit"] = fake_st

identity = importlib.import_module("lesson_identity")
renderer = importlib.import_module("lesson_content_renderer")
blueprints = importlib.import_module("lesson_blueprint_engine")
blocks = importlib.import_module("lesson_block_generation_engine")
evidence_engine = importlib.import_module("evidence_synthesis_engine")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(path: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8")
    if path.endswith(".py"):
        ast.parse(text, filename=path)
    return text


def polluted_fixture():
    source_titles = [
        "undergraduate studies catalogue 2022",
        "اللائحة الداخلية للمرحلة البكالوريوس",
    ]
    lesson = {
        "lesson_id": "L3",
        "unit_id": "U1",
        "sequence_order": 3,
        "title": "درس 3: undergraduate studies catalogue 2022 و اللائحة الداخلية للمرحلة البكالوريوس",
        "concept_ids": ["C1", "C2"],
        "source_ids": ["S1", "S2"],
    }
    blueprint = {
        "concepts": [
            {"concept_id": "C1", "name": source_titles[0]},
            {"concept_id": "C2", "name": source_titles[1]},
        ],
        "units": [{"unit_id": "U1", "title": "الوحدة 1", "description": "تعلم بايثون"}],
        "lessons": [lesson],
    }
    project = {
        "id": 1,
        "target_concept": "البرمجة بلغة بايثون",
        "unit_title": "تعلم بايثون",
        "domain": "البرمجة",
        "primary_language_code": "ar",
    }
    return source_titles, lesson, blueprint, project


def validate_identity_gate() -> None:
    source_titles, lesson, blueprint, project = polluted_fixture()
    report = identity.inspect_lesson_identity(
        lesson=lesson,
        blueprint=blueprint,
        project=project,
        source_titles=source_titles,
        index=3,
        lang="ar",
    )
    require(report["valid"] is False, "polluted lesson identity was not blocked")
    require("lesson_title_matches_reference_source" in report["reasons"], "source-title reason missing")
    require("undergraduate studies catalogue 2022" not in report["display_title"], "source title leaked into display identity")
    require(report["display_title"] == "درس 3: البرمجة بلغة بايثون", "safe project fallback title failed")

    clean = identity.inspect_lesson_identity(
        lesson={"lesson_id": "L1", "sequence_order": 1, "title": "درس 1: المتغيرات", "concept_ids": ["C1"]},
        blueprint={"concepts": [{"concept_id": "C1", "name": "المتغيرات"}]},
        project=project,
        source_titles=source_titles,
        index=1,
        lang="ar",
    )
    require(clean["valid"] is True, "valid pedagogical lesson was incorrectly blocked")
    require(clean["display_title"] == "درس 1: المتغيرات", "clean title changed unexpectedly")


def validate_safe_renderer() -> None:
    raw = '''## مثال\n\n<details><summary>إظهار الحل</summary>**الإجابة:** 18 ساعة معتمدة [S1].</details>\n\n```html\n<details><summary>keep in code</summary></details>\n```\n'''
    normalized = renderer.normalize_generated_markdown(raw, "ar")
    require("<details><summary>إظهار الحل" not in normalized, "raw disclosure HTML leaked into general preview")
    require("#### إظهار الحل" in normalized, "disclosure was not flattened safely")
    require("**الإجابة:**" in normalized, "Markdown inside disclosure was damaged")
    require("<details><summary>keep in code</summary></details>" in normalized, "HTML inside fenced code must be preserved")

    segments = renderer.teacher_markdown_segments(raw, "ar")
    disclosures = [item for item in segments if item.get("kind") == "disclosure"]
    require(len(disclosures) == 1, "native disclosure segment parsing failed")
    require(disclosures[0]["label"] == "إظهار الحل", "disclosure label parsing failed")
    require("**الإجابة:**" in disclosures[0]["text"], "disclosure body Markdown was damaged")


def validate_evidence_fallback_hygiene() -> None:
    source = evidence_engine.ScoredSource(
        source_id="S1",
        title="undergraduate studies catalogue 2022",
        url="",
        canonical_url="",
        domain="example.edu",
        source_type="official",
        language="en",
        publication_date="2022",
        access_date="",
        snippet="",
        authority_score=1.0,
        relevance_score=1.0,
        freshness_score=1.0,
        pedagogical_score=1.0,
        accessibility_score=1.0,
        license_score=1.0,
        composite_score=1.0,
        status="approved",
        rationale="",
        fingerprint="S1",
    )
    concepts = evidence_engine._fallback_concepts(
        {
            "target_concept": "Python variables",
            "unit_title": "Intro to Python",
            "domain": "Programming",
            "prerequisites": "",
        },
        [source],
        8,
    )
    names = [item.name for item in concepts]
    require("undergraduate studies catalogue 2022" not in names, "source title entered deterministic fallback concepts")
    require("Python variables" in names, "teacher target concept missing from deterministic fallback")


def validate_blueprint_hygiene() -> None:
    source_titles, _, _, project = polluted_fixture()
    evidence = {
        "id": 12,
        "concepts": [
            {"concept_id": "C1", "name": source_titles[0], "source_ids": ["S1"], "difficulty": "introductory"},
            {"concept_id": "C2", "name": source_titles[1], "source_ids": ["S2"], "difficulty": "introductory"},
        ],
        "sources": [
            {"source_id": "S1", "title": source_titles[0], "status": "approved"},
            {"source_id": "S2", "title": source_titles[1], "status": "approved"},
        ],
        "evidence_cards": [],
    }
    result = blueprints.compile_deterministic_blueprint(project, evidence, max_units=2, max_lessons=4)
    titles = [str(item.get("title") or "") for item in result.blueprint.get("lessons") or []]
    require(titles, "blueprint fallback did not create a lesson")
    require(all("catalogue 2022" not in title for title in titles), "publication title leaked into rebuilt blueprint")
    require(all("اللائحة الداخلية" not in title for title in titles), "regulation title leaked into rebuilt blueprint")
    require(result.quality.get("rejected_source_like_concepts") == 2, "rejected concept count not tracked")
    require(result.quality.get("identity_error_count") == 0, "clean rebuilt blueprint has identity errors")
    require(result.quality.get("evidence_rebuild_required") is True, "fully contaminated evidence must require evidence rebuild")
    require(result.quality.get("source_traceability") == 0.0, "project fallback must not claim traceability to rejected sources")
    require(result.status == "needs_review", "provisional project fallback plan must not be marked completed")
    require(all(not (item.get("source_ids") or []) for item in result.blueprint.get("concepts") or []), "fallback concepts inherited untrusted source ids")


def validate_blueprint_scoped_lesson_state() -> None:
    original_active = blocks._active_blueprint_run_id
    original_latest = blocks.db.latest_lesson_blocks_by_type
    calls = []
    try:
        blocks._active_blueprint_run_id = lambda project_id: 42

        def fake_latest(project_id, lesson_id, *, blueprint_run_id=None):
            calls.append(blueprint_run_id)
            return {
                "activation": {
                    "id": 7,
                    "blueprint_run_id": 42,
                    "approved_by_teacher": 1,
                    "status": "completed",
                }
            }

        blocks.db.latest_lesson_blocks_by_type = fake_latest
        rows = blocks.lesson_block_state(1, "L1", "ar")
        require(calls == [42], "lesson state did not scope reads to the active blueprint")
        require(rows[0]["approved"] is True, "scoped block state was not read")
    finally:
        blocks._active_blueprint_run_id = original_active
        blocks.db.latest_lesson_blocks_by_type = original_latest


def validate_static_integration() -> None:
    teacher = read("teacher_studio.py")
    db_source = read("db.py")
    evidence = read("evidence_synthesis_engine.py")
    blocks_source = read("lesson_block_generation_engine.py")
    css = read(".streamlit/v6_theme.css")

    require(any(v in db_source for v in (
        'APP_VERSION = "v6.20.1-responsive-visual-polish"', 'APP_VERSION = "v6.20.0-published-course-runtime"', 'APP_VERSION = "v6.19.1-learner-evidence-misconception-tracing"', 'APP_VERSION = "v6.19.0-pedagogical-quality-adaptive-coach"',
        'APP_VERSION = "v6.18.9-lesson-identity-content-hygiene"',
    )), "V6.18.9+ app version missing")
    for token in (
        "_render_teacher_lesson_markdown",
        "teacher_markdown_segments",
        "v6189_rebuild_plan_",
        "v6189_rebuild_evidence_",
        "source_titles_from_bundle",
        "inspect_lesson_identity",
    ):
        require(token in teacher, f"teacher integration token missing: {token}")
    require("Concept names must name teachable domain concepts" in evidence, "evidence prompt hygiene rule missing")
    require("blueprint_run_id=blueprint_run_id" in blocks_source, "blueprint-scoped lesson-block reads missing")
    require("Lesson approval blocked because its identity" in db_source, "approval identity boundary missing")
    require("every evidence concept was rejected" in db_source, "evidence rebuild approval boundary missing")
    require("V6.18.9 — Lesson Identity & Safe Content Hygiene" in css, "V6.18.9 CSS layer missing")


def main() -> None:
    validate_identity_gate()
    validate_safe_renderer()
    validate_evidence_fallback_hygiene()
    validate_blueprint_hygiene()
    validate_blueprint_scoped_lesson_state()
    validate_static_integration()
    print("V6.18.9 lesson identity and content hygiene validation passed.")


if __name__ == "__main__":
    main()
