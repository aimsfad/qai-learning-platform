from __future__ import annotations
from pathlib import Path
import hashlib, json, shutil, sys
from datetime import datetime

ROOT=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
PKG=Path(__file__).resolve().parent
MANIFEST=json.loads((PKG/'manifest.json').read_text(encoding='utf-8'))

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

errors=[]
for rel,expected in MANIFEST['baseline'].items():
    p=ROOT/rel
    if not p.is_file():
        errors.append(f"{rel}: missing")
    else:
        actual=sha(p)
        if actual!=expected:
            errors.append(f"{rel}: expected {expected[:12]}..., found {actual[:12]}...")
if errors:
    print("The installer did not write any runtime changes because the tracked baseline differs from V6.20.27.1.")
    print("Mismatches:")
    for e in errors: print(" - "+e)
    print("Run: git status")
    print("Do not force-copy the payload over unknown tracked changes.")
    raise SystemExit(2)

stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
backup=ROOT.parent/f"{ROOT.name}_backup_before_v62027_2_{stamp}"
backup.mkdir(parents=True,exist_ok=True)
for rel in MANIFEST['baseline']:
    src=ROOT/rel
    if src.is_file():
        dest=backup/rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dest)

for rel,expected in MANIFEST['payload'].items():
    src=PKG/'payload'/rel
    if sha(src)!=expected:
        raise SystemExit(f"Payload integrity failure: {rel}")
    dest=ROOT/rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dest)
print("Applied V6.20.27.2 AI pre-test recovery patch.")
print(f"Backup: {backup}")
