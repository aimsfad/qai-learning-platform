#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path
import security

root = Path(__file__).resolve().parent

assert hasattr(security, "password_policy_error")
assert hasattr(security, "password_is_strong")
assert security.password_policy_error("short1") is not None
assert security.password_policy_error("abcdefgh") is not None
assert security.password_policy_error("12345678") is not None
assert security.password_policy_error("StrongPass8") is None
assert security.password_is_strong("StrongPass8")
encoded = security.hash_password("StrongPass8")
assert security.verify_password("StrongPass8", encoded)
assert not security.verify_password("wrong", encoded)

db_text = (root / "db.py").read_text(encoding="utf-8")
assert "password_policy_error" in db_text
ast.parse((root / "security.py").read_text(encoding="utf-8"), filename="security.py")
ast.parse(db_text, filename="db.py")

print("V6.20.20.1 security hotfix validation PASS")
