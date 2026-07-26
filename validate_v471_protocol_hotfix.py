from __future__ import annotations

import ast
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

py_compile.compile(str(ROOT / "main_app.py"), doraise=True)
py_compile.compile(str(ROOT / "content.py"), doraise=True)

import content  # noqa: E402

assert len(content.PRE_TEST) == 18, len(content.PRE_TEST)
assert len(content.POST_TEST) == 18, len(content.POST_TEST)
assert len(content.LESSONS) == 6, len(content.LESSONS)

content_tree = ast.parse((ROOT / "content.py").read_text(encoding="utf-8"))
defined: set[str] = set()
for node in content_tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                defined.add(target.id)
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        defined.add(node.target.id)
    elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        defined.add(node.name)

main_tree = ast.parse((ROOT / "main_app.py").read_text(encoding="utf-8"))
missing = []
for node in ast.walk(main_tree):
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "content":
        if node.attr not in defined:
            missing.append((node.attr, node.lineno))
assert not missing, missing

main_text = (ROOT / "main_app.py").read_text(encoding="utf-8")
for expected in [
    "بروتوكول الدراسة",
    "Protocole d’étude",
    "Study Protocol",
    '_content_collection_size("PRE_TEST", "PRE_TEST_QUESTIONS")',
    '_content_collection_size("POST_TEST", "POST_TEST_QUESTIONS")',
]:
    assert expected in main_text, expected

print("V4.7.1 protocol hotfix validation passed.")
