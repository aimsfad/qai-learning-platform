"""Validation for V6.16.5 UI stability and shared design system."""

from __future__ import annotations

import ast
import builtins
import symtable
from pathlib import Path

import ui_stability

ROOT = Path(__file__).resolve().parent
teacher_path = ROOT / "teacher_studio.py"
ui_path = ROOT / "ui_v6.py"
main_path = ROOT / "main_app.py"
css_path = ROOT / ".streamlit" / "v6_theme.css"

teacher = teacher_path.read_text(encoding="utf-8")
ui = ui_path.read_text(encoding="utf-8")
main = main_path.read_text(encoding="utf-8")
css = css_path.read_text(encoding="utf-8")
stability = (ROOT / "ui_stability.py").read_text(encoding="utf-8")

static_checks = {
    "shared helper module": "def columns(" in stability and "def render_error_card(" in stability,
    "teacher imports helper": "import ui_stability" in teacher,
    "public UI imports helper": "import ui_stability" in ui,
    "evaluator app imports helper": "import ui_stability" in main,
    "teacher critical layouts guarded": "ui_stability.columns([2.25, 1]" in teacher,
    "public navbar layout guarded": "ui_stability.columns(\n            [1.85, 3.55" in ui,
    "friendly teacher errors centralized": "ui_stability.render_error_card" in teacher,
    "phase statuses centralized": "ui_stability.status_semantics" in teacher and "ui_stability.status_badge_html" in teacher,
    "design tokens present": "--qai-primary:" in css and "--qai-space-6:" in css,
    "accessible focus present": ":focus-visible" in css,
    "reduced motion present": "prefers-reduced-motion: reduce" in css,
    "error card CSS present": ".qai-ui-error-card" in css,
    "semantic status CSS present": ".qai-status-badge" in css and ".qai-status-queued" in css,
}
failed = [name for name, ok in static_checks.items() if not ok]
if failed:
    raise AssertionError("Static checks failed: " + ", ".join(failed))

# No unsupported vertical-alignment literals may be passed to layout calls.
allowed = {"top", "center", "bottom"}
invalid_alignments: list[str] = []
for path in ROOT.rglob("*.py"):
    if any(part in {".git", "__pycache__"} for part in path.parts):
        continue
    source = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg != "vertical_alignment" or not isinstance(keyword.value, ast.Constant):
                continue
            value = keyword.value.value
            if isinstance(value, str) and value not in allowed:
                invalid_alignments.append(f"{path.name}:{getattr(node, 'lineno', '?')}:{value}")
if invalid_alignments:
    raise AssertionError(f"Unsupported vertical alignments: {invalid_alignments}")

# Behavioral checks for defensive layout and status normalization.
assert ui_stability.normalize_gap("unexpected") == "small"
assert ui_stability.normalize_gap("large") == "large"
assert ui_stability.normalize_vertical_alignment("stretch") == "top"
assert ui_stability.normalize_vertical_alignment("center") == "center"
assert ui_stability.status_semantics("queued") == ("queued", "queued")
assert ui_stability.status_semantics("completed") == ("approved", "approved")
assert ui_stability.status_label("needs_review", "ar") == "تحتاج مراجعة"
friendly, technical, incident = ui_stability.friendly_error("HTTP 429 quota exceeded", "en")
assert "quota" in friendly.lower() and technical and len(incident) == 10

# Parse all modified Python files.
for path in [ROOT / "ui_stability.py", teacher_path, ui_path, main_path]:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

# Catch unresolved global names in the compact shared module and teacher UI.
def unresolved_globals(path: Path) -> set[str]:
    source = path.read_text(encoding="utf-8")
    table = symtable.symtable(source, str(path), "exec")
    available = set(dir(builtins))
    for name in table.get_identifiers():
        symbol = table.lookup(name)
        if symbol.is_imported() or symbol.is_assigned() or symbol.is_namespace() or symbol.is_parameter():
            available.add(name)
    unresolved: set[str] = set()

    def walk(scope) -> None:
        for name in scope.get_identifiers():
            symbol = scope.lookup(name)
            if symbol.is_referenced() and symbol.is_global() and name not in available:
                unresolved.add(name)
        for child in scope.get_children():
            walk(child)

    walk(table)
    return unresolved

for path in [ROOT / "ui_stability.py", teacher_path]:
    unresolved = unresolved_globals(path)
    if unresolved:
        raise AssertionError(f"Unresolved global names in {path.name}: {sorted(unresolved)}")

print("V6.16.5 UI stability and design-system validation passed.")
