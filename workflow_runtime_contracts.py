"""Runtime API contracts for the guided teacher production workflow.

V6.18.3 centralizes the callable/constant checks that previously surfaced as
late AttributeError failures after the teacher had already navigated deep into
an editing flow.  The module is intentionally Streamlit-free so it can be used
from validators, workers, and the UI.
"""
from __future__ import annotations

import importlib
from typing import Any, Dict, Iterable, List, Mapping


CONTRACTS: Dict[str, Dict[str, Dict[str, Iterable[str]]]] = {
    "blueprint": {
        "lesson_blueprint_engine": {
            "callables": (
                "blueprint_status",
                "generate_and_persist",
                "prepare_editor_draft",
                "normalize_blueprint",
                "recompute_blueprint_quality",
                "compare_blueprints",
                "add_unit",
                "update_unit",
                "move_unit",
                "delete_unit",
                "add_lesson",
                "update_lesson",
                "move_lesson",
                "delete_lesson",
                "add_outcome",
                "update_outcome",
                "delete_outcome",
                "save_manual_revision",
            ),
            "attributes": (),
        },
        "db": {
            "callables": (
                "teacher_evidence_runs_df",
                "teacher_evidence_bundle",
                "latest_teacher_blueprint",
                "teacher_blueprint_bundle",
                "approve_teacher_blueprint_run",
                "teacher_blueprint_versions_df",
                "teacher_blueprint_audit_df",
            ),
            "attributes": (),
        },
    },
    "lesson_blocks": {
        "lesson_block_generation_engine": {
            "callables": (
                "block_generation_status",
                "block_label",
                "ordered_block_types",
                "lesson_block_state",
                "next_incomplete_block",
                "can_generate_block",
                "generate_and_persist",
                "save_teacher_revision",
                "lesson_completion",
            ),
            "attributes": ("BLOCK_SPECS",),
        },
        "db": {
            "callables": (
                "latest_teacher_blueprint",
                "latest_teacher_lesson_block",
                "latest_lesson_blocks_by_type",
                "approve_teacher_lesson_block",
                "teacher_lesson_block_versions_df",
                "teacher_lesson_block_audit_df",
            ),
            "attributes": (),
        },
    },
}


def _module(name: str):
    return importlib.import_module(str(name))


def check_contract(scope: str) -> Dict[str, Any]:
    """Return a structured readiness report for a workflow scope."""

    spec = CONTRACTS.get(str(scope))
    if not spec:
        return {
            "ok": False,
            "scope": str(scope),
            "missing": [f"unknown contract scope: {scope}"],
            "modules": {},
        }

    missing: List[str] = []
    module_reports: Dict[str, Any] = {}
    for module_name, requirements in spec.items():
        try:
            module = _module(module_name)
        except Exception as exc:  # Import failures must be visible to validators.
            message = f"{module_name}: import failed ({exc.__class__.__name__})"
            missing.append(message)
            module_reports[module_name] = {"ok": False, "missing": [message]}
            continue

        module_missing: List[str] = []
        for name in requirements.get("callables", ()):
            if not callable(getattr(module, str(name), None)):
                module_missing.append(f"{module_name}.{name}()")
        for name in requirements.get("attributes", ()):
            if not hasattr(module, str(name)):
                module_missing.append(f"{module_name}.{name}")

        missing.extend(module_missing)
        module_reports[module_name] = {
            "ok": not module_missing,
            "missing": module_missing,
        }

    return {
        "ok": not missing,
        "scope": str(scope),
        "missing": missing,
        "modules": module_reports,
    }


def assert_contract(scope: str) -> None:
    report = check_contract(scope)
    if not report.get("ok"):
        raise RuntimeError(
            f"Workflow runtime contract '{scope}' is incomplete: "
            + ", ".join(str(item) for item in report.get("missing") or [])
        )


def contract_summary(scopes: Iterable[str] | None = None) -> Mapping[str, Dict[str, Any]]:
    selected = list(scopes or CONTRACTS.keys())
    return {scope: check_contract(scope) for scope in selected}
