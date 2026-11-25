"""Security and hygiene gate for 3alimnIA V7.0 Enterprise releases."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # 1. No live secret files in workspace
    forbidden_files = [
        ROOT / ".streamlit" / "secrets.toml",
        ROOT / ".env",
        ROOT / ".env.local",
        ROOT / "treamlitsecrets.toml",
    ]
    for path in forbidden_files:
        require(not path.exists(), f"Forbidden secret/stray file present: {path.name}")

    # 2. Attempt-first pedagogical gate must not be bypassed in production
    attempt_gate_src = (ROOT / "attempt_gate.py").read_text(encoding="utf-8")
    require(
        "DEMO_BYPASS_ATTEMPT_GATE = False" in attempt_gate_src,
        "DEMO_BYPASS_ATTEMPT_GATE must be False for release builds.",
    )

    # 3. Password hashing strength check
    security_src = (ROOT / "security.py").read_text(encoding="utf-8")
    require('ALGORITHM = "pbkdf2_sha256"' in security_src, "Expected pbkdf2_sha256 in security.py")
    match = re.search(r"ITERATIONS\s*=\s*([0-9_]+)", security_src)
    require(bool(match) and int(match.group(1).replace("_", "")) >= 260_000, "PBKDF2 iterations < 260,000")
    require("hmac.compare_digest" in security_src, "Constant-time comparison missing in security.py")

    # 4. db.py must not hard-require Streamlit at import time
    db_src = (ROOT / "db.py").read_text(encoding="utf-8")
    require("try:\n    import streamlit as st" in db_src, "db.py must guard streamlit import for headless workers")

    # 5. Single PostgreSQL driver in requirements.txt
    req_src = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    require("psycopg2-binary" not in req_src, "Duplicate psycopg2-binary still in requirements.txt")
    require("psycopg[binary]" in req_src, "psycopg[binary] missing from requirements.txt")

    # 6. Single unified Liquid Glass CSS stylesheet
    css_files = sorted(p.name for p in (ROOT / ".streamlit").glob("*.css"))
    require(css_files == ["app.css"], f"Expected only app.css in .streamlit/, found: {css_files}")

    # 7. Safe HTML escaping layer present
    require((ROOT / "safe_html.py").exists(), "safe_html.py XSS protection layer is missing")

    # 8. Sanitized release packager excludes secrets and patch backups
    pkg_src = (ROOT / "package_release.py").read_text(encoding="utf-8")
    require(".streamlit/secrets.toml" in pkg_src and ".3alimnia_patch_backups" in pkg_src, "package_release.py missing exclusions")

    print("PASS validate_release_security.py — All V7.0 security & hygiene checks passed.")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print(f"FAIL validate_release_security.py: {exc}", file=sys.stderr)
        raise SystemExit(1)
