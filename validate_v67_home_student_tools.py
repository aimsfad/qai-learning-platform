from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    ui = (ROOT / "ui_v6.py").read_text(encoding="utf-8")
    db = (ROOT / "db.py").read_text(encoding="utf-8")
    css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
    hero = ROOT / "assets" / "branding" / "v67_home_brand_hero.png"

    for path in (ROOT / "app.py", ROOT / "ui_v6.py", ROOT / "db.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    require(hero.exists() and hero.stat().st_size > 500_000, "Prominent homepage hero asset is missing or unexpectedly small.")
    require('hero_asset = branding.ASSET_DIR / "v67_home_brand_hero.png"' in ui, "Homepage does not reference the V6.7 hero asset.")
    require("st.image(" in ui and "v67-home-brand-marker" in ui, "Homepage hero is not rendered through Streamlit media.")
    require("def _render_student_tool_dock()" in app, "Persistent learner tool dock is missing.")
    for page in ("Student Home", "Learning Module", "AI Tutor Lab", "Adaptive Plan", "Pre-test", "Post-test", "Satisfaction Survey", "Research Notice"):
        require(page in app, f"Learner tool destination missing: {page}")
    require("router.queue(router.route_key(\"student\", page))" in app, "Learner dock does not use the native router queue.")
    require("_render_student_tool_dock()" in app.split("def main()", 1)[1], "Learner dock is not mounted in the app shell.")
    require("v67-home-brand-marker" in css, "Hero styling is missing.")
    require("st-key-v67_student_tool_dock" in css, "Learner dock styling is missing.")
    require(any(v in db for v in ('APP_VERSION = "v6.19.1-learner-evidence-misconception-tracing"', 'APP_VERSION = "v6.19.0-pedagogical-quality-adaptive-coach"', 'APP_VERSION = "v6.18.9-lesson-identity-content-hygiene"', 'APP_VERSION = "v6.18.8-teacher-workspace-screenshot-polish"', 'APP_VERSION = "v6.18.7-frictionless-ui-contract"', 'APP_VERSION = "v6.18.6-unified-premium-platform-design"', 'APP_VERSION = "v6.7-home-hero-student-tools"')), "Application version was not updated.")

    print("V6.7 home hero and student tools validation passed.")


if __name__ == "__main__":
    main()
