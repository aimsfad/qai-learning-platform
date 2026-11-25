from pathlib import Path
import ast
import symtable
import builtins

ROOT = Path(__file__).resolve().parent
teacher_path = ROOT / "teacher_studio.py"
teacher = teacher_path.read_text(encoding="utf-8")

checks = {
    "branding imported": "import branding" in teacher,
    "login logo resolves branding": "getattr(branding, \"OFFICIAL_LOGO_PATH\"" in teacher,
    "student preview function restored": "def render_project_student_preview(" in teacher,
    "publication preview call has implementation": "render_project_student_preview(project, public_view=False)" in teacher,
    "public catalog preview call has implementation": "render_project_student_preview(project, public_view=True)" in teacher,
    "invalid stretch alignment absent": 'vertical_alignment="stretch"' not in teacher,
}

for label, ok in checks.items():
    if not ok:
        raise AssertionError(label)

ast.parse(teacher)

# Detect unresolved global references that would raise NameError at runtime.
table = symtable.symtable(teacher, str(teacher_path), "exec")
available = set(dir(builtins))
for name in table.get_identifiers():
    symbol = table.lookup(name)
    if symbol.is_imported() or symbol.is_assigned() or symbol.is_namespace() or symbol.is_parameter():
        available.add(name)

unresolved = set()
def walk(scope):
    for name in scope.get_identifiers():
        symbol = scope.lookup(name)
        if symbol.is_referenced() and symbol.is_global() and name not in available:
            unresolved.add(name)
    for child in scope.get_children():
        walk(child)
walk(table)

if unresolved:
    raise AssertionError(f"Unresolved global names: {sorted(unresolved)}")

print("V6.16.3.1 frontend runtime hotfix validation passed.")
