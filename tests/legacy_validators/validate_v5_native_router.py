from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


app_text = (ROOT / "app.py").read_text(encoding="utf-8")
main_text = (ROOT / "main_app.py").read_text(encoding="utf-8")
router_text = (ROOT / "router.py").read_text(encoding="utf-8")
css_text = (ROOT / ".streamlit" / "v4_theme.css").read_text(encoding="utf-8")
requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")

# Syntax validation.
for path in ROOT.glob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

# Router contract.
require('st.navigation(pages, position="top"' in app_text, "Native top navigation is not configured.")
require("st.Page(" in app_text, "No st.Page routes were declared.")
require("router.process_pending_route()" in app_text, "Queued routes are not processed.")
require("st.switch_page(page)" in router_text, "Router does not use native st.switch_page.")
require("render_global_escape_navigation()" not in app_text, "Legacy escape navigation is still called by app.py.")

# Account controls must use callbacks, not fragile DOM scripts.
for callback in (
    "change_account_callback",
    "switch_workspace_callback",
    "logout_callback",
):
    require(f"def {callback}" in main_text, f"Missing callback: {callback}")
    require(f"on_click=main_app.{callback}" in app_text, f"Toolbar is not wired to {callback}")
require("_v411_open_sidebar" not in app_text, "V5 app.py still depends on DOM sidebar clicking.")

# Internal route helpers must queue native routes.
require('router.navigate(router.route_key("student", page))' in main_text, "Student page helper is not native-routed.")
require('router.navigate(router.route_key("evaluator", page))' in main_text, "Evaluator page helper is not native-routed.")

# Every key evaluator destination must be registered.
for page in (
    "Evaluator Dashboard",
    "Study Protocol",
    "Students",
    "Registration Accounts",
    "Student Details",
    "AI Tutor Logs",
    "AI Response Evaluation",
    "AI Metrics",
    "Exports",
):
    require(page in app_text, f"Evaluator route missing: {page}")

# Every learner destination must be registered.
for page in (
    "Student Home",
    "Adaptive Plan",
    "Learning Module",
    "AI Tutor Lab",
    "Pre-test",
    "Post-test",
    "Satisfaction Survey",
    "Research Notice",
    "Sign in",
    "Create account",
):
    require(page in app_text, f"Student route missing: {page}")

# CSS must restore the header and style active native navigation.
require("Restore the Streamlit header" in css_text, "Header restoration override is missing.")
require('a[aria-current="page"]' in css_text, "Active native page styling is missing.")
require(".v5-toolbar-marker" in css_text, "V5 account toolbar styling is missing.")
require("streamlit>=1.53" in requirements, "Streamlit version is too old for top navigation.")

print("V5 native router validation passed.")
