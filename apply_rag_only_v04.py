"""Apply 3alimnIA RAG-only teacher-source flow to V0.3 feature branch.

Usage (Windows CMD, from repository root):
    py path\to\apply_rag_only_v04.py --dry-run
    py path\to\apply_rag_only_v04.py --apply

Never edits the Neon database or pushes/merges any branch.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

BRANCH = "feat/neon-rag-storage-v03"
EXPECTED = {
    "teacher_studio.py": "d29e172a17b9494b2e7eca1193e165d170c45c59",
    "guided_teacher_workflow.py": "40ec7f0f90eedc4691bf355b4a785d706465d9ef",
    "evidence_synthesis_engine.py": "62a4ddf5f5e466afe4b943383556ab9d9891913e",
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True, encoding="utf-8").strip()


def replace_once(text: str, old: str, new: str, path: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Patch mismatch in {path}: expected anchor once, found {count}: {old[:60]}")
    return text.replace(old, new, 1)


def patch_teacher(s: str) -> str:
    p = "teacher_studio.py"
    s = replace_once(s, "import hybrid_rag\n", "import hybrid_rag\nimport rag_course_sources\n", p)
    s = replace_once(s, "    # Inputs must exist even when the settings expander is closed.", '''    if hybrid_rag.enabled():
        st.markdown("#### مصادر RAG المعتمدة — دون بحث خارجي")
        st.caption(
            "استخدم المراجع التي رفعتها واعتمدتها في مكتبة RAG. "
            "يجب السماح باستخدام المقاطع في التوليد السحابي؛ "
            "لا تُعتبر هذه العملية بحثًا عبر الإنترنت."
        )
        rag_query = st.text_input(
            "كلمات مفتاحية لاسترجاع مقاطع المقرر",
            value=str(p.get("target_concept") or p.get("project_name") or "")[:180],
            key=f"teacher_local_rag_query_{project_id}",
        )
        if st.button(
            "إنشاء حزمة مصادر من مراجع RAG",
            disabled=not bool(rag_query.strip()),
            use_container_width=True,
            key=f"teacher_local_rag_import_{project_id}",
        ):
            try:
                rag_course_sources.create_local_rag_dossier(
                    p, owner=_current_teacher_username(), query=rag_query,
                )
                st.session_state.teacher_flash_success = (
                    "حُفظت حزمة RAG. راجع المصادر واعتمدها للانتقال إلى تركيب الأدلة."
                )
            except Exception as exc:
                st.session_state.teacher_flash_error = str(exc)
            st.rerun()

    # Inputs must exist even when the settings expander is closed.''', p)
    s = replace_once(s, '    approved = bool(int(latest.get("approved_by_teacher") or 0))', '''    snapshot_error = rag_course_sources.current_snapshot_error(
        latest, owner=_current_teacher_username(), project_id=int(project_id),
    )
    approved = bool(int(latest.get("approved_by_teacher") or 0)) and not snapshot_error''', p)
    s = replace_once(s, '''    elif canonical_stage and status in {"completed", "needs_review"}:
        st.markdown("<span class='v6172-approval-marker' aria-hidden='true'></span>", unsafe_allow_html=True)''', '''    elif canonical_stage and status in {"completed", "needs_review"}:
        if snapshot_error:
            st.error(snapshot_error)
        st.markdown("<span class='v6172-approval-marker' aria-hidden='true'></span>", unsafe_allow_html=True)''', p)
    s = replace_once(s, '''        if st.button(labels["approve"], type="primary", use_container_width=True, key=f"approve_research_{int(latest.get('id') or 0)}"):''', '''        if st.button(labels["approve"], type="primary", use_container_width=True, disabled=bool(snapshot_error), key=f"approve_research_{int(latest.get('id') or 0)}"):''', p)
    s = replace_once(s, '''    approved_research = db.latest_approved_teacher_research(project_id, research_phase)
    stage_state =''', '''    approved_research = db.latest_approved_teacher_research(project_id, research_phase)
    if approved_research:
        rag_permission_error = rag_course_sources.current_snapshot_error(
            approved_research, owner=_current_teacher_username(), project_id=project_id,
        )
        if rag_permission_error:
            st.warning(rag_permission_error)
            approved_research = None
    stage_state =''', p)
    s = replace_once(s, '''    latest_research = db.latest_approved_teacher_research(project_id, phase_number)
    col1, col2 = st.columns(2)''', '''    latest_research = db.latest_approved_teacher_research(project_id, phase_number)
    if latest_research:
        rag_permission_error = rag_course_sources.current_snapshot_error(
            latest_research, owner=_current_teacher_username(), project_id=project_id,
        )
        if rag_permission_error:
            st.error(rag_permission_error)
            latest_research = None
    col1, col2 = st.columns(2)''', p)
    return s


def patch_workflow(s: str) -> str:
    p = "guided_teacher_workflow.py"
    return replace_once(s, '''    research_runs = research_df.to_dict("records") if hasattr(research_df, "to_dict") else []
    evidence =''', '''    research_runs = research_df.to_dict("records") if hasattr(research_df, "to_dict") else []
    # Revoked/deleted local RAG sources cannot unlock later workflow stages.
    import rag_course_sources
    owner = str(project.get("teacher_username") or "").strip()
    for row in research_runs:
        if str(row.get("provider") or "") == rag_course_sources.LOCAL_RAG_PROVIDER:
            if rag_course_sources.current_snapshot_error(
                row, owner=owner, project_id=project_id,
            ):
                row["approved_by_teacher"] = 0
    evidence =''', p)


def patch_evidence(s: str) -> str:
    p = "evidence_synthesis_engine.py"
    s = replace_once(s, "import web_research_engine\n", "import web_research_engine\nimport rag_course_sources\n", p)
    s = replace_once(s,
        "You are converting a completed web-research dossier into a strict, traceable evidence layer for an educational project.",
        "You are converting a teacher-reviewed source dossier into a strict, traceable evidence layer for an educational project.\nThe source dossier may contain uploaded teacher RAG references instead of web research. Never claim the web was searched if it was not.\nTeacher approval does not independently establish scholarly authority, truth, licensing, or corroboration.", p)
    s = replace_once(s, '''    if not run:
        raise ValueError("Run web research for this phase before synthesizing evidence.")
    result = synthesize_evidence''', '''    if not run:
        raise ValueError("Approve a web research dossier or a teacher RAG source dossier before synthesizing evidence.")
    rag_permission_error = rag_course_sources.current_snapshot_error(
        run, owner=owner, project_id=project_id,
    )
    if rag_permission_error:
        raise ValueError(rag_permission_error)
    result = synthesize_evidence''', p)
    return s


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    script_dir = Path(__file__).resolve().parent
    if not (Path.cwd() / ".git").exists():
        raise SystemExit("Run this command from the root of your qai-learning-platform Git repository.")
    branch = git("branch", "--show-current")
    if branch != BRANCH:
        raise SystemExit(f"STOP: current branch is {branch!r}; expected {BRANCH!r}. Do not modify main.")
    outputs = {}
    for path, sha in EXPECTED.items():
        found = git("rev-parse", f"HEAD:{path}")
        if found != sha:
            raise SystemExit(f"STOP: {path} has changed since the audited V0.3 baseline ({found}). Nothing written.")
        if git("status", "--porcelain", "--", path):
            raise SystemExit(f"STOP: {path} has uncommitted changes. Nothing written.")
        source = Path(path).read_text(encoding="utf-8")
        patched = {"teacher_studio.py":patch_teacher,"guided_teacher_workflow.py":patch_workflow,"evidence_synthesis_engine.py":patch_evidence}[path](source)
        compile(patched, path, "exec")
        outputs[path] = patched
    for file_name in ("rag_course_sources.py", "tests/test_rag_course_sources.py"):
        if Path(file_name).exists():
            raise SystemExit(f"STOP: {file_name} already exists. Nothing written.")
        source = (script_dir / file_name).read_text(encoding="utf-8")
        compile(source, file_name, "exec")
        outputs[file_name] = source
    print("Validated feature branch, source hashes, clean files, patch anchors and Python syntax.")
    print("Files:", ", ".join(outputs))
    if args.dry_run:
        print("Dry run OK. No files changed.")
        return
    backup_dir = Path(".3alimnia_patch_backups") / ("rag_only_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    backup_dir.mkdir(parents=True)
    for path in EXPECTED:
        shutil.copy2(path, backup_dir / path)
    for path, content in outputs.items():
        f = Path(path)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8", newline="\n")
    print(f"Applied patch. Backups of modified files: {backup_dir}")
    print("No secrets, database, GitHub push, merge or production branch were touched.")


if __name__ == "__main__":
    main()
