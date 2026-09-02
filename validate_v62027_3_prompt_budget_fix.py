#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Lightweight Streamlit stub so this validator can run in a bare Python env.
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
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

# Reproduce the three long prompt families seen in V6.20.27 diagnostics.
base = (
    "Create the automatic diagnostic pre-test for one 3alimnIA teacher-authored course.\n"
    "Return JSON ONLY with exactly six objective questions and a strict schema.\n"
    + ("course-context-evidence " * 1800)
    + "\n</course_context>"
)
repair = (
    "Repair a failed 3alimnIA course pre-test generation. Return JSON ONLY.\n"
    + ("original-request-and-invalid-output " * 900)
    + "\nExactly six items."
)
recovery = (
    "3alimnIA PRE-TEST RECOVERY PASS. Return JSON only.\n"
    + ("specific-blueprint-context " * 1200)
    + '\nReturn exactly: {"schema_version":"3alimnia.course_pretest.v1","course_pretest":[]}'
)

checks = {}
for name, prompt in (("generation", base), ("repair", repair), ("recovery", recovery)):
    compact = mod.compact_prompt_for_budget(prompt, 3800)
    tokens = mod.estimate_tokens(compact)
    checks[f"{name} non-empty"] = bool(compact.strip()) and tokens > 300
    checks[f"{name} bounded"] = tokens <= 3800
    checks[f"{name} keeps head"] = prompt.splitlines()[0] in compact
    checks[f"{name} keeps tail"] = prompt.splitlines()[-1] in compact

source = (ROOT / "content_generation_engine.py").read_text(encoding="utf-8")
checks["unstructured fallback present"] = "def _compact_unstructured_prompt(" in source
checks["empty compact guarded"] = "if not compact:" in source

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + ": " + name)
if failed:
    raise SystemExit("V6.20.27.3 validation failed: " + ", ".join(failed))
print(f"V6.20.27.3 checks: {len(checks)}/{len(checks)} PASS")
