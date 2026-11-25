from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def exported_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


def main() -> None:
    for path in ROOT.rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    exports = exported_names(ROOT / "branding.py")
    missing: list[str] = []
    for path in ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "branding"
                and node.attr not in exports
            ):
                missing.append(f"{path.relative_to(ROOT)}:{node.lineno} -> branding.{node.attr}")

    if missing:
        raise AssertionError("Undefined branding symbols:\n" + "\n".join(missing))

    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'copy.get(role) or getattr(branding, "BRAND_NAME_LATIN", branding.BRAND_NAME)' in app_text
    assert "BRAND_NAME_LATIN = BRAND_NAME" in (ROOT / "branding.py").read_text(encoding="utf-8")
    print("V5.0.1 branding hotfix validation passed.")


if __name__ == "__main__":
    main()
