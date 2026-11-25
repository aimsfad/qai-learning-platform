"""Behavioral validation for V6.11.1 prompt budgeting and Arabic output normalization."""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
import types
from pathlib import Path

_tmp = tempfile.NamedTemporaryFile(prefix="qai_v6111_", suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

fake_st = types.ModuleType("streamlit")
fake_st.secrets = {
    "CONTENT_LLM_PROVIDER": "groq",
    "GROQ_API_KEY": "test-key",
    "CONTENT_GROQ_MODEL": "openai/gpt-oss-120b",
    "ENABLE_MODEL_FALLBACK": "true",
    "ENABLE_PROVIDER_PROMPT_BUDGETING": "true",
    "CONTENT_GROQ_TOTAL_TOKEN_BUDGET": "7000",
    "CONTENT_GROQ_MAX_OUTPUT_TOKENS": "2600",
    "CONTENT_GROQ_STRICT_INPUT_TOKENS": "2200",
    "CONTENT_GROQ_STRICT_OUTPUT_TOKENS": "1700",
}
fake_st.cache_resource = lambda *args, **kwargs: (lambda fn: fn)
sys.modules["streamlit"] = fake_st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

engine = importlib.import_module("content_generation_engine")
builder = importlib.import_module("educational_builder")
model_router = importlib.import_module("model_router")


def long_project() -> dict:
    return {
        "project_name": "تعلم بايثون",
        "domain": "البرمجة",
        "program_name": "أساسيات البرمجة",
        "unit_title": "تعلم بايثون",
        "target_concept": "تعليم أساسيات لغة بايثون للمبتدئين" * 80,
        "target_learners": "متعلمين مبتدئين في المرحلة الثانوية" * 30,
        "learner_level": "Beginner",
        "prerequisites": "الاستخدام الأساسي للحاسوب" * 80,
        "target_languages": ["Arabic", "French", "English"],
        "primary_language": "Arabic",
        "primary_language_code": "ar",
        "expected_duration": "ستة أسابيع",
        "technical_environment": "Python, Streamlit, browser",
        "platform_components": ["Lessons", "AI Coach", "Assessment"],
        "source_material": ("مرجع تعليمي موثوق حول بايثون. " * 4000),
        "teaching_preferences": "المحاولة أولاً ثم التلميحات التدريجية" * 120,
        "assessment_preferences": "اختبارات قصيرة ومشروع تطبيقي" * 120,
        "additional_notes": "الحفاظ على لغة عربية واضحة" * 80,
        "requested_outputs": ["Interactive lesson", "Assessment bank"],
    }


def main() -> None:
    prompt = builder.compile_project_prompt(long_project(), 1, prior_context="")
    assert "# Phase 1" in prompt and "# Phase 2" not in prompt

    info = engine.prompt_budget_info(prompt, builder.PHASE_MAX_TOKENS[1])
    assert info["provider"] == "groq"
    assert info["compacted"] is True
    assert info["estimated_runtime_tokens"] < info["estimated_original_tokens"]
    assert info["estimated_runtime_tokens"] + info["max_output_tokens"] < 7000

    selection = model_router.generation_candidates("content")[0]
    system = engine.content_system_prompt("Arabic")
    plan = engine._provider_prompt_plan(selection, prompt, system, 3600)
    assert plan.compacted
    assert "<teacher_project_brief>" in plan.prompt
    assert "# Phase 1" in plan.prompt
    assert "# Response contract" in plan.prompt
    assert plan.estimated_runtime_tokens <= 4200

    raw = """# المرحلة الأولى: تدقيق الأدلة والمفاهيم (Evidence and Concept Audit)

## أ. التعريف العلمي الموجز (Scientific Definition)

شرح عربي منظم.

## Generation checks

- يحتاج إلى موافقة الأستاذ.
"""
    normalized = builder.normalize_phase_output(raw, 1, "ar")
    assert normalized.startswith("# المرحلة 1: تدقيق الأدلة والمفهوم")
    assert "## أ. التعريف العلمي الموجز (Scientific Definition)" not in normalized
    assert "**المصطلح الإنجليزي:** `Scientific Definition`" in normalized
    assert "## فحوص التوليد" in normalized

    # Simulate a successful Groq call and verify that the runtime prompt—not the
    # oversized downloadable prompt—is sent to the provider.
    captured = {}
    original_candidates = model_router.generation_candidates
    original_call = engine._call_selection
    model_router.generation_candidates = lambda task="content": [selection]

    def fake_call(sel, runtime_prompt, system_prompt, max_tokens, **kwargs):
        captured["prompt"] = runtime_prompt
        captured["max_tokens"] = max_tokens
        return ("# ناتج\n\n" + ("- محتوى تعليمي منظم.\n" * 120), sel.provider, sel.model)

    engine._call_selection = fake_call
    try:
        result = engine.generate_content(prompt, "Arabic", max_tokens=3600, phase_number=1)
    finally:
        engine._call_selection = original_call
        model_router.generation_candidates = original_candidates

    assert result.status == "completed"
    assert engine.estimate_tokens(captured["prompt"]) < engine.estimate_tokens(prompt)
    assert captured["max_tokens"] <= 2600
    assert "Runtime prompt compacted" in result.diagnostic

    print("V6.11.1 prompt budget and RTL normalization validation passed.")


if __name__ == "__main__":
    try:
        main()
    finally:
        Path(_tmp.name).unlink(missing_ok=True)
