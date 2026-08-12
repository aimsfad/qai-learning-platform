"""Validation for V6.19.1 Learner Evidence Model + Misconception Tracing."""
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
    "ENABLE_LEARNER_EVIDENCE_MODEL": "true",
    "ENABLE_MISCONCEPTION_TRACING": "true",
    "ENABLE_ADAPTIVE_AI_COACH": "true",
}
fake_st.cache_resource = lambda *args, **kwargs: (lambda fn: fn)
sys.modules.setdefault("streamlit", fake_st)

learner_model = importlib.import_module("learner_model_engine")
adaptive = importlib.import_module("adaptive_support_engine")
content = importlib.import_module("content")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(path: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8")
    if path.endswith(".py"):
        ast.parse(text, filename=path)
    return text


def _row(attempt: str, concept: str, correct: int, level: str = "Understanding", code: str = "", label: str = ""):
    return {
        "attempt_type": attempt,
        "question_id": f"{attempt}-{concept}-{level}-{correct}-{code}",
        "concept": concept,
        "is_correct": correct,
        "cognitive_level": level,
        "misconception_code": code,
        "misconception_label": label,
    }


def validate_evidence_stages() -> None:
    empty = learner_model.build_learner_evidence_profile(language_code="en")
    require(empty["stage"] == "insufficient", "empty evidence must remain insufficient")
    require(empty["observed_performance"] is None, "empty evidence fabricated a performance signal")

    developing = learner_model.build_learner_evidence_profile(
        question_responses=[
            _row("pre", "Measurement", 1),
            _row("pre", "Measurement", 0),
        ],
        assessment_concepts=["Measurement"],
        learner_attempt={
            "attempt_text": "I think measurement produces a classical outcome.",
            "validation_status": "submitted_for_support",
            "word_count": 8,
        },
        language_code="en",
    )
    require(developing["stage"] in {"developing", "supported"}, "valid attempt + partial assessment should show developing evidence")
    require(developing["evidence_flags"]["attempt_before_support"] is True, "pre-support attempt evidence missing")

    transfer = learner_model.build_learner_evidence_profile(
        question_responses=[
            _row("pre", "Measurement", 0, "Understanding"),
            _row("post", "Measurement", 1, "Understanding"),
            _row("post", "Measurement", 1, "Application"),
            _row("post", "Measurement", 1, "Application"),
        ],
        assessment_concepts=["Measurement"],
        learner_attempt={
            "attempt_text": "Measurement samples the state into classical data after my prediction.",
            "validation_status": "submitted_for_support",
            "word_count": 10,
        },
        lesson_progress={"completed": 1, "reflection_text": "I can now separate state before measurement from classical output after it."},
        language_code="en",
    )
    require(transfer["stage"] == "transfer_signal", "post + application evidence should create a transfer signal")
    require(transfer["next_move"] == "transfer", "transfer evidence should lead to a new transfer/spaced task")
    require("not an automated final judgement" in transfer["guardrail"], "human-centred learner-model guardrail missing")


def validate_misconception_tracing() -> None:
    tagged = [
        _row("pre", "Measurement", 0, code="measurement_equals_hadamard", label="Confuses measurement with H"),
        _row("post", "Measurement", 0, code="measurement_equals_hadamard", label="Confuses measurement with H"),
    ]
    hypotheses = learner_model.trace_misconception_evidence(tagged, ["Measurement"], "en")
    require(len(hypotheses) == 1, "explicit diagnostic tag not traced")
    require(hypotheses[0]["kind"] == "explicit_misconception_hypothesis", "explicit tag should remain a hypothesis")
    require(hypotheses[0]["status"] == "persistent_hypothesis", "pre/post repeated tag should be persistent hypothesis")
    require(hypotheses[0]["is_confirmed"] is False, "misconception was incorrectly auto-confirmed")
    require(hypotheses[0]["requires_human_review"] is True, "human review flag missing")

    untagged = [
        _row("pre", "Shots", 0),
        _row("post", "Shots", 0),
    ]
    patterns = learner_model.trace_misconception_evidence(untagged, ["Shots"], "en")
    require(patterns and patterns[0]["kind"] == "recurring_error_pattern", "repeated untagged errors should be diagnostic patterns")
    require(patterns[0]["is_confirmed"] is False, "untagged error pattern became a misconception claim")


def validate_adaptive_link() -> None:
    profile = learner_model.build_learner_evidence_profile(
        question_responses=[
            _row("pre", "Measurement", 0, code="measurement_equals_hadamard", label="Confuses measurement with H"),
            _row("post", "Measurement", 0, code="measurement_equals_hadamard", label="Confuses measurement with H"),
        ],
        assessment_concepts=["Measurement"],
        learner_attempt={"attempt_text": "My attempt", "validation_status": "submitted_for_support", "word_count": 4},
        language_code="en",
    )
    decision = adaptive.recommend_support(
        lesson={"concepts": ["Measurement"]},
        learner_attempt={"validation_status": "submitted_for_support", "word_count": 4, "unique_word_count": 4},
        learner_evidence_profile=profile,
        language_code="en",
    )
    require(decision["level"] >= 2, "explicit misconception hypothesis should prevent premature low-support mode")
    require(decision["signals"]["learner_evidence_stage"] == profile["stage"], "learner evidence stage not passed into adaptive support")
    contract = adaptive.prompt_contract(decision)
    require("Learner evidence stage" in contract, "adaptive prompt contract omitted learner evidence stage")
    require("Diagnostic patterns requiring follow-up" in contract, "diagnostic pattern count omitted from adaptive contract")


def validate_content_metadata() -> None:
    q = next(item for item in content.PRE_TEST if item.id == "pre_cb_3")
    require(0 in q.distractor_misconceptions, "curated distractor misconception metadata missing")
    meta = q.distractor_misconceptions[0]
    require(meta.get("code") == "state_vs_classical_output", "unexpected misconception code")


def validate_integration_contracts() -> None:
    db = read("db.py")
    main = read("main_app.py")
    css = read(".streamlit/v6_theme.css")
    secrets = read(".streamlit/secrets_example.toml")

    require('APP_VERSION = "v6.19.1-learner-evidence-misconception-tracing"' in db, "V6.19.1 app version missing")
    for token in [
        "CREATE TABLE IF NOT EXISTS learner_evidence_events",
        "misconception_code",
        "misconception_label",
        "def log_learning_evidence",
        "def learner_evidence_events_df",
        "def student_question_responses_df",
        '"learner_evidence_events": learner_evidence_events_df()',
    ]:
        require(token in db, f"DB learner-evidence contract missing: {token}")

    for token in [
        "import learner_model_engine",
        "_v6191_learner_evidence_profile",
        "render_v6191_learner_evidence_panel",
        "learner_evidence_profile=learner_evidence_profile",
        "db.log_learning_evidence",
        '"Learner evidence"',
    ]:
        require(token in main, f"main UI/model integration missing: {token}")

    require(".v6191-evidence-card" in css and ".v6191-next-move" in css, "learner evidence CSS missing")
    require('ENABLE_LEARNER_EVIDENCE_MODEL = "true"' in secrets, "learner evidence feature flag example missing")
    require('ENABLE_MISCONCEPTION_TRACING = "true"' in secrets, "misconception tracing feature flag example missing")


def main() -> None:
    validate_evidence_stages()
    validate_misconception_tracing()
    validate_adaptive_link()
    validate_content_metadata()
    validate_integration_contracts()
    print("V6.19.1 learner evidence + misconception tracing validation passed.")


if __name__ == "__main__":
    main()
