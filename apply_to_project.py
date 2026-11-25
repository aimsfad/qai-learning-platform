"""Safe cumulative overlay for the provided 3alimnIA project release.

Verify all signatures before changes; back up existing code, keep secrets and
user data untouched, and refuse modified/unrecognised baselines.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, os, shutil, sys

HERE=Path(__file__).resolve().parent
sha=lambda data:hashlib.sha256(data).hexdigest()


def run():
    parser=argparse.ArgumentParser(description="Install Online Hybrid RAG V0.2")
    parser.add_argument('--target',required=True,help='Path to the original qai_platform_ folder')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    target=Path(args.target).expanduser().resolve()
    if not (target/'app.py').is_file() or not (target/'model_router.py').is_file():
        raise SystemExit('Invalid target: expected app.py and model_router.py')
    manifest=json.loads((HERE/'manifest.json').read_text(encoding='utf-8'))
    changes=[]
    conflicts=[]
    for rel,meta in manifest['files'].items():
        relpath=Path(rel)
        if relpath.is_absolute() or '..' in relpath.parts or rel.startswith(('.streamlit/','data/','assets/','.git/')):
            raise SystemExit('Unsafe patch entry: '+rel)
        src=HERE/'patch_files'/relpath
        dst=target/relpath
        if not src.is_file() or sha(src.read_bytes()) != meta['patched_sha256']:
            raise SystemExit('Damaged package: '+rel)
        if dst.exists() and not dst.is_file():
            conflicts.append(rel)
            continue
        if dst.exists():
            actual=sha(dst.read_bytes())
            if actual == meta['patched_sha256']:
                continue
            allowed={meta.get('original_sha256'),meta.get('v01_sha256')}-{None}
            if actual not in allowed:
                conflicts.append(rel)
                continue
        changes.append((relpath,src,dst))
    if conflicts:
        print('Conflicts: working files differ from the supplied release. Nothing changed.')
        for name in conflicts:print(' -',name)
        raise SystemExit(2)
    if args.dry_run:
        print(f'Validation passed. Pending code files: {len(changes)}. No files written.')
        return
    if not changes:
        print('All V0.2 patch files already installed.')
        return
    backup=target/'.3alimnia_patch_backups'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backed=[];created=[]
    try:
        for rel,src,dst in changes:
            if dst.exists():
                saved=backup/rel
                saved.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(dst,saved)
                backed.append((dst,saved))
            else:
                created.append(dst)
        for rel,src,dst in changes:
            dst.parent.mkdir(parents=True,exist_ok=True)
            staged=dst.with_name(dst.name+'.v02_install_tmp')
            shutil.copyfile(src,staged)
            os.replace(staged,dst)
    except Exception:
        for dst,saved in backed:
            if saved.exists():shutil.copy2(saved,dst)
        for dst in created:
            if dst.is_file():dst.unlink()
        raise
    print(f'Online Hybrid RAG V0.2 installed: {len(changes)} files.')
    print('Code backup:',backup)
    print('Run: python -m unittest tests.test_hybrid_rag_v01 tests.test_online_hybrid_rag_v02')
    print('Read: docs/3ALIMNIA_ONLINE_HYBRID_RAG_V02_AR.md')

if __name__=='__main__':run()
