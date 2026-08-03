"""Persistent hybrid production pipeline for 3alimnIA V6.17.

The pipeline supports an RQ/Redis backend for real background execution and an
inline backend for local validation. Jobs are always persisted in the SQL
store so the Streamlit UI can be left and reopened without losing state.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import db
import educational_builder

PHASE_DEPENDENCIES: Dict[int, List[int]] = {
    1: [], 2: [1], 3: [2],
    4: [3], 5: [3], 6: [3], 7: [3], 8: [3], 9: [3],
    10: [4, 5, 6, 7, 8, 9], 11: [10],
}
PARALLEL_PHASES = [4, 5, 6, 7, 8, 9]
TERMINAL_STATUSES = {"generated", "needs_review", "approved", "failed", "canceled"}

@dataclass
class EnqueueResult:
    job_id: int
    queue_job_id: str
    backend: str
    status: str
    phase_number: int
    batch_id: str = ""


def queue_backend() -> str:
    requested = str(os.getenv("PRODUCTION_QUEUE_BACKEND", "auto")).strip().lower()
    if requested == "inline":
        return "inline"
    if requested in {"rq", "auto"} and os.getenv("REDIS_URL"):
        try:
            import redis  # noqa: F401
            import rq  # noqa: F401
            return "rq"
        except Exception:
            if requested == "rq":
                raise RuntimeError("RQ backend requested but redis/rq are unavailable")
    return "inline"


def completed_phases(project_id: int) -> set[int]:
    outputs = db.teacher_project_phase_outputs(int(project_id), prefer_completed=True)
    return {phase for phase, row in outputs.items() if str(row.get("status") or "") == "completed"}


def missing_dependencies(project_id: int, phase_number: int) -> List[int]:
    done = completed_phases(project_id)
    return [phase for phase in PHASE_DEPENDENCIES[int(phase_number)] if phase not in done]


def _safe_error(exc: Exception) -> tuple[str, str]:
    text = str(exc or "").lower()
    if "429" in text or "quota" in text or "rate limit" in text:
        return "provider_quota", "The AI service quota is temporarily unavailable. Retry later."
    if "413" in text or "too large" in text or "token" in text:
        return "request_too_large", "The generation request was too large and needs a smaller context."
    return "generation_failed", "The production task failed. Project data and earlier outputs were preserved."


def run_job(job_id: int) -> Dict[str, Any]:
    job = db.query_one("SELECT * FROM teacher_production_jobs WHERE id=:id", {"id": int(job_id)})
    if not job:
        raise ValueError("Production job not found")
    project = db.get_teacher_project(int(job["project_id"]), str(job["teacher_username"]))
    if not project:
        raise ValueError("Teacher project not found or access denied")
    phase = int(job["phase_number"])
    missing = missing_dependencies(int(project["id"]), phase)
    if missing:
        db.update_teacher_production_job(job_id, status="waiting_for_dependency", progress_percent=0)
        return {"status": "waiting_for_dependency", "missing": missing}

    attempt = int(job.get("attempt_count") or 0) + 1
    db.update_teacher_production_job(job_id, status="running", progress_percent=10, attempt_count=attempt, started=True)
    try:
        result = educational_builder.generate_project_phase(
            project,
            str(job["teacher_username"]),
            phase_number=phase,
            research_mode=str(os.getenv("BACKGROUND_RESEARCH_MODE", "off")),
            max_research_sources=int(os.getenv("BACKGROUND_RESEARCH_MAX_SOURCES", "6")),
            force_research=False,
        )
        final_status = "generated" if result.status == "completed" else str(result.status or "needs_review")
        db.update_teacher_production_job(
            job_id,
            status=final_status,
            progress_percent=100,
            result_run_id=int(result.run_id or 0),
            completed=True,
        )
        return {"status": final_status, "run_id": int(result.run_id or 0), "phase": phase}
    except Exception as exc:
        code, safe = _safe_error(exc)
        db.update_teacher_production_job(
            job_id,
            status="failed",
            progress_percent=100,
            error_code=code,
            error_message_safe=safe,
            completed=True,
        )
        raise


def _enqueue_rq(job_id: int, phase_number: int) -> str:
    from redis import Redis
    from rq import Queue, Retry
    connection = Redis.from_url(os.environ["REDIS_URL"])
    queue_name = str(os.getenv("PRODUCTION_QUEUE_NAME", "3alimnia-production"))
    queue = Queue(queue_name, connection=connection, default_timeout=int(os.getenv("PRODUCTION_JOB_TIMEOUT", "900")))
    rq_job = queue.enqueue(
        run_job,
        int(job_id),
        job_timeout=int(os.getenv("PRODUCTION_JOB_TIMEOUT", "900")),
        retry=Retry(max=int(os.getenv("PRODUCTION_JOB_RETRIES", "2")), interval=[30, 120]),
        description=f"3alimnIA phase {int(phase_number):02d}",
    )
    db.update_teacher_production_job(job_id, queue_job_id=str(rq_job.id))
    return str(rq_job.id)


def enqueue_phase(project_id: int, teacher_username: str, phase_number: int, *, batch_id: str = "", execute_inline: bool = True) -> EnqueueResult:
    phase = int(phase_number)
    if phase not in PHASE_DEPENDENCIES:
        raise ValueError("phase_number must be between 1 and 11")
    project = db.get_teacher_project(int(project_id), str(teacher_username))
    if not project:
        raise ValueError("Teacher project not found or access denied")
    missing = missing_dependencies(int(project_id), phase)
    status = "waiting_for_dependency" if missing else "queued"
    backend = queue_backend()
    job_id = db.create_teacher_production_job(
        int(project_id), str(teacher_username), phase,
        batch_id=str(batch_id), backend=backend,
        parent_job_ids_json=json.dumps(missing),
    )
    if status != "queued":
        db.update_teacher_production_job(job_id, status=status)
        return EnqueueResult(job_id, "", backend, status, phase, str(batch_id))
    if backend == "rq":
        queue_job_id = _enqueue_rq(job_id, phase)
        return EnqueueResult(job_id, queue_job_id, backend, "queued", phase, str(batch_id))
    if execute_inline:
        run_job(job_id)
        current = db.query_one("SELECT status FROM teacher_production_jobs WHERE id=:id", {"id": job_id}) or {}
        return EnqueueResult(job_id, "", backend, str(current.get("status") or "generated"), phase, str(batch_id))
    return EnqueueResult(job_id, "", backend, "queued", phase, str(batch_id))


def enqueue_parallel_batch(project_id: int, teacher_username: str) -> Dict[str, Any]:
    if 3 not in completed_phases(int(project_id)):
        raise ValueError("Phase 3 must be completed before starting batch production")
    batch_id = f"batch-{uuid.uuid4().hex[:12]}"
    results = [enqueue_phase(project_id, teacher_username, phase, batch_id=batch_id) for phase in PARALLEL_PHASES]
    return {"batch_id": batch_id, "backend": queue_backend(), "jobs": [r.__dict__ for r in results]}


def refresh_waiting_jobs(project_id: int) -> int:
    frame = db.teacher_production_jobs_df(int(project_id))
    if frame.empty:
        return 0
    released = 0
    for _, row in frame.iterrows():
        if str(row.get("status") or "") != "waiting_for_dependency":
            continue
        if not missing_dependencies(int(project_id), int(row["phase_number"])):
            db.update_teacher_production_job(int(row["id"]), status="queued")
            if str(row.get("backend") or "") == "rq":
                _enqueue_rq(int(row["id"]), int(row["phase_number"]))
            released += 1
    return released
