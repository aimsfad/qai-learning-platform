#!/usr/bin/env python3
"""Safe learner-account diagnostic. Does not print password hashes or secrets."""
from __future__ import annotations

import argparse
import db


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("identifier", help="Participant code, email, or exact registered full name")
    args = parser.parse_args()
    db.init_db()
    state = db.student_auth_diagnostic(args.identifier)
    print("database_dialect:", db.dialect())
    print("account_found:", bool(state.get("found")))
    if state.get("found"):
        print("account_active:", bool(state.get("is_active")))
        print("password_configured:", bool(state.get("has_password")))
        print("participant_code:", state.get("participant_code") or "")
    else:
        print("next_action: verify that deployment uses the same persistent DATABASE_URL/database as the earlier learner account")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
