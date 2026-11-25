#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASELINE = {
    "db.py": "31b060b669486a72aa2115e790907a1d18e0ad6941ee1b8175ff61131368f814",
    "published_course_runtime.py": "0233aee4b24004abe4c9a53c4d11f81b7fa9fd70bb6fe7fba07962624d9a3d78",
    "teacher_studio.py": "14e076f572966fe38242e1c1949bdacc9af91a5246c6ce1038b2a557c9c1b7a8",
    "validate_current_release.py": "64d7ce327cafd5312d6b4d9536f8f6722114f5f13405aa4d6d68ab0ac31c6c4b",
    "prompts/educational_content_production_master.md": "a60d1cfe2301f9ddce6b030c46e988c579b1b74fad17f2c7dfcccd3e97c57b03",
    "CHANGELOG.md": "994ab48050cfa0a5292d6856a8c8895a83acb61b3fd062e83082c62edf94274a",
}

PAYLOAD_FILES = [
    "db.py",
    "published_course_runtime.py",
    "teacher_studio.py",
    "validate_current_release.py",
    "prompts/educational_content_production_master.md",
    "CHANGELOG.md",
    "course_pretest_contract.py",
    "course_pretest_engine.py",
    "validate_v62027_ai_course_pretest.py",
    "V6_20_27_AI_GENERATED_COURSE_PRETEST.md",
]


def canonical_hash(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def die(message: str) -> None:
    raise SystemExit("ERROR: " + message)


root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
package_root = Path(__file__).resolve().parent
payload = package_root / "payload"

if not (root / "app.py").is_file() or not (root / "db.py").is_file():
    die(f"{root} does not look like the 3alimnIA repository root.")

# Idempotent second run.
existing_db = (root / "db.py").read_text(encoding="utf-8")
if (
    'COURSE_PRETEST_ENGINE_VERSION = "v6.20.27-ai-generated-course-pretest"' in existing_db
    and (root / "course_pretest_engine.py").is_file()
    and (root / "validate_v62027_ai_course_pretest.py").is_file()
):
    print("V6.20.27 already appears to be installed. Running validator only.")
    result = subprocess.run([sys.executable, str(root / "validate_v62027_ai_course_pretest.py")], cwd=root)
    raise SystemExit(result.returncode)

mismatches = []
for rel, expected in BASELINE.items():
    path = root / rel
    if not path.is_file():
        mismatches.append(f"{rel}: missing")
        continue
    actual = canonical_hash(path)
    if actual != expected:
        mismatches.append(f"{rel}: expected {expected[:12]}..., found {actual[:12]}...")

if mismatches:
    print("The installer did not write any runtime changes because the tracked baseline differs from V6.20.26.")
    print("Mismatches:")
    for item in mismatches:
        print(" - " + item)
    print("Run: git status")
    print("Do not force-copy the payload over unknown tracked changes.")
    raise SystemExit(2)

for rel in PAYLOAD_FILES:
    if not (payload / rel).is_file():
        die(f"payload file missing: {rel}")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = root.parent / f"{root.name}_backup_before_v62027_{stamp}"
for rel in PAYLOAD_FILES:
    src = root / rel
    if src.is_file():
        dst = backup / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

for rel in PAYLOAD_FILES:
    src = payload / rel
    dst = root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

print("Applied V6.20.27 AI-generated course pre-test engine.")
print(f"Backup: {backup}")

# Dependency-light syntax/contract validation only; no pandas/Streamlit install is required.
compile_targets = [
    "db.py",
    "published_course_runtime.py",
    "teacher_studio.py",
    "course_pretest_contract.py",
    "course_pretest_engine.py",
    "validate_current_release.py",
    "validate_v62027_ai_course_pretest.py",
]
for rel in compile_targets:
    subprocess.run([sys.executable, "-m", "py_compile", str(root / rel)], cwd=root, check=True)
subprocess.run([sys.executable, str(root / "validate_v62027_ai_course_pretest.py")], cwd=root, check=True)

for legacy in ("validate_v62026_pretest_content_grid.py", "validate_v62025_1_current_main.py"):
    if (root / legacy).is_file():
        subprocess.run([sys.executable, str(root / legacy)], cwd=root, check=True)

print("V6.20.27 applied and validated.")
print("Next:")
print("  git status")
print("  git diff --stat")
