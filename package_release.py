"""Build a sanitized enterprise source release for 3alimnIA V7.0.

Excludes local credentials, runtime databases, caches, VCS history,
patch backups, and accidental terminal artifacts, and enforces a strict
post-build security audit before succeeding.
"""

from __future__ import annotations

import argparse
import fnmatch
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT.parent / "3alimnIA_V7_0_LiquidGlass_Enterprise.zip"
ARCHIVE_ROOT = "3alimnIA_V7_0_Enterprise"

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".3alimnia_patch_backups",
    "patch_files",
    "payload",
    "data",
    "dist",
    "build",
    ".rag_data",
}
EXCLUDED_FILES = {
    ".streamlit/secrets.toml",
    ".env",
    ".env.local",
    ".env.production",
    "treamlitsecrets.toml",
    "-v3-9",
    "tatus",
    "tatus -sb",
    "py",
}
EXCLUDED_GLOBS = (
    "*.pyc",
    "*.pyo",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.swp",
    "*.swo",
    "*.swn",
    "*#Uf022",
    ".DS_Store",
    "APPLY_*.cmd",
)
FORBIDDEN_ARCHIVE_PATTERNS = (
    "*secrets.toml",
    "*.env",
    "*.env.*",
    "*/.git/*",
    "*/__pycache__/*",
    "*.db",
    "*.sqlite*",
)


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def should_include(path: Path, output: Path) -> bool:
    if path.resolve() == output.resolve():
        return False
    rel = _relative(path)
    parts = path.relative_to(ROOT).parts
    if any(part in EXCLUDED_DIRS for part in parts[:-1]):
        return False
    if rel in EXCLUDED_FILES or path.name in EXCLUDED_FILES:
        return False
    return not any(fnmatch.fnmatch(path.name, pattern) for pattern in EXCLUDED_GLOBS)


def build_release(output: Path) -> Path:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    files = sorted(
        path for path in ROOT.rglob("*") if path.is_file() and should_include(path, output)
    )
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, f"{ARCHIVE_ROOT}/{_relative(path)}")

    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        forbidden = [
            name
            for name in names
            if any(fnmatch.fnmatch(name, pat) for pat in FORBIDDEN_ARCHIVE_PATTERNS)
            and not name.endswith("secrets_example.toml")
        ]
        if forbidden:
            output.unlink(missing_ok=True)
            raise RuntimeError(f"Release security check failed; forbidden files found: {forbidden[:5]}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Package a sanitized 3alimnIA V7.0 release ZIP.")
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    out = build_release(args.output)
    print(f"Sanitized release created: {out} ({out.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
