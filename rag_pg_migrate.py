"""Explicit schema migration for a separate Neon staging database only.

Usage:
  python rag_pg_migrate.py --dry-run
  python rag_pg_migrate.py --apply --confirm-staging

Never deploy with production DB credentials. It reads RAG_DATABASE_URL only.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from rag_postgres import _required_staging_dsn

SCRIPT = Path(__file__).parent / "migrations" / "001_neon_rag.sql"


def migration_statements() -> list[str]:
    # This particular migration contains only SQL statements, no PL/pgSQL,
    # semicolons inside string literals, or dollar-quoted functions.
    lines = [line for line in SCRIPT.read_text(encoding="utf-8").splitlines()
             if not line.lstrip().startswith("--")]
    return [statement.strip() for statement in "\n".join(lines).split(";") if statement.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="3alimnIA Neon RAG staging schema")
    exclusive = parser.add_mutually_exclusive_group(required=True)
    exclusive.add_argument("--dry-run", action="store_true")
    exclusive.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-staging", action="store_true")
    args = parser.parse_args()
    statements = migration_statements()
    print(f"RAG V0.3 schema: {len(statements)} SQL statements; path={SCRIPT.name}")
    if args.dry_run:
        print("DRY RUN ONLY. No database connection and no changes.")
        return
    if not args.confirm_staging:
        parser.error("--apply requires --confirm-staging after checking the Neon staging branch")
    dsn = _required_staging_dsn()
    try:
        import psycopg
        with psycopg.connect(dsn, sslmode="require", connect_timeout=10) as connection:
            with connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)
    except Exception:
        raise SystemExit("Migration failed and was rolled back. Check separate Neon staging database settings.") from None
    print("Schema migration committed on the configured staging database.")


if __name__ == "__main__":
    main()
