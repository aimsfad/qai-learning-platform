from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "db.py"
ENGINE_PATH = ROOT / "lesson_blueprint_engine.py"


def function_keywords(tree: ast.Module, function_name: str) -> set[str]:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            args = node.args
            return {
                *(arg.arg for arg in args.args),
                *(arg.arg for arg in args.kwonlyargs),
            }
    raise AssertionError(f"Function not found: {function_name}")


def dotted_name(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def main() -> None:
    db_source = DB_PATH.read_text(encoding="utf-8")
    engine_source = ENGINE_PATH.read_text(encoding="utf-8")
    db_tree = ast.parse(db_source)
    engine_tree = ast.parse(engine_source)

    save_args = function_keywords(db_tree, "save_teacher_blueprint_bundle")
    audit_args = function_keywords(db_tree, "record_teacher_blueprint_audit")

    save_calls = 0
    audit_calls = 0

    for node in ast.walk(engine_tree):
        if not isinstance(node, ast.Call):
            continue
        name = dotted_name(node.func)
        if name == "db.save_teacher_blueprint_bundle":
            save_calls += 1
            supplied = {kw.arg for kw in node.keywords if kw.arg}
            unknown = supplied - save_args
            assert not unknown, f"Unsupported save_teacher_blueprint_bundle keywords: {sorted(unknown)}"
        elif name == "db.record_teacher_blueprint_audit":
            audit_calls += 1
            supplied = {kw.arg for kw in node.keywords if kw.arg}
            unknown = supplied - audit_args
            assert not unknown, f"Unsupported record_teacher_blueprint_audit keywords: {sorted(unknown)}"
        elif name == "db.log_teacher_blueprint_change":
            raise AssertionError("Obsolete db.log_teacher_blueprint_change call remains")

    assert save_calls >= 2, "Expected blueprint generation and manual-revision save calls"
    assert audit_calls >= 3, "Expected generation and revision audit calls"

    for forbidden in (
        "revision_number=",
        "edit_source=",
        "source.get('revision_number')",
        'source.get("revision_number")',
    ):
        assert forbidden not in engine_source, f"Obsolete API name remains: {forbidden}"

    assert "version_number=1" in engine_source
    assert 'revision_type="generated"' in engine_source
    assert 'revision_type="manual"' in engine_source
    assert "source.get('version_number')" in engine_source

    compile(engine_source, str(ENGINE_PATH), "exec")
    print("V6.18.1 blueprint API contract validation passed.")


if __name__ == "__main__":
    main()
