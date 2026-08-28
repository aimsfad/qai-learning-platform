"""Build a sanitized source release for 3alimnIA.

The package intentionally excludes local credentials, runtime databases,
Python caches, VCS history, and editor artifacts. It is safe to share as a
source bundle once the resulting archive passes the built-in inspection.
"""

from __future__ import annotations

import argparse
import fnmatch
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT.parent / "3alimnIA_V6.20.0_Published_Course_Runtime.zip"
ARCHIVE_ROOT = "3alimnIA_V6.20.0"

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "data",
    "dist",
    "build",
}
EXCLUDED_FILES = {
    ".streamlit/secrets.toml",
    ".env",
    ".env.local",
    "-v3-9",
}
EXCLUDED_GLOBS = (
    "*.pyc",
    "*.pyo",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.swp",
    "*.swo",
    "*#Uf022",
    ".DS_Store",
)


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def should_include(path: Path, output: Path) -> bool:
    if path.resolve() == output.resolve():
        return False
    rel = _relative(path)
    if any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts[:-1]):
        return False
    if rel in EXCLUDED_FILES:
        return False
    return not any(fnmatch.fnmatch(path.name, pattern) for pattern in EXCLUDED_GLOBS)


def build_release(output: Path) -> Path:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    files = sorted(path for path in ROOT.rglob("*") if path.is_file() and should_include(path, output))
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, f"{ARCHIVE_ROOT}/{_relative(path)}")

    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        forbidden = [
            name for name in names
            if "/.git/" in name
            or name.endswith("/.streamlit/secrets.toml")
            or "/data/" in name
            or "/__pycache__/" in name
            or name.endswith((".pyc", ".pyo", ".db", ".sqlite", ".sqlite3"))
        ]
        if forbidden:
            output.unlink(missing_ok=True)
            raise RuntimeError(f"Unsafe release content detected: {forbidden[:5]}")
        required = {
            f"{ARCHIVE_ROOT}/app.py",
            f"{ARCHIVE_ROOT}/db.py",
            f"{ARCHIVE_ROOT}/published_course_runtime.py",
            f"{ARCHIVE_ROOT}/.streamlit/secrets_example.toml",
        }
        missing = required.difference(names)
        if missing:
            output.unlink(missing_ok=True)
            raise RuntimeError(f"Release is missing required files: {sorted(missing)}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Build sanitized 3alimnIA source release")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build_release(args.output)
    print(result)


if __name__ == "__main__":
    main()
