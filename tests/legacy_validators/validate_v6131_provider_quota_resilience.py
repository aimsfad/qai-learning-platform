"""Behavioral validation for V6.13.1 provider quota resilience."""

from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import types
from pathlib import Path

_tmp = tempfile.NamedTemporaryFile(prefix="qai_v6131_", suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

fake_st = types.ModuleType("streamlit")
fake_st.secrets = {
    "ENABLE_RESEARCH_AUGMENTED_GENERATION": "true",
    "ENABLE_EVIDENCE_SYNTHESIS": "true",
    "REQUIRE_EVIDENCE_APPROVAL_FOR_GENERATION": "true",
    "GROQ_API_KEY": "test-key",
    "CONTENT_GROQ_RESEARCH_MODEL": "groq/compound",
    "CONTENT_GROQ_QUICK_RESEARCH_MODEL": "groq/compound-mini",
    "CONTENT_GROQ_RESEARCH_INPUT_TOKENS": "1000",
    "CONTENT_GROQ_RESEARCH_STRICT_INPUT_TOKENS": "500",
    "CONTENT_GROQ_RESEARCH_MAX_OUTPUT_TOKENS": "1200",
    "CONTENT_GROQ_RESEARCH_STRICT_OUTPUT_TOKENS": "600",
}
fake_st.cache_resource = lambda *args, **kwargs: (lambda fn: fn)
sys.modules["streamlit"] = fake_st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

db = importlib.import_module("db")
web_research_engine = importlib.import_module("web_research_engine")
content_generation_engine = importlib.import_module("content_generation_engine")
evidence_synthesis_engine = importlib.import_module("evidence_synthesis_engine")
educational_builder = importlib.import_module("educational_builder")


class FakeResponse:
    def __init__(self, status_code: int, payload=None, text: str = "", headers=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text or json.dumps(self._payload)
        self.headers = headers or {}

    def json(self):
        return self._payload


def project_payload() -> dict:
    return {
        "teacher_username": "validator",
        "project_name": "Quota resilient course",
        "domain": "Programming",
        "program_name": "Python foundations",
        "unit_title": "Variables",
        "target_concept": "Python variables",
        "target_learners": "Beginners",
        "learner_level": "Beginner",
        "prerequisites": "Basic computer use",
        "target_languages": ["Arabic"],
        "primary_language": "Arabic",
        "primary_language_code": "ar",
        "expected_duration": "45 minutes",
        "technical_environment": "Python 3",
        "platform_components": ["AI Coach"],
        "source_material": "Teacher notes",
        "teaching_preferences": "Attempt first",
        "assessment_preferences": "Formative assessment",
        "additional_notes": "",
        "requested_outputs": ["Lesson"],
        "current_phase": 1,
        "status": "draft",
    }


def sources() -> list[web_research_engine.ResearchSource]:
    return [
        web_research_engine.ResearchSource(
            "S1", "Python reference", "https://docs.python.org/3/reference/", "docs.python.org",
            "official technical documentation", 5, "Assignment binds names to objects.", 0.95,
        ),
        web_research_engine.ResearchSource(
            "S2", "Python tutorial", "https://docs.python.org/3/tutorial/", "docs.python.org",
            "official technical documentation", 5, "The tutorial gives executable examples.", 0.91,
        ),
        web_research_engine.ResearchSource(
            "S3", "University teaching guide", "https://example.edu/python-teaching", "example.edu",
            "university or academic institution", 5, "Misconception-based assessment supports beginners.", 0.84,
        ),
    ]


def main() -> None:
    # Friendly diagnostics must not expose provider links or raw quota prose.
    friendly = web_research_engine._friendly_provider_failure(
        "gemini",
        RuntimeError("gemini HTTP 429: You exceeded your current quota, check billing at https://provider.example/usage"),
    )
    assert "quota is currently exhausted" in friendly
    assert "http" not in friendly.lower()

    # Prompt compaction is bounded.
    long_prompt = "research evidence " * 5000
    compact = web_research_engine._truncate_to_tokens(long_prompt, 500)
    assert web_research_engine._estimate_tokens(compact) <= 510

    # Groq retries a 413 exactly once with Compound Mini and a stricter prompt.
    original_post = web_research_engine._post_json
    calls = []

    def fake_post(url, headers, payload, provider):
        calls.append(payload)
        if len(calls) == 1:
            return FakeResponse(413, {"error": {"message": "Request Entity Too Large"}})
        return FakeResponse(
            200,
            {
                "choices": [{
                    "message": {
                        "content": "Verified findings with sources.",
                        "executed_tools": [{
                            "search_results": {"results": [
                                {"title": "Python docs", "url": "https://docs.python.org/3/", "content": "Official docs"},
                                {"title": "Python tutorial", "url": "https://docs.python.org/3/tutorial/", "content": "Tutorial"},
                            ]}
                        }],
                    }
                }]
            },
        )

    web_research_engine._post_json = fake_post
    try:
        report, found_sources, _, model = web_research_engine._call_groq(
            long_prompt,
            max_sources=5,
            preferred_domains=[],
            excluded_domains=[],
            mode="balanced",
        )
    finally:
        web_research_engine._post_json = original_post
    assert report
    assert found_sources
    assert model == "groq/compound-mini"
    assert len(calls) == 2
    assert calls[0]["model"] == "groq/compound"
    assert calls[1]["model"] == "groq/compound-mini"
    assert web_research_engine._estimate_tokens(calls[1]["messages"][0]["content"]) <= 510

    # A failed refresh must not replace the latest usable dossier.
    db.init_db()
    project_id = db.save_teacher_project(project_payload())
    project = db.get_teacher_project(project_id, "validator")
    assert project
    usable_id = db.save_teacher_research_run(
        project_id=project_id,
        phase_number=1,
        research_mode="balanced",
        query_plan_json="[]",
        report_text="A valid cached research dossier with enough detail and authoritative sources.",
        sources_json=web_research_engine.sources_to_json(sources()),
        provider="gemini",
        model="test",
        status="completed",
        diagnostic="ok",
        source_count=3,
    )
    failed_id = db.save_teacher_research_run(
        project_id=project_id,
        phase_number=1,
        research_mode="balanced",
        query_plan_json="[]",
        report_text="",
        sources_json="[]",
        provider="gemini",
        model="test",
        status="provider_unavailable",
        diagnostic="quota exhausted",
        source_count=0,
    )
    assert int(db.latest_teacher_research(project_id, 1)["id"]) == failed_id
    assert int(db.latest_usable_teacher_research(project_id, 1)["id"]) == usable_id

    # Manual refresh returns the cached dossier with a visible fallback flag.
    original_research = web_research_engine.run_phase_research
    web_research_engine.run_phase_research = lambda *args, **kwargs: web_research_engine.ResearchResult(
        report="", sources=[], queries=["query"], provider="gemini", model="unknown",
        status="provider_unavailable", diagnostic="providers unavailable", latency_ms=10,
    )
    try:
        returned = educational_builder.run_project_research(
            project,
            "validator",
            phase_number=1,
            research_mode="balanced",
        )
    finally:
        web_research_engine.run_phase_research = original_research
    assert int(returned["id"]) == usable_id
    assert int(returned["cache_fallback_used"]) == 1
    assert returned["refresh_status"] == "provider_unavailable"

    # Evidence synthesis degrades to deterministic records instead of a hard error.
    research_run = db.latest_usable_teacher_research(project_id, 1)
    original_generate = content_generation_engine.generate_content
    content_generation_engine.generate_content = lambda *args, **kwargs: content_generation_engine.ContentGenerationResult(
        response="Generation failed.", provider="gemini", model="test", status="error",
        diagnostic="quota unavailable", latency_ms=5,
    )
    try:
        result = evidence_synthesis_engine.synthesize_evidence(project, 1, research_run)
    finally:
        content_generation_engine.generate_content = original_generate
    assert result.status == "needs_review"
    assert result.provider == "deterministic"
    assert result.model == "evidence-fallback-v1"
    assert result.evidence_cards and result.concepts
    assert result.used_fallback

    print("V6.13.1 provider quota resilience validation passed.")


if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            os.unlink(_tmp.name)
        except OSError:
            pass
