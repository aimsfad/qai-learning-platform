"""Validation for V6.19.0 Pedagogical Quality Gate + Adaptive AI Coach."""
from __future__ import annotations

import ast
import importlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Keep this validator deterministic and independent of a live Streamlit/DB.
fake_st = types.ModuleType("streamlit")
fake_st.secrets = {
    "ENABLE_LESSON_BLOCK_GENERATION": "true",
    "ENABLE_PEDAGOGICAL_QUALITY_GATE": "true",
    "ENABLE_ADAPTIVE_AI_COACH": "true",
}
fake_st.cache_resource = lambda *args, **kwargs: (lambda fn: fn)
sys.modules.setdefault("streamlit", fake_st)

quality_gate = importlib.import_module("pedagogical_quality_gate")
adaptive = importlib.import_module("adaptive_support_engine")
feedback_runtime = importlib.import_module("feedback_engine")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(path: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8")
    if path.endswith(".py"):
        ast.parse(text, filename=path)
    return text


def _row(block_type: str, text: str, *, errors=None, warnings=None, cited=("S1",)):
    return {
        "block_type": block_type,
        "content_text": text,
        "run": {
            "validation": {
                "errors": list(errors or []),
                "warnings": list(warnings or []),
                "cited_source_ids": list(cited or []),
            }
        },
    }


def _good_lesson_rows():
    return [
        _row("activation", "استرجع ما تعرفه عن المتغيرات: ما الفرق بين الاسم والقيمة؟ توقّع الناتج. [S1]"),
        _row("explanation", "شرح المفهوم مع مثال وجدول بسيط يربط الاسم بالقيمة. [S1]"),
        _row("worked_example", "جرّب أولًا: ما الناتج؟\nتلميح: تتبع القيمة.\nالحل النموذجي: مثال جديد.\nتحقق ذاتي: غيّر القيمة. [S1]"),
        _row("guided_practice", "تدريب موجه. تلميح عام ثم نقطة تحقق: ما الخطوة التالية؟ [S1]"),
        _row("independent_practice", "تطبيق جديد في حالة جديدة. معيار النجاح: اكتب حلاً صحيحًا وفسره. [S1]"),
        _row("misconceptions", "خطأ شائع: الخلط بين الاسم والقيمة. التصحيح: الصحيح هو... تحقق: أي عبارة صحيحة؟ [S1]"),
        _row("formative_assessment", "معيار النجاح: 80%. سؤال؟ تغذية راجعة فورية. إذا أخطأ أعد التدريس أو قدم مثال إضافي، وإذا نجح انتقل. [S1]"),
        _row("summary", "تأمل: ماذا تغير في فهمك؟ فكّر في الخطوة التالية وسأراجع المثال قبل الدرس التالي. [S1]"),
        _row("resources", "موارد ومتابعة: جدول مراجعة ومثال إضافي. [S1]"),
    ]


def validate_quality_gate_good_lesson() -> None:
    lesson = {
        "learning_outcomes": ["يعرّف المتغير", "يستخدم المتغير"],
        "assessments": ["سؤال تكويني"],
        "source_ids": ["S1"],
    }
    report = quality_gate.evaluate_lesson(lesson, _good_lesson_rows(), language_code="ar")
    require(report["can_approve"] is True, "a structurally valid lesson was blocked")
    require(report["status"] == "ready", "high-quality fixture should be ready")
    require(report["quality_score"] >= 80, "high-quality fixture score is unexpectedly low")
    require(report["blocker_count"] == 0, "unexpected blockers on good lesson")
    keys = {item["key"] for item in report["dimensions"]}
    require(keys == {item["key"] for item in quality_gate.DIMENSIONS}, "quality dimensions are incomplete")


def validate_quality_gate_blockers_and_advisories() -> None:
    lesson = {"learning_outcomes": [], "assessments": [], "source_ids": ["S1"]}
    rows = _good_lesson_rows()[:-1]  # missing resources is a hard structural blocker
    report = quality_gate.evaluate_lesson(lesson, rows, language_code="en")
    require(report["can_approve"] is False, "missing required section must block approval")
    require(any(str(item).startswith("missing_lesson_section:resources") for item in report["blockers"]), "missing section blocker absent")
    require("outcomes_missing" in report["warnings"], "outcome advisory absent")

    unsafe_rows = _good_lesson_rows()
    unsafe_rows[1] = _row("explanation", "شرح عادي <script>alert('x')</script>")
    unsafe = quality_gate.evaluate_lesson(
        {"learning_outcomes": ["هدف"], "assessments": ["تقويم"], "source_ids": []},
        unsafe_rows,
        language_code="ar",
    )
    require(unsafe["can_approve"] is False, "unsafe generated HTML must block approval")
    require(any(str(item).startswith("unsafe_html_detected:explanation") for item in unsafe["blockers"]), "unsafe HTML blocker missing")

    fenced_rows = _good_lesson_rows()
    fenced_rows[1] = _row("explanation", "مثال HTML تعليمي:\n```html\n<script>demo()</script>\n```\nثم اشرح المثال. [S1]")
    fenced = quality_gate.evaluate_lesson(
        {"learning_outcomes": ["هدف"], "assessments": ["تقويم"], "source_ids": ["S1"]},
        fenced_rows,
        language_code="ar",
    )
    require(not any(str(item).startswith("unsafe_html_detected") for item in fenced["blockers"]), "HTML inside fenced teaching code was incorrectly blocked")


def validate_adaptive_support_policy() -> None:
    lesson = {"concepts": ["Measurement"]}

    strong_pre = {
        "score": 90,
        "correct_count": 9,
        "total_count": 10,
        "per_concept_json": '{"Measurement":{"correct":9,"total":10}}',
    }
    strong_attempt = {
        "validation_status": "valid_draft",
        "word_count": 26,
        "unique_word_count": 19,
    }
    strong = adaptive.recommend_support(
        lesson=lesson,
        pre_attempt=strong_pre,
        learner_attempt=strong_attempt,
        recent_interactions=[],
        language_code="ar",
    )
    require(strong["level"] == 0, "strong evidence should preserve challenge/transfer mode")
    require(strong["mode"] == "quiz", "level 0 should use a challenge/quiz mode")

    weak_pre = {
        "score": 20,
        "correct_count": 2,
        "total_count": 10,
        "per_concept_json": '{"Measurement":{"correct":1,"total":5}}',
    }
    weak = adaptive.recommend_support(
        lesson=lesson,
        pre_attempt=weak_pre,
        learner_attempt=None,
        recent_interactions=[{"id": i} for i in range(5)],
        language_code="en",
    )
    require(weak["level"] == 3, "persistent difficulty should increase support to level 3")
    require(weak["mode"] == "simplify", "level 3 should use a micro-explanation mode")

    unknown = adaptive.recommend_support(
        lesson=lesson,
        pre_attempt=None,
        learner_attempt=None,
        recent_interactions=[],
        language_code="fr",
    )
    require(unknown["level"] == 1, "unknown evidence should default to a low-directness guiding question")
    require(unknown["confidence"] < 0.5, "unknown evidence must not claim high confidence")

    contract = adaptive.prompt_contract(weak)
    require("not a claim of learner mastery" in contract, "mastery guardrail missing")
    require("one next instructional move at a time" in contract, "single-next-move guardrail missing")
    require("Do not reveal a complete solution" in contract, "answer-dumping guardrail missing")

    offline = feedback_runtime.local_fallback(
        "support", "Measurement", "محاولة متعلم صالحة", "Arabic", {"adaptive_support_level": 3}
    )
    require("شرح مصغّر" in offline, "offline fallback did not preserve adaptive support level")
    require("محاولتك" in offline, "offline adaptive support must return responsibility to the learner")


def validate_static_integration() -> None:
    db = read("db.py")
    main = read("main_app.py")
    teacher = read("teacher_studio.py")
    feedback = read("feedback_engine.py")
    blocks = read("lesson_block_generation_engine.py")
    css = read(".streamlit/v6_theme.css")
    secrets = read(".streamlit/secrets_example.toml")

    require(any(v in db for v in ('APP_VERSION = "v6.20.0-published-course-runtime"', 'APP_VERSION = "v6.19.1-learner-evidence-misconception-tracing"', 'APP_VERSION = "v6.19.0-pedagogical-quality-adaptive-coach"')), "V6.19.0+ app version missing")
    for column in (
        "adaptive_support_level",
        "adaptive_support_mode",
        "adaptive_support_confidence",
        "adaptive_support_reason",
    ):
        require(column in db, f"adaptive DB field missing: {column}")
    require("adaptive_support_analytics_df" in db, "adaptive research aggregation missing")
    require("student_lesson_ai_interactions_df" in db, "lesson-level support history query missing")

    for token in (
        "import adaptive_support_engine",
        "ENABLE_ADAPTIVE_AI_COACH",
        "adaptive_support_engine.recommend_support",
        "adaptive_support_engine.prompt_contract",
        "adaptive_support_decision",
        "v619_adaptive_coach",
    ):
        require(token in main, f"student adaptive integration missing: {token}")

    for token in (
        "import pedagogical_quality_gate",
        "ENABLE_PEDAGOGICAL_QUALITY_GATE",
        "pedagogical_quality_gate.evaluate_lesson",
        "pedagogical_gate",
    ):
        require(token in blocks, f"lesson quality integration missing: {token}")

    for token in (
        "pedagogical_quality",
        "quality_dimensions",
        "v619-quality-gate",
        "gate.get(\"can_approve\"",
    ):
        require(token in teacher, f"teacher quality UI integration missing: {token}")

    require("adaptive_support_contract" in feedback, "feedback prompt does not receive adaptive support contract")
    require("_adaptive_local_support" in feedback and "_fallback_notice" in feedback, "adaptive offline fallback/localization missing")
    require("follow its support level and directness" in feedback, "adaptive contract priority rule missing")
    require(".v619-quality-gate" in css, "quality gate CSS missing")
    require(".v619-adaptive-support-card" in css, "adaptive coach CSS missing")
    require('ENABLE_PEDAGOGICAL_QUALITY_GATE = "true"' in secrets, "quality feature flag example missing")
    require('ENABLE_ADAPTIVE_AI_COACH = "true"' in secrets, "adaptive coach feature flag example missing")


def main() -> None:
    validate_quality_gate_good_lesson()
    validate_quality_gate_blockers_and_advisories()
    validate_adaptive_support_policy()
    validate_static_integration()
    print("V6.19.0 pedagogical quality + adaptive AI coach validation passed.")


if __name__ == "__main__":
    main()
