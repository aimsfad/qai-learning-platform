"""Regression checks for V6.20.27.4 structured pre-test output."""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Lightweight Streamlit stub for bare-Python release validation.
st = types.ModuleType("streamlit")
st.secrets = {}
sys.modules.setdefault("streamlit", st)
try:
    import requests  # noqa: F401
except Exception:
    req = types.ModuleType("requests")
    req.Response = object
    sys.modules["requests"] = req

spec = importlib.util.spec_from_file_location("content_generation_engine", ROOT / "content_generation_engine.py")
engine = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)
from course_pretest_contract import (
    REQUIRED_QUESTION_COUNT,
    SCHEMA_VERSION,
    course_pretest_json_schema,
    extract_payload,
    validate_generated_pretest,
)

checks = {}

schema = course_pretest_json_schema()
checks["schema top-level object"] = schema.get("type") == "object"
checks["schema exact six"] = (
    schema["properties"]["course_pretest"].get("minItems") == REQUIRED_QUESTION_COUNT
    and schema["properties"]["course_pretest"].get("maxItems") == REQUIRED_QUESTION_COUNT
)
question_schema = schema["properties"]["course_pretest"]["items"]
checks["schema four options"] = (
    question_schema["properties"]["options"].get("minItems") == 4
    and question_schema["properties"]["options"].get("maxItems") == 4
)
checks["schema strict objects"] = (
    schema.get("additionalProperties") is False
    and question_schema.get("additionalProperties") is False
    and set(question_schema.get("required") or []) == set(question_schema.get("properties") or {})
)

sample = {
    "schema_version": SCHEMA_VERSION,
    "course_pretest": [
        {
            "id": f"Q{i}",
            "question_type": ["prerequisite", "prerequisite", "core_concept", "misconception", "application", "transfer"][i-1],
            "concept": ["variables", "conditions", "loops", "equality", "lists", "functions"][i-1],
            "question": f"Diagnostic question {i} about a specific Python concept?",
            "options": [f"option {i}A", f"option {i}B", f"option {i}C", f"option {i}D"],
            "correct_index": i % 4,
            "explanation": f"Explanation for diagnostic question {i}.",
            "difficulty": "medium",
            "cognitive_level": "apply" if i >= 4 else "understand",
        }
        for i in range(1, 7)
    ],
}
rows = extract_payload(json.dumps(sample))
normalized, quality = validate_generated_pretest(rows, blocked_titles=["Python basics"])
checks["strict-shaped sample parses"] = len(rows) == 6
checks["strict-shaped sample passes quality"] = quality.get("ready") is True and len(normalized) == 6

captured = {}
class FakeResponse:
    status_code = 200
    text = ""
    headers = {}
    def json(self):
        return {"choices": [{"message": {"content": json.dumps(sample)}}]}

def fake_post(url, *, headers, payload, provider):
    captured.clear()
    captured.update(payload)
    return FakeResponse()

original_post = engine._post_json
engine._post_json = fake_post
try:
    text, provider, model = engine._call_openai_compatible(
        "Return the diagnostic.",
        "System",
        provider="groq",
        model="openai/gpt-oss-120b",
        max_tokens=2600,
        api_key="test",
        base_url="https://example.invalid",
        structured_schema=schema,
        structured_schema_name="course_pretest",
    )
finally:
    engine._post_json = original_post

rf = captured.get("response_format") or {}
js = rf.get("json_schema") or {}
checks["groq strict json schema enabled"] = rf.get("type") == "json_schema" and js.get("strict") is True
checks["groq schema attached"] = js.get("schema") == schema and js.get("name") == "course_pretest"
checks["groq structured completion budget"] = (
    captured.get("max_completion_tokens") == 2600
    and "max_tokens" not in captured
    and captured.get("reasoning_effort") == "low"
)
checks["groq structured response preserved"] = extract_payload(text) != [] and provider == "groq" and model == "openai/gpt-oss-120b"

source = (ROOT / "course_pretest_engine.py").read_text(encoding="utf-8")
checks["all three pretest calls request schema"] = source.count("structured_schema=response_schema") == 3

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + ": " + name)
if failed:
    raise SystemExit("V6.20.27.4 failed: " + ", ".join(failed))
print(f"V6.20.27.4 checks: {len(checks)}/{len(checks)} PASS")
