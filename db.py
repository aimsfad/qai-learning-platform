"""Database layer for the 3alimnIA Streamlit platform."""

from __future__ import annotations

import hashlib
import json
import os
import secrets as py_secrets
import string
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
import streamlit as st
from sqlalchemy import bindparam, create_engine, text

APP_VERSION = "v6.13-evidence-synthesis-foundation"
from sqlalchemy.engine import Engine

from security import hash_password, verify_password


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


@st.cache_resource(show_spinner=False)
def get_engine() -> Engine:
    database_url = _secret("DATABASE_URL", "").strip() or os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        return create_engine(database_url, pool_pre_ping=True, future=True)
    os.makedirs("data", exist_ok=True)
    return create_engine("sqlite:///data/qai_platform.db", future=True, connect_args={"check_same_thread": False})


def dialect() -> str:
    return get_engine().dialect.name


def exec_sql(sql: str, params: Optional[Dict[str, Any]] = None) -> None:
    with get_engine().begin() as conn:
        conn.execute(text(sql), params or {})


def query_df(sql: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def query_one(sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    with get_engine().connect() as conn:
        row = conn.execute(text(sql), params or {}).mappings().first()
        return dict(row) if row else None


def execute_returning_id(sql: str, params: Dict[str, Any]) -> int:
    with get_engine().begin() as conn:
        result = conn.execute(text(sql), params)
        if dialect() == "sqlite":
            return int(conn.execute(text("SELECT last_insert_rowid()")).scalar_one())
        returned = result.scalar()
        return int(returned)


@st.cache_resource(show_spinner=False)
def init_db() -> None:
    d = dialect()
    id_col = "INTEGER PRIMARY KEY AUTOINCREMENT" if d == "sqlite" else "SERIAL PRIMARY KEY"
    created_default = "TEXT" if d == "sqlite" else "TEXT"

    statements = [
        f"""
        CREATE TABLE IF NOT EXISTS students (
            id {id_col},
            participant_code TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            institution TEXT,
            academic_level TEXT,
            preferred_language TEXT DEFAULT 'ar',
            prior_python_level INTEGER DEFAULT 1,
            prior_quantum_level INTEGER DEFAULT 0,
            study_group TEXT,
            password_hash TEXT,
            created_at {created_default},
            last_login_at {created_default},
            is_active INTEGER DEFAULT 1
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id {id_col},
            student_id INTEGER NOT NULL,
            token_hash TEXT UNIQUE NOT NULL,
            created_at {created_default},
            expires_at {created_default},
            used_at {created_default}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS test_attempts (
            id {id_col},
            student_id INTEGER NOT NULL,
            attempt_type TEXT NOT NULL,
            score REAL NOT NULL,
            correct_count INTEGER NOT NULL,
            total_count INTEGER NOT NULL,
            answers_json TEXT NOT NULL,
            per_concept_json TEXT NOT NULL,
            created_at {created_default},
            UNIQUE(student_id, attempt_type)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS lesson_progress (
            id {id_col},
            student_id INTEGER NOT NULL,
            lesson_id TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            reflection_text TEXT,
            updated_at {created_default},
            UNIQUE(student_id, lesson_id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS learner_attempts (
            id {id_col},
            student_id INTEGER NOT NULL,
            lesson_id TEXT NOT NULL,
            attempt_text TEXT NOT NULL,
            support_mode TEXT,
            char_count INTEGER DEFAULT 0,
            word_count INTEGER DEFAULT 0,
            unique_word_count INTEGER DEFAULT 0,
            validation_status TEXT,
            created_at {created_default},
            updated_at {created_default},
            UNIQUE(student_id, lesson_id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS ai_interactions (
            id {id_col},
            student_id INTEGER NOT NULL,
            module TEXT,
            concept TEXT,
            task TEXT,
            prompt TEXT,
            response TEXT,
            mode TEXT,
            provider TEXT,
            model TEXT,
            diagnostic TEXT,
            created_at {created_default}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS llm_evaluations (
            id {id_col},
            ai_interaction_id INTEGER NOT NULL,
            evaluator_username TEXT,
            conceptual_accuracy INTEGER,
            answer_relevance INTEGER,
            pedagogical_clarity INTEGER,
            scaffolding_quality INTEGER,
            qiskit_alignment INTEGER,
            reflection_support INTEGER,
            personalization INTEGER,
            overall_comment TEXT,
            created_at {created_default},
            UNIQUE(ai_interaction_id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS survey_responses (
            id {id_col},
            student_id INTEGER UNIQUE NOT NULL,
            responses_json TEXT NOT NULL,
            open_feedback_json TEXT NOT NULL,
            created_at {created_default}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS question_responses (
            id {id_col},
            student_id INTEGER NOT NULL,
            attempt_type TEXT NOT NULL,
            question_id TEXT NOT NULL,
            concept TEXT NOT NULL,
            question_text TEXT,
            cognitive_level TEXT,
            selected_index INTEGER,
            selected_answer TEXT,
            correct_index INTEGER,
            correct_answer TEXT,
            is_correct INTEGER NOT NULL,
            explanation TEXT,
            created_at {created_default},
            UNIQUE(student_id, attempt_type, question_id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS consent_records (
            id {id_col},
            student_id INTEGER NOT NULL,
            consent_text TEXT NOT NULL,
            consent_version TEXT DEFAULT 'v1',
            created_at {created_default}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS events_log (
            id {id_col},
            student_id INTEGER,
            actor_role TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_detail TEXT,
            created_at {created_default}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS teacher_accounts (
            id {id_col},
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            institution TEXT,
            specialization TEXT,
            preferred_language TEXT DEFAULT 'ar',
            password_hash TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at {created_default},
            last_login_at {created_default}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS teacher_projects (
            id {id_col},
            teacher_username TEXT NOT NULL,
            project_name TEXT NOT NULL,
            domain TEXT NOT NULL,
            program_name TEXT,
            unit_title TEXT NOT NULL,
            target_concept TEXT NOT NULL,
            target_learners TEXT NOT NULL,
            learner_level TEXT,
            prerequisites TEXT,
            target_languages_json TEXT,
            primary_language TEXT,
            primary_language_code TEXT,
            expected_duration TEXT,
            technical_environment TEXT,
            platform_components_json TEXT,
            source_material TEXT,
            teaching_preferences TEXT,
            assessment_preferences TEXT,
            additional_notes TEXT,
            requested_outputs_json TEXT,
            current_phase INTEGER DEFAULT 1,
            status TEXT DEFAULT 'draft',
            created_at {created_default},
            updated_at {created_default}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS teacher_generation_runs (
            id {id_col},
            project_id INTEGER NOT NULL,
            phase_number INTEGER NOT NULL,
            prompt_text TEXT NOT NULL,
            response_text TEXT,
            provider TEXT,
            model TEXT,
            status TEXT,
            diagnostic TEXT,
            latency_ms INTEGER,
            validation_status TEXT,
            is_fallback_used INTEGER DEFAULT 0,
            created_at {created_default}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS teacher_research_runs (
            id {id_col},
            project_id INTEGER NOT NULL,
            phase_number INTEGER NOT NULL,
            research_mode TEXT,
            query_plan_json TEXT,
            report_text TEXT,
            sources_json TEXT,
            provider TEXT,
            model TEXT,
            status TEXT,
            diagnostic TEXT,
            source_count INTEGER DEFAULT 0,
            latency_ms INTEGER DEFAULT 0,
            is_fallback_used INTEGER DEFAULT 0,
            created_at {created_default}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS teacher_evidence_runs (
            id {id_col},
            project_id INTEGER NOT NULL,
            phase_number INTEGER NOT NULL,
            research_run_id INTEGER,
            prompt_text TEXT,
            response_text TEXT,
            provider TEXT,
            model TEXT,
            status TEXT,
            diagnostic TEXT,
            quality_json TEXT,
            source_count INTEGER DEFAULT 0,
            evidence_card_count INTEGER DEFAULT 0,
            concept_count INTEGER DEFAULT 0,
            latency_ms INTEGER DEFAULT 0,
            is_fallback_used INTEGER DEFAULT 0,
            approved_by_teacher INTEGER DEFAULT 0,
            approved_at {created_default},
            created_at {created_default}
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS teacher_evidence_sources (
            id {id_col},
            evidence_run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            title TEXT,
            url TEXT,
            canonical_url TEXT,
            domain TEXT,
            source_type TEXT,
            language TEXT,
            publication_date TEXT,
            access_date TEXT,
            snippet TEXT,
            authority_score REAL DEFAULT 0,
            relevance_score REAL DEFAULT 0,
            freshness_score REAL DEFAULT 0,
            pedagogical_score REAL DEFAULT 0,
            accessibility_score REAL DEFAULT 0,
            license_score REAL DEFAULT 0,
            composite_score REAL DEFAULT 0,
            status TEXT,
            rationale TEXT,
            fingerprint TEXT,
            UNIQUE(evidence_run_id, source_id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS teacher_evidence_cards (
            id {id_col},
            evidence_run_id INTEGER NOT NULL,
            evidence_id TEXT NOT NULL,
            claim_text TEXT NOT NULL,
            source_ids_json TEXT NOT NULL,
            evidence_excerpt TEXT,
            confidence TEXT,
            intended_use_json TEXT,
            review_status TEXT DEFAULT 'pending',
            UNIQUE(evidence_run_id, evidence_id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS teacher_evidence_concepts (
            id {id_col},
            evidence_run_id INTEGER NOT NULL,
            concept_id TEXT NOT NULL,
            concept_name TEXT NOT NULL,
            description TEXT,
            prerequisites_json TEXT,
            source_ids_json TEXT,
            difficulty TEXT,
            review_status TEXT DEFAULT 'pending',
            UNIQUE(evidence_run_id, concept_id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS adaptive_recommendations (
            id {id_col},
            student_id INTEGER UNIQUE NOT NULL,
            weak_concepts_json TEXT NOT NULL,
            recommended_lessons_json TEXT NOT NULL,
            created_at {created_default}
        )
        """,
    ]
    for stmt in statements:
        exec_sql(stmt)

    # Lightweight migrations for users updating from older releases.
    ensure_column("students", "password_hash", "TEXT")
    ensure_column("students", "is_active", "INTEGER DEFAULT 1")
    ensure_column("students", "last_login_at", "TEXT")
    ensure_column("students", "study_group", "TEXT")
    ensure_column("students", "preferred_language", "TEXT DEFAULT 'ar'")
    ensure_column("ai_interactions", "provider", "TEXT")
    ensure_column("ai_interactions", "model", "TEXT")
    ensure_column("ai_interactions", "diagnostic", "TEXT")
    ensure_column("ai_interactions", "latency_ms", "INTEGER")
    ensure_column("ai_interactions", "response_word_count", "INTEGER")
    ensure_column("ai_interactions", "student_input_language", "TEXT")
    ensure_column("teacher_projects", "published_at", "TEXT")
    ensure_column("teacher_projects", "reviewed_at", "TEXT")
    ensure_column("teacher_generation_runs", "latency_ms", "INTEGER")
    ensure_column("teacher_generation_runs", "validation_status", "TEXT")
    ensure_column("teacher_generation_runs", "is_fallback_used", "INTEGER DEFAULT 0")
    ensure_column("ai_interactions", "response_language", "TEXT")
    ensure_column("ai_interactions", "error_type", "TEXT")
    ensure_column("ai_interactions", "is_fallback_used", "INTEGER DEFAULT 0")
    ensure_column("question_responses", "question_text", "TEXT")
    ensure_column("question_responses", "cognitive_level", "TEXT")
    ensure_column("question_responses", "selected_answer", "TEXT")
    ensure_column("question_responses", "correct_answer", "TEXT")
    ensure_column("question_responses", "explanation", "TEXT")
    ensure_column("test_attempts", "locked", "INTEGER DEFAULT 1")
    ensure_column("test_attempts", "app_version", "TEXT")
    ensure_column("survey_responses", "locked", "INTEGER DEFAULT 1")
    ensure_column("survey_responses", "app_version", "TEXT")
    ensure_column("ai_interactions", "app_version", "TEXT")
    ensure_column("ai_interactions", "prompt_template_version", "TEXT")
    ensure_column("ai_interactions", "lesson_id", "TEXT")
    ensure_column("ai_interactions", "activity_id", "TEXT")
    ensure_column("ai_interactions", "selected_text", "TEXT")
    ensure_column("ai_interactions", "student_usefulness_rating", "INTEGER")
    ensure_column("ai_interactions", "student_ai_feedback", "TEXT")
    ensure_column("teacher_evidence_runs", "approved_by_teacher", "INTEGER DEFAULT 0")
    ensure_column("teacher_evidence_runs", "approved_at", "TEXT")
    ensure_column("teacher_evidence_runs", "quality_json", "TEXT")


def ensure_column(table: str, column: str, col_type: str) -> None:
    d = dialect()
    try:
        if d == "sqlite":
            cols = query_df(f"PRAGMA table_info({table})")
            if column not in set(cols["name"].tolist()):
                exec_sql(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        else:
            exists = query_one(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name=:table AND column_name=:column
                """,
                {"table": table, "column": column},
            )
            if not exists:
                exec_sql(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    except Exception:
        # Avoid breaking the whole app for non-critical migrations.
        pass


def generate_code(prefix: str = "3AI") -> str:
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(30):
        code = f"{prefix}-" + "".join(py_secrets.choice(alphabet) for _ in range(6))
        if not get_student_by_code(code):
            return code
    raise RuntimeError("Could not generate a unique participant code.")


def create_student(
    full_name: str,
    email: str,
    institution: str,
    academic_level: str,
    prior_python_level: int,
    prior_quantum_level: int,
    password: str,
    participant_code: Optional[str] = None,
    study_group: Optional[str] = None,
    preferred_language: str = "ar",
) -> Dict[str, Any]:
    if not full_name.strip():
        raise ValueError("Full name is required.")
    password_hash = hash_password(password)
    code = participant_code or generate_code()
    student_id = execute_returning_id(
        """
        INSERT INTO students
        (participant_code, full_name, email, institution, academic_level, preferred_language, prior_python_level,
         prior_quantum_level, study_group, password_hash, created_at, last_login_at, is_active)
        VALUES
        (:participant_code, :full_name, :email, :institution, :academic_level, :preferred_language, :prior_python_level,
         :prior_quantum_level, :study_group, :password_hash, :created_at, NULL, 1)
        """ + (" RETURNING id" if dialect() != "sqlite" else ""),
        {
            "participant_code": code,
            "full_name": full_name.strip(),
            "email": email.strip().lower(),
            "institution": institution.strip(),
            "academic_level": academic_level,
            "preferred_language": str(preferred_language or "ar"),
            "prior_python_level": int(prior_python_level),
            "prior_quantum_level": int(prior_quantum_level),
            "study_group": (study_group if study_group is not None else "single_arm"),
            "password_hash": password_hash,
            "created_at": utc_now(),
        },
    )
    return get_student(student_id) or {"id": student_id, "participant_code": code}


def get_student(student_id: int) -> Optional[Dict[str, Any]]:
    return query_one("SELECT * FROM students WHERE id=:id", {"id": int(student_id)})


def set_student_preferred_language(student_id: int, language: str) -> None:
    """Persist an ISO language code (ar/fr/en) for a learner account."""
    clean = str(language or "ar").strip().lower()
    if clean not in {"ar", "fr", "en"}:
        raise ValueError("language must be ar, fr, or en")
    exec_sql("UPDATE students SET preferred_language=:lang WHERE id=:id", {"lang": clean, "id": int(student_id)})


def assign_study_group(student_id: int) -> str:
    """Assign a student to a balanced control/experimental group if not already assigned."""
    student = get_student(student_id)
    current = str((student or {}).get("study_group") or "").strip().lower()
    if current in {"control", "experimental", "single_arm"}:
        return current
    counts = query_df(
        """
        SELECT COALESCE(study_group, '') AS study_group, COUNT(*) AS n
        FROM students
        WHERE COALESCE(study_group, '') IN ('control', 'experimental')
        GROUP BY COALESCE(study_group, '')
        """
    )
    count_map = {str(r["study_group"]): int(r["n"]) for _, r in counts.iterrows()} if not counts.empty else {}
    group = "control" if count_map.get("control", 0) <= count_map.get("experimental", 0) else "experimental"
    exec_sql("UPDATE students SET study_group=:group WHERE id=:id", {"group": group, "id": int(student_id)})
    return group


def set_student_study_group(student_id: int, study_group: str) -> None:
    """Administrative helper for correcting a study group assignment."""
    clean = str(study_group or "").strip().lower()
    if clean not in {"control", "experimental", "single_arm"}:
        raise ValueError("study_group must be control, experimental, or single_arm")
    exec_sql("UPDATE students SET study_group=:group WHERE id=:id", {"group": clean, "id": int(student_id)})


def get_student_by_code(code: str) -> Optional[Dict[str, Any]]:
    return query_one("SELECT * FROM students WHERE LOWER(participant_code)=LOWER(:code)", {"code": code.strip()})


def authenticate_student(identifier: str, password: str) -> Optional[Dict[str, Any]]:
    ident = identifier.strip().lower()
    if not ident:
        return None
    student = query_one(
        """
        SELECT * FROM students
        WHERE is_active=1 AND (
            LOWER(participant_code)=:ident OR LOWER(email)=:ident OR LOWER(full_name)=:ident
        )
        ORDER BY id DESC
        """,
        {"ident": ident},
    )
    if student and verify_password(password, student.get("password_hash")):
        exec_sql("UPDATE students SET last_login_at=:ts WHERE id=:id", {"ts": utc_now(), "id": student["id"]})
        return get_student(student["id"])
    return None


def get_student_by_email(email: str) -> Optional[Dict[str, Any]]:
    return query_one(
        "SELECT * FROM students WHERE is_active=1 AND LOWER(email)=LOWER(:email) ORDER BY id DESC",
        {"email": email.strip().lower()},
    )


def _reset_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_password_reset_token(email: str, minutes_valid: int = 30) -> Optional[Tuple[Dict[str, Any], str, str]]:
    """Create a one-time reset token for a student email.

    Returns (student, raw_token, expires_at) if the email exists; otherwise None.
    The raw token is never stored in the database.
    """
    student = get_student_by_email(email)
    if not student:
        return None
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(minutes=int(minutes_valid))).isoformat()
    raw_token = py_secrets.token_urlsafe(32)
    token_hash = _reset_token_hash(raw_token)
    exec_sql(
        """
        INSERT INTO password_reset_tokens
        (student_id, token_hash, created_at, expires_at, used_at)
        VALUES (:student_id, :token_hash, :created_at, :expires_at, NULL)
        """,
        {
            "student_id": student["id"],
            "token_hash": token_hash,
            "created_at": now.isoformat(),
            "expires_at": expires_at,
        },
    )
    return student, raw_token, expires_at


def reset_student_password(token: str, new_password: str) -> Tuple[bool, str]:
    """Validate a password reset token and update the student's password."""
    if not token.strip():
        return False, "Missing reset token."
    if len(new_password or "") < 6:
        return False, "Password must contain at least 6 characters."
    token_hash = _reset_token_hash(token.strip())
    row = query_one(
        """
        SELECT prt.*, s.email, s.participant_code
        FROM password_reset_tokens prt
        JOIN students s ON s.id = prt.student_id
        WHERE prt.token_hash=:token_hash
        """,
        {"token_hash": token_hash},
    )
    if not row:
        return False, "Invalid or expired reset link."
    if row.get("used_at"):
        return False, "This reset link has already been used."
    try:
        expires = datetime.fromisoformat(str(row.get("expires_at")))
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
    except Exception:
        return False, "Invalid reset link expiration."
    if datetime.now(timezone.utc) > expires:
        return False, "This reset link has expired. Please request a new one."
    new_hash = hash_password(new_password)
    now = utc_now()
    exec_sql("UPDATE students SET password_hash=:ph WHERE id=:id", {"ph": new_hash, "id": row["student_id"]})
    exec_sql("UPDATE password_reset_tokens SET used_at=:ts WHERE id=:id", {"ts": now, "id": row["id"]})
    return True, "Password updated successfully. You can now sign in."


def set_student_active(student_id: int, is_active: bool) -> None:
    exec_sql("UPDATE students SET is_active=:active WHERE id=:id", {"active": 1 if is_active else 0, "id": student_id})


def save_test_attempt(student_id: int, attempt_type: str, answers: Dict[str, int], questions: Sequence[Any]) -> Dict[str, Any]:
    """Store a pre/post test once.

    Pilot-safety rule: never overwrite an existing attempt. This preserves data
    already collected from students who have started the live study.
    """
    existing = get_test_attempt(student_id, attempt_type)
    if existing:
        return {
            "score": float(existing.get("score", 0.0)),
            "correct_count": int(existing.get("correct_count", 0)),
            "total_count": int(existing.get("total_count", 0)),
            "per_concept": json.loads(existing.get("per_concept_json") or "{}"),
            "already_submitted": True,
        }

    correct = 0
    per_concept: Dict[str, Dict[str, int]] = {}
    for q in questions:
        selected = answers.get(q.id, -1)
        is_correct = int(selected == q.answer_index)
        correct += is_correct
        per_concept.setdefault(q.concept, {"correct": 0, "total": 0})
        per_concept[q.concept]["correct"] += is_correct
        per_concept[q.concept]["total"] += 1
    total = len(questions)
    score = round((correct / total) * 100, 2) if total else 0.0
    payload = {
        "student_id": student_id,
        "attempt_type": attempt_type,
        "score": score,
        "correct_count": correct,
        "total_count": total,
        "answers_json": json.dumps(answers),
        "per_concept_json": json.dumps(per_concept),
        "created_at": utc_now(),
        "locked": 1,
        "app_version": APP_VERSION,
    }
    sql = """
        INSERT INTO test_attempts
        (student_id, attempt_type, score, correct_count, total_count, answers_json, per_concept_json, created_at, locked, app_version)
        VALUES
        (:student_id, :attempt_type, :score, :correct_count, :total_count, :answers_json, :per_concept_json, :created_at, :locked, :app_version)
    """
    exec_sql(sql, payload)
    save_question_responses(student_id, attempt_type, answers, questions)
    return {"score": score, "correct_count": correct, "total_count": total, "per_concept": per_concept, "already_submitted": False}


def save_question_responses(student_id: int, attempt_type: str, answers: Dict[str, int], questions: Sequence[Any]) -> None:
    """Store per-question responses without deleting existing live data."""
    existing = query_one(
        "SELECT COUNT(*) AS n FROM question_responses WHERE student_id=:sid AND attempt_type=:attempt_type",
        {"sid": student_id, "attempt_type": attempt_type},
    )
    if existing and int(existing.get("n", 0)) > 0:
        return
    for q in questions:
        selected = int(answers.get(q.id, -1))
        selected_answer = q.options[selected] if 0 <= selected < len(q.options) else ""
        correct_answer = q.options[q.answer_index] if 0 <= q.answer_index < len(q.options) else ""
        exec_sql(
            """
            INSERT INTO question_responses
            (student_id, attempt_type, question_id, concept, question_text, cognitive_level, selected_index,
             selected_answer, correct_index, correct_answer, is_correct, explanation, created_at)
            VALUES
            (:student_id, :attempt_type, :question_id, :concept, :question_text, :cognitive_level, :selected_index,
             :selected_answer, :correct_index, :correct_answer, :is_correct, :explanation, :created_at)
            """,
            {
                "student_id": student_id,
                "attempt_type": attempt_type,
                "question_id": q.id,
                "concept": q.concept,
                "question_text": q.question,
                "cognitive_level": getattr(q, "cognitive_level", "Understanding"),
                "selected_index": selected,
                "selected_answer": selected_answer,
                "correct_index": int(q.answer_index),
                "correct_answer": correct_answer,
                "is_correct": 1 if selected == q.answer_index else 0,
                "explanation": q.explanation,
                "created_at": utc_now(),
            },
        )


def get_test_attempt(student_id: int, attempt_type: str) -> Optional[Dict[str, Any]]:
    return query_one(
        "SELECT * FROM test_attempts WHERE student_id=:sid AND attempt_type=:typ",
        {"sid": student_id, "typ": attempt_type},
    )


def compute_adaptive_recommendation(student_id: int, concept_to_lessons: Dict[str, List[str]], threshold: float = 0.75) -> Dict[str, Any]:
    pre = get_test_attempt(student_id, "pre")
    weak: List[str] = []
    lessons: List[str] = []
    if pre:
        per = json.loads(pre.get("per_concept_json") or "{}")
        for concept, stats in per.items():
            total = max(1, int(stats.get("total", 1)))
            ratio = float(stats.get("correct", 0)) / total
            if ratio < threshold:
                weak.append(concept)
                for lesson_id in concept_to_lessons.get(concept, []):
                    if lesson_id not in lessons:
                        lessons.append(lesson_id)
    if not lessons:
        lessons = ["orientation", "hadamard_superposition", "shots_counts", "cnot_correlation"]
    payload = {
        "student_id": student_id,
        "weak_concepts_json": json.dumps(weak),
        "recommended_lessons_json": json.dumps(lessons),
        "created_at": utc_now(),
    }
    if dialect() == "sqlite":
        sql = """
        INSERT OR REPLACE INTO adaptive_recommendations
        (student_id, weak_concepts_json, recommended_lessons_json, created_at)
        VALUES (:student_id, :weak_concepts_json, :recommended_lessons_json, :created_at)
        """
    else:
        sql = """
        INSERT INTO adaptive_recommendations
        (student_id, weak_concepts_json, recommended_lessons_json, created_at)
        VALUES (:student_id, :weak_concepts_json, :recommended_lessons_json, :created_at)
        ON CONFLICT (student_id) DO UPDATE SET
        weak_concepts_json=EXCLUDED.weak_concepts_json,
        recommended_lessons_json=EXCLUDED.recommended_lessons_json,
        created_at=EXCLUDED.created_at
        """
    exec_sql(sql, payload)
    return {"weak_concepts": weak, "recommended_lessons": lessons}


def get_recommendation(student_id: int) -> Optional[Dict[str, Any]]:
    row = query_one("SELECT * FROM adaptive_recommendations WHERE student_id=:sid", {"sid": student_id})
    if not row:
        return None
    return {
        "weak_concepts": json.loads(row.get("weak_concepts_json") or "[]"),
        "recommended_lessons": json.loads(row.get("recommended_lessons_json") or "[]"),
    }


def save_lesson_progress(student_id: int, lesson_id: str, reflection_text: str, completed: bool = True) -> None:
    payload = {
        "student_id": student_id,
        "lesson_id": lesson_id,
        "completed": 1 if completed else 0,
        "reflection_text": reflection_text.strip(),
        "updated_at": utc_now(),
    }
    if dialect() == "sqlite":
        sql = """
        INSERT OR REPLACE INTO lesson_progress
        (student_id, lesson_id, completed, reflection_text, updated_at)
        VALUES (:student_id, :lesson_id, :completed, :reflection_text, :updated_at)
        """
    else:
        sql = """
        INSERT INTO lesson_progress
        (student_id, lesson_id, completed, reflection_text, updated_at)
        VALUES (:student_id, :lesson_id, :completed, :reflection_text, :updated_at)
        ON CONFLICT (student_id, lesson_id) DO UPDATE SET
        completed=EXCLUDED.completed, reflection_text=EXCLUDED.reflection_text, updated_at=EXCLUDED.updated_at
        """
    exec_sql(sql, payload)



def save_learner_attempt(
    student_id: int,
    lesson_id: str,
    attempt_text: str,
    support_mode: str = "",
    validation_status: str = "valid_draft",
    char_count: int = 0,
    word_count: int = 0,
    unique_word_count: int = 0,
) -> None:
    existing = get_learner_attempt(student_id, lesson_id)
    now = utc_now()
    payload = {
        "student_id": int(student_id),
        "lesson_id": str(lesson_id),
        "attempt_text": (attempt_text or "").strip(),
        "support_mode": support_mode or "",
        "char_count": int(char_count),
        "word_count": int(word_count),
        "unique_word_count": int(unique_word_count),
        "validation_status": validation_status or "",
        "created_at": str(existing.get("created_at") or now) if existing else now,
        "updated_at": now,
    }
    if dialect() == "sqlite":
        sql = """
        INSERT OR REPLACE INTO learner_attempts
        (student_id, lesson_id, attempt_text, support_mode, char_count, word_count,
         unique_word_count, validation_status, created_at, updated_at)
        VALUES (:student_id, :lesson_id, :attempt_text, :support_mode, :char_count, :word_count,
                :unique_word_count, :validation_status, :created_at, :updated_at)
        """
    else:
        sql = """
        INSERT INTO learner_attempts
        (student_id, lesson_id, attempt_text, support_mode, char_count, word_count,
         unique_word_count, validation_status, created_at, updated_at)
        VALUES (:student_id, :lesson_id, :attempt_text, :support_mode, :char_count, :word_count,
                :unique_word_count, :validation_status, :created_at, :updated_at)
        ON CONFLICT (student_id, lesson_id) DO UPDATE SET
        attempt_text=EXCLUDED.attempt_text,
        support_mode=EXCLUDED.support_mode,
        char_count=EXCLUDED.char_count,
        word_count=EXCLUDED.word_count,
        unique_word_count=EXCLUDED.unique_word_count,
        validation_status=EXCLUDED.validation_status,
        updated_at=EXCLUDED.updated_at
        """
    exec_sql(sql, payload)


def get_learner_attempt(student_id: int, lesson_id: str) -> Optional[Dict[str, Any]]:
    return query_one(
        "SELECT * FROM learner_attempts WHERE student_id=:sid AND lesson_id=:lesson_id",
        {"sid": int(student_id), "lesson_id": str(lesson_id)},
    )


def learner_attempts_df() -> pd.DataFrame:
    return query_df("SELECT * FROM learner_attempts ORDER BY updated_at DESC, id DESC")

def get_lesson_progress(student_id: int) -> pd.DataFrame:
    return query_df("SELECT * FROM lesson_progress WHERE student_id=:sid", {"sid": student_id})


def log_ai_interaction(
    student_id: int,
    module: str,
    concept: str,
    task: str,
    prompt: str,
    response: str,
    mode: str,
    provider: str,
    model: str,
    diagnostic: str = "",
    latency_ms: Optional[int] = None,
    response_word_count: Optional[int] = None,
    student_input_language: str = "",
    response_language: str = "",
    error_type: str = "",
    is_fallback_used: int = 0,
    prompt_template_version: str = "qai-tutor-v5",
    lesson_id: str = "",
    activity_id: str = "",
    selected_text: str = "",
) -> int:
    sql = """
        INSERT INTO ai_interactions
        (student_id, module, concept, task, prompt, response, mode, provider, model, diagnostic,
         latency_ms, response_word_count, student_input_language, response_language, error_type,
         is_fallback_used, app_version, prompt_template_version, lesson_id, activity_id, selected_text, created_at)
        VALUES
        (:student_id, :module, :concept, :task, :prompt, :response, :mode, :provider, :model, :diagnostic,
         :latency_ms, :response_word_count, :student_input_language, :response_language, :error_type,
         :is_fallback_used, :app_version, :prompt_template_version, :lesson_id, :activity_id, :selected_text, :created_at)
    """ + (" RETURNING id" if dialect() != "sqlite" else "")
    return execute_returning_id(
        sql,
        {
            "student_id": student_id,
            "module": module,
            "concept": concept,
            "task": task,
            "prompt": prompt,
            "response": response,
            "mode": mode,
            "provider": provider,
            "model": model,
            "diagnostic": diagnostic,
            "latency_ms": latency_ms,
            "response_word_count": response_word_count if response_word_count is not None else len((response or "").split()),
            "student_input_language": student_input_language,
            "response_language": response_language,
            "error_type": error_type,
            "is_fallback_used": int(is_fallback_used or 0),
            "app_version": APP_VERSION,
            "prompt_template_version": prompt_template_version,
            "lesson_id": lesson_id,
            "activity_id": activity_id,
            "selected_text": selected_text,
            "created_at": utc_now(),
        },
    )


def update_ai_student_feedback(ai_interaction_id: int, usefulness_rating: int, comment: str = "") -> None:
    exec_sql(
        """
        UPDATE ai_interactions
        SET student_usefulness_rating=:rating, student_ai_feedback=:comment
        WHERE id=:id
        """,
        {"rating": int(usefulness_rating), "comment": comment.strip(), "id": int(ai_interaction_id)},
    )


def save_llm_evaluation(
    ai_interaction_id: int,
    evaluator_username: str,
    conceptual_accuracy: int,
    answer_relevance: int,
    pedagogical_clarity: int,
    scaffolding_quality: int,
    qiskit_alignment: int,
    reflection_support: int,
    personalization: int,
    overall_comment: str = "",
) -> None:
    payload = {
        "ai_interaction_id": int(ai_interaction_id),
        "evaluator_username": evaluator_username.strip(),
        "conceptual_accuracy": int(conceptual_accuracy),
        "answer_relevance": int(answer_relevance),
        "pedagogical_clarity": int(pedagogical_clarity),
        "scaffolding_quality": int(scaffolding_quality),
        "qiskit_alignment": int(qiskit_alignment),
        "reflection_support": int(reflection_support),
        "personalization": int(personalization),
        "overall_comment": overall_comment.strip(),
        "created_at": utc_now(),
    }
    if dialect() == "sqlite":
        sql = """
        INSERT OR REPLACE INTO llm_evaluations
        (ai_interaction_id, evaluator_username, conceptual_accuracy, answer_relevance,
         pedagogical_clarity, scaffolding_quality, qiskit_alignment, reflection_support,
         personalization, overall_comment, created_at)
        VALUES
        (:ai_interaction_id, :evaluator_username, :conceptual_accuracy, :answer_relevance,
         :pedagogical_clarity, :scaffolding_quality, :qiskit_alignment, :reflection_support,
         :personalization, :overall_comment, :created_at)
        """
    else:
        sql = """
        INSERT INTO llm_evaluations
        (ai_interaction_id, evaluator_username, conceptual_accuracy, answer_relevance,
         pedagogical_clarity, scaffolding_quality, qiskit_alignment, reflection_support,
         personalization, overall_comment, created_at)
        VALUES
        (:ai_interaction_id, :evaluator_username, :conceptual_accuracy, :answer_relevance,
         :pedagogical_clarity, :scaffolding_quality, :qiskit_alignment, :reflection_support,
         :personalization, :overall_comment, :created_at)
        ON CONFLICT (ai_interaction_id) DO UPDATE SET
        evaluator_username=EXCLUDED.evaluator_username,
        conceptual_accuracy=EXCLUDED.conceptual_accuracy,
        answer_relevance=EXCLUDED.answer_relevance,
        pedagogical_clarity=EXCLUDED.pedagogical_clarity,
        scaffolding_quality=EXCLUDED.scaffolding_quality,
        qiskit_alignment=EXCLUDED.qiskit_alignment,
        reflection_support=EXCLUDED.reflection_support,
        personalization=EXCLUDED.personalization,
        overall_comment=EXCLUDED.overall_comment,
        created_at=EXCLUDED.created_at
        """
    exec_sql(sql, payload)


def llm_evaluations_df() -> pd.DataFrame:
    return query_df(
        """
        SELECT e.*, a.student_id, s.participant_code, s.full_name, a.module, a.concept, a.task,
               a.mode, a.provider, a.model, a.prompt, a.response, a.created_at AS interaction_created_at,
               ROUND((conceptual_accuracy + answer_relevance + pedagogical_clarity + scaffolding_quality +
                      qiskit_alignment + reflection_support + personalization) / 7.0, 2) AS pedagogical_quality_score
        FROM llm_evaluations e
        LEFT JOIN ai_interactions a ON a.id=e.ai_interaction_id
        LEFT JOIN students s ON s.id=a.student_id
        ORDER BY e.created_at DESC
        """
    )


def llm_evaluation_summary_df() -> pd.DataFrame:
    df = llm_evaluations_df()
    if df.empty:
        return pd.DataFrame()
    cols = [
        "conceptual_accuracy", "answer_relevance", "pedagogical_clarity", "scaffolding_quality",
        "qiskit_alignment", "reflection_support", "personalization", "pedagogical_quality_score",
    ]
    rows = []
    for col in cols:
        if col in df:
            rows.append({"metric": col, "mean_score": round(float(pd.to_numeric(df[col], errors="coerce").mean()), 2), "n": int(df[col].notna().sum())})
    return pd.DataFrame(rows)


def llm_candidate_interactions_df(limit: int = 100, only_unrated: bool = False, only_llm: bool = True) -> pd.DataFrame:
    where = []
    if only_llm:
        where.append("a.mode IN ('llm', 'llm_error')")
    if only_unrated:
        where.append("e.id IS NULL")
    where_sql = " WHERE " + " AND ".join(where) if where else ""
    sql = f"""
        SELECT a.id AS interaction_id, a.created_at, s.participant_code, s.full_name,
               a.module, a.concept, a.task, a.mode, a.provider, a.model, a.prompt, a.response,
               a.diagnostic, a.latency_ms, a.response_word_count, a.student_input_language,
               a.response_language, a.error_type, a.is_fallback_used,
               e.id AS evaluation_id,
               ROUND((e.conceptual_accuracy + e.answer_relevance + e.pedagogical_clarity + e.scaffolding_quality +
                      e.qiskit_alignment + e.reflection_support + e.personalization) / 7.0, 2) AS existing_quality_score
        FROM ai_interactions a
        LEFT JOIN students s ON s.id=a.student_id
        LEFT JOIN llm_evaluations e ON e.ai_interaction_id=a.id
        {where_sql}
        ORDER BY a.created_at DESC
        LIMIT :limit
    """
    return query_df(sql, {"limit": int(limit)})



def save_consent(student_id: int, consent_text: str, consent_version: str = "v1") -> None:
    exec_sql(
        """
        INSERT INTO consent_records (student_id, consent_text, consent_version, created_at)
        VALUES (:student_id, :consent_text, :consent_version, :created_at)
        """,
        {
            "student_id": student_id,
            "consent_text": consent_text.strip(),
            "consent_version": consent_version,
            "created_at": utc_now(),
        },
    )


def has_consent(student_id: int) -> bool:
    row = query_one("SELECT COUNT(*) AS n FROM consent_records WHERE student_id=:sid", {"sid": int(student_id)})
    return bool(row and int(row.get("n", 0)) > 0)


def ai_interaction_count(student_id: int) -> int:
    row = query_one("SELECT COUNT(*) AS n FROM ai_interactions WHERE student_id=:sid", {"sid": int(student_id)})
    return int(row.get("n", 0)) if row else 0


def completed_lesson_count(student_id: int) -> int:
    row = query_one(
        "SELECT COUNT(*) AS n FROM lesson_progress WHERE student_id=:sid AND completed=1",
        {"sid": int(student_id)},
    )
    return int(row.get("n", 0)) if row else 0


def complete_case_status(student_id: int, total_lessons: int) -> Dict[str, Any]:
    pre_done = get_test_attempt(student_id, "pre") is not None
    post_done = get_test_attempt(student_id, "post") is not None
    survey_done = get_survey(student_id) is not None
    completed_lessons = completed_lesson_count(student_id)
    ai_count = ai_interaction_count(student_id)
    consent_done = has_consent(student_id)
    requirements = {
        "consent": consent_done,
        "pre_test": pre_done,
        "at_least_one_lesson": completed_lessons >= 1,
        "at_least_one_ai_interaction": ai_count >= 1,
        "post_test": post_done,
        "survey": survey_done,
    }
    missing = [key for key, ok in requirements.items() if not ok]
    return {
        "is_complete_case": len(missing) == 0,
        "missing_requirements": missing,
        "completed_lessons": completed_lessons,
        "ai_interactions": ai_count,
        "consent_done": consent_done,
    }


def log_event(student_id: Optional[int], actor_role: str, event_type: str, event_detail: str = "") -> None:
    exec_sql(
        """
        INSERT INTO events_log (student_id, actor_role, event_type, event_detail, created_at)
        VALUES (:student_id, :actor_role, :event_type, :event_detail, :created_at)
        """,
        {
            "student_id": student_id,
            "actor_role": actor_role,
            "event_type": event_type,
            "event_detail": event_detail,
            "created_at": utc_now(),
        },
    )


def get_last_open_lesson(student_id: int) -> str:
    row = query_one(
        """
        SELECT event_detail FROM events_log
        WHERE student_id=:sid AND event_type='open_module'
        ORDER BY created_at DESC, id DESC
        """,
        {"sid": int(student_id)},
    )
    return str(row.get("event_detail") or "") if row else ""


def student_events_df(student_id: int, limit: int = 150) -> pd.DataFrame:
    return query_df(
        """
        SELECT created_at, actor_role, event_type, event_detail
        FROM events_log
        WHERE student_id=:sid
        ORDER BY created_at DESC, id DESC
        LIMIT :limit
        """,
        {"sid": int(student_id), "limit": int(limit)},
    )


def ai_learning_observer_df() -> pd.DataFrame:
    return query_df(
        """
        SELECT
            COALESCE(NULLIF(module,''), 'unknown') AS module,
            COALESCE(NULLIF(lesson_id,''), 'not linked') AS lesson_id,
            COUNT(*) AS interactions,
            AVG(latency_ms) AS avg_latency_ms,
            AVG(response_word_count) AS avg_response_words,
            AVG(student_usefulness_rating) AS avg_student_usefulness,
            SUM(CASE WHEN is_fallback_used=1 THEN 1 ELSE 0 END) AS fallback_count
        FROM ai_interactions
        GROUP BY COALESCE(NULLIF(module,''), 'unknown'), COALESCE(NULLIF(lesson_id,''), 'not linked')
        ORDER BY interactions DESC
        """
    )



def ai_task_mode_df() -> pd.DataFrame:
    """Aggregate AI support by pedagogical task/mode for research analytics."""
    return query_df(
        """
        SELECT
            COALESCE(NULLIF(lesson_id,''), 'not linked') AS lesson_id,
            COALESCE(NULLIF(module,''), 'unknown') AS module,
            COALESCE(NULLIF(task,''), 'unspecified') AS task,
            COALESCE(NULLIF(provider,''), 'unknown') AS provider,
            COALESCE(NULLIF(mode,''), 'unknown') AS mode,
            COUNT(*) AS interactions,
            AVG(latency_ms) AS avg_latency_ms,
            AVG(response_word_count) AS avg_response_words,
            AVG(student_usefulness_rating) AS avg_student_usefulness,
            SUM(CASE WHEN is_fallback_used=1 THEN 1 ELSE 0 END) AS fallback_count
        FROM ai_interactions
        GROUP BY
            COALESCE(NULLIF(lesson_id,''), 'not linked'),
            COALESCE(NULLIF(module,''), 'unknown'),
            COALESCE(NULLIF(task,''), 'unspecified'),
            COALESCE(NULLIF(provider,''), 'unknown'),
            COALESCE(NULLIF(mode,''), 'unknown')
        ORDER BY interactions DESC
        """
    )


def ai_request_timing_events_df() -> pd.DataFrame:
    """Return raw AI timing events; event_detail contains JSON with seconds_before_ai."""
    return query_df(
        """
        SELECT e.created_at, e.student_id, s.participant_code, s.full_name, e.event_detail
        FROM events_log e
        LEFT JOIN students s ON s.id=e.student_id
        WHERE e.event_type='ai_request_timing'
        ORDER BY e.created_at DESC, e.id DESC
        """
    )

def save_survey(student_id: int, responses: Dict[str, int], open_feedback: Dict[str, str]) -> None:
    """Store the survey once; do not overwrite live pilot responses."""
    existing = get_survey(student_id)
    if existing:
        return
    payload = {
        "student_id": student_id,
        "responses_json": json.dumps(responses),
        "open_feedback_json": json.dumps(open_feedback),
        "created_at": utc_now(),
        "locked": 1,
        "app_version": APP_VERSION,
    }
    sql = """
        INSERT INTO survey_responses
        (student_id, responses_json, open_feedback_json, created_at, locked, app_version)
        VALUES (:student_id, :responses_json, :open_feedback_json, :created_at, :locked, :app_version)
    """
    exec_sql(sql, payload)


def get_survey(student_id: int) -> Optional[Dict[str, Any]]:
    return query_one("SELECT * FROM survey_responses WHERE student_id=:sid", {"sid": student_id})


def students_df(limit: Optional[int] = None) -> pd.DataFrame:
    sql = """
        SELECT id, participant_code, full_name, email, institution, academic_level,
               COALESCE(preferred_language, 'ar') AS preferred_language,
               prior_python_level, prior_quantum_level, COALESCE(study_group, 'single_arm') AS study_group, created_at, last_login_at, is_active
        FROM students
        ORDER BY created_at DESC
    """
    params: Dict[str, Any] = {}
    if limit is not None:
        sql += " LIMIT :limit"
        params["limit"] = int(limit)
    return query_df(sql, params)


def count_rows(table: str) -> int:
    allowed = {"students", "test_attempts", "survey_responses", "ai_interactions", "events_log", "consent_records", "lesson_progress", "learner_attempts"}
    if table not in allowed:
        raise ValueError(f"Unsupported table for count_rows: {table}")
    row = query_one(f"SELECT COUNT(*) AS n FROM {table}")
    return int(row["n"]) if row else 0


def attempts_df() -> pd.DataFrame:
    return query_df("SELECT * FROM test_attempts")


def ai_usage_df() -> pd.DataFrame:
    return query_df(
        """
        SELECT COALESCE(mode, 'unknown') AS mode,
               COALESCE(provider, 'unknown') AS provider,
               COALESCE(model, 'unknown') AS model,
               COUNT(*) AS interactions
        FROM ai_interactions
        GROUP BY mode, provider, model
        ORDER BY interactions DESC
        """
    )


def ai_filter_options() -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for col in ["mode", "module", "concept"]:
        df = query_df(f"SELECT DISTINCT {col} AS value FROM ai_interactions WHERE {col} IS NOT NULL ORDER BY {col}")
        out[col] = df["value"].dropna().astype(str).tolist() if not df.empty else []
    return out


def ai_logs_df(
    limit: Optional[int] = None,
    mode: Optional[Sequence[str]] = None,
    module: Optional[Sequence[str]] = None,
    concept: Optional[Sequence[str]] = None,
    participant_code: Optional[str] = None,
) -> pd.DataFrame:
    where = []
    params: Dict[str, Any] = {}
    if mode:
        where.append("a.mode IN :modes")
        params["modes"] = tuple(mode)
    if module:
        where.append("a.module IN :modules")
        params["modules"] = tuple(module)
    if concept:
        where.append("a.concept IN :concepts")
        params["concepts"] = tuple(concept)
    if participant_code:
        where.append("s.participant_code = :participant_code")
        params["participant_code"] = participant_code
    where_sql = " WHERE " + " AND ".join(where) if where else ""
    sql = f"""
        SELECT a.id AS interaction_id, a.created_at, s.participant_code, s.full_name, a.module, a.concept, a.task,
               a.mode, a.provider, a.model, a.prompt, a.response, a.diagnostic,
               a.latency_ms, a.response_word_count, a.student_input_language, a.response_language,
               a.error_type, a.is_fallback_used, a.app_version, a.prompt_template_version, a.lesson_id, a.activity_id, a.selected_text, a.student_usefulness_rating, a.student_ai_feedback
        FROM ai_interactions a
        LEFT JOIN students s ON s.id=a.student_id
        {where_sql}
        ORDER BY a.created_at DESC
    """
    if limit is not None:
        sql += " LIMIT :limit"
        params["limit"] = int(limit)
    stmt = text(sql)
    if mode:
        stmt = stmt.bindparams(bindparam("modes", expanding=True))
    if module:
        stmt = stmt.bindparams(bindparam("modules", expanding=True))
    if concept:
        stmt = stmt.bindparams(bindparam("concepts", expanding=True))
    with get_engine().connect() as conn:
        return pd.read_sql(stmt, conn, params=params)


def survey_df() -> pd.DataFrame:
    return query_df(
        """
        SELECT s.participant_code, s.full_name, r.responses_json, r.open_feedback_json, r.created_at
        FROM survey_responses r
        LEFT JOIN students s ON s.id=r.student_id
        ORDER BY r.created_at DESC
        """
    )


def progress_summary_df(total_lessons: int) -> pd.DataFrame:
    students = students_df()
    if students.empty:
        return students
    attempts = attempts_df()
    progress = query_df("SELECT student_id, COUNT(*) AS completed_lessons FROM lesson_progress WHERE completed=1 GROUP BY student_id")
    surveys = query_df("SELECT student_id, COUNT(*) AS survey_done FROM survey_responses GROUP BY student_id")
    ai_counts = query_df("SELECT student_id, COUNT(*) AS ai_interactions FROM ai_interactions GROUP BY student_id")
    consents = query_df("SELECT student_id, COUNT(*) AS consent_done FROM consent_records GROUP BY student_id")
    pre = attempts[attempts["attempt_type"] == "pre"][["student_id", "score"]].rename(columns={"score": "pre_score"}) if not attempts.empty else pd.DataFrame(columns=["student_id", "pre_score"])
    post = attempts[attempts["attempt_type"] == "post"][["student_id", "score"]].rename(columns={"score": "post_score"}) if not attempts.empty else pd.DataFrame(columns=["student_id", "post_score"])
    df = students.rename(columns={"id": "student_id"})
    for other in [pre, post, progress, surveys, ai_counts, consents]:
        df = df.merge(other, how="left", on="student_id")
    df["completed_lessons"] = df["completed_lessons"].fillna(0).astype(int)
    df["survey_done"] = df["survey_done"].fillna(0).astype(int)
    df["ai_interactions"] = df["ai_interactions"].fillna(0).astype(int)
    df["consent_done"] = df["consent_done"].fillna(0).astype(int)
    df["pre_done"] = df["pre_score"].notna()
    df["post_done"] = df["post_score"].notna()
    df["learning_gain"] = df["post_score"] - df["pre_score"]
    df["has_ai_interaction"] = df["ai_interactions"] > 0
    df["has_lesson_activity"] = df["completed_lessons"] >= 1
    df["is_complete_case"] = (
        (df["consent_done"] > 0)
        & df["pre_done"]
        & df["has_lesson_activity"]
        & df["has_ai_interaction"]
        & df["post_done"]
        & (df["survey_done"] > 0)
    )

    def _missing_reason(row: pd.Series) -> str:
        missing = []
        if int(row.get("consent_done", 0)) <= 0:
            missing.append("consent")
        if not bool(row.get("pre_done", False)):
            missing.append("pre-test")
        if int(row.get("completed_lessons", 0)) < 1:
            missing.append("lesson")
        if int(row.get("ai_interactions", 0)) < 1:
            missing.append("AI interaction")
        if not bool(row.get("post_done", False)):
            missing.append("post-test")
        if int(row.get("survey_done", 0)) <= 0:
            missing.append("survey")
        return "Complete" if not missing else ", ".join(missing)

    df["complete_case_missing"] = df.apply(_missing_reason, axis=1)
    df["progress_percent"] = (
        (df["consent_done"] > 0).astype(int)
        + df["pre_done"].astype(int)
        + (df["completed_lessons"] / max(1, total_lessons))
        + (df["ai_interactions"] > 0).astype(int)
        + df["post_done"].astype(int)
        + (df["survey_done"] > 0).astype(int)
    ) / 6 * 100
    return df


def concept_scores_df() -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    attempts = attempts_df()
    for _, row in attempts.iterrows():
        per = json.loads(row.get("per_concept_json") or "{}")
        for concept, stats in per.items():
            total = max(1, int(stats.get("total", 1)))
            rows.append({
                "student_id": row["student_id"],
                "attempt_type": row["attempt_type"],
                "concept": concept,
                "percentage": round(float(stats.get("correct", 0)) / total * 100, 2),
                "correct": int(stats.get("correct", 0)),
                "total": total,
            })
    return pd.DataFrame(rows)


def question_responses_df() -> pd.DataFrame:
    return query_df(
        """
        SELECT q.*, s.participant_code, s.full_name
        FROM question_responses q
        LEFT JOIN students s ON s.id=q.student_id
        ORDER BY q.created_at DESC
        """
    )


def consent_records_df() -> pd.DataFrame:
    return query_df(
        """
        SELECT c.*, s.participant_code, s.full_name
        FROM consent_records c
        LEFT JOIN students s ON s.id=c.student_id
        ORDER BY c.created_at DESC
        """
    )


def events_log_df(limit: Optional[int] = None) -> pd.DataFrame:
    sql = """
        SELECT e.*, s.participant_code, s.full_name
        FROM events_log e
        LEFT JOIN students s ON s.id=e.student_id
        ORDER BY e.created_at DESC
    """
    params: Dict[str, Any] = {}
    if limit is not None:
        sql += " LIMIT :limit"
        params["limit"] = int(limit)
    return query_df(sql, params)



def anonymize_dataframe(df: pd.DataFrame, keep_student_id: bool = False) -> pd.DataFrame:
    """Remove direct identifiers from exports while preserving research variables."""
    if df is None or df.empty:
        return df
    out = df.copy()
    drop_cols = [
        "full_name", "email", "institution", "password_hash", "raw_name", "name",
    ]
    if not keep_student_id:
        drop_cols.extend(["student_id", "id"])
    out = out.drop(columns=[c for c in drop_cols if c in out.columns], errors="ignore")
    return out


def research_export_tables(total_lessons: int, anonymized: bool = True) -> Dict[str, pd.DataFrame]:
    """Paper-ready export tables. Defaults to anonymized data for ethics-safe analysis."""
    tables: Dict[str, pd.DataFrame] = {
        "progress_summary": progress_summary_df(total_lessons),
        "test_attempts": attempts_df(),
        "question_responses": question_responses_df(),
        "concept_scores": concept_scores_df(),
        "lesson_reflections": query_df("SELECT * FROM lesson_progress"),
        "learner_attempts": learner_attempts_df(),
        "ai_interactions": ai_logs_df(),
        "llm_evaluations": llm_evaluations_df(),
        "llm_evaluation_summary": llm_evaluation_summary_df(),
        "surveys": survey_df(),
        "consent_records": consent_records_df(),
        "event_logs": events_log_df(),
    }
    if anonymized:
        tables = {name: anonymize_dataframe(df) for name, df in tables.items()}
        # Free-text attempts can contain names or other self-disclosed identifiers.
        # Keep research-safe quantitative metadata in anonymized exports and reserve
        # the raw attempt text for the protected administrative workbook.
        if "learner_attempts" in tables and not tables["learner_attempts"].empty:
            tables["learner_attempts"] = tables["learner_attempts"].drop(
                columns=["attempt_text"], errors="ignore"
            )
    return tables


def system_readiness(total_lessons: int) -> Dict[str, Any]:
    """Return non-destructive checks for the live Streamlit/Neon deployment."""
    d = dialect()
    status: Dict[str, Any] = {
        "app_version": APP_VERSION,
        "database_dialect": d,
        "database_ok": False,
        "database_error": "",
    }
    try:
        row = query_one("SELECT 1 AS ok")
        status["database_ok"] = bool(row and int(row.get("ok", 0)) == 1)
    except Exception as exc:
        status["database_error"] = str(exc)
    for table in ["students", "test_attempts", "survey_responses", "ai_interactions", "events_log", "consent_records", "lesson_progress", "learner_attempts"]:
        try:
            status[f"n_{table}"] = count_rows(table)
        except Exception:
            status[f"n_{table}"] = None
    try:
        progress = progress_summary_df(total_lessons)
        status["n_pre"] = int(progress["pre_done"].sum()) if not progress.empty and "pre_done" in progress else 0
        status["n_post"] = int(progress["post_done"].sum()) if not progress.empty and "post_done" in progress else 0
        status["n_complete_cases"] = int(progress["is_complete_case"].sum()) if not progress.empty and "is_complete_case" in progress else 0
        status["n_with_ai_interaction"] = int((progress["ai_interactions"] > 0).sum()) if not progress.empty and "ai_interactions" in progress else 0
    except Exception as exc:
        status["progress_error"] = str(exc)
    return status


def paper_summary() -> Dict[str, Any]:
    """Return paper-ready aggregate metrics for the one-group pilot study."""
    progress = progress_summary_df(total_lessons=6)
    logs = ai_logs_df()
    concept = concept_scores_df()
    survey = survey_df()
    completed = progress.dropna(subset=["pre_score", "post_score"]) if not progress.empty else pd.DataFrame()
    out: Dict[str, Any] = {
        "n_registered": int(len(progress)) if not progress.empty else 0,
        "n_pre": int(progress["pre_done"].sum()) if not progress.empty and "pre_done" in progress else 0,
        "n_post": int(progress["post_done"].sum()) if not progress.empty and "post_done" in progress else 0,
        "n_complete_pairs": int(len(completed)),
        "n_complete_cases": int(progress["is_complete_case"].sum()) if not progress.empty and "is_complete_case" in progress else 0,
        "n_surveys": int(len(survey)) if not survey.empty else 0,
        "total_ai_interactions": int(len(logs)) if not logs.empty else 0,
    }
    if not completed.empty:
        out.update({
            "mean_pre": round(float(completed["pre_score"].mean()), 2),
            "mean_post": round(float(completed["post_score"].mean()), 2),
            "mean_gain": round(float(completed["learning_gain"].mean()), 2),
            "median_gain": round(float(completed["learning_gain"].median()), 2),
        })
    else:
        out.update({"mean_pre": None, "mean_post": None, "mean_gain": None, "median_gain": None})
    return out

# -----------------------------------------------------------------------------
# Teacher Content Studio persistence
# -----------------------------------------------------------------------------

def get_teacher_account(identifier: str) -> Optional[Dict[str, Any]]:
    """Return an active teacher account by username or email."""
    ident = str(identifier or "").strip().lower()
    if not ident:
        return None
    return query_one(
        """
        SELECT * FROM teacher_accounts
        WHERE is_active=1 AND (LOWER(username)=:ident OR LOWER(email)=:ident)
        ORDER BY id DESC
        """,
        {"ident": ident},
    )


def get_teacher_account_by_id(account_id: int) -> Optional[Dict[str, Any]]:
    return query_one(
        "SELECT * FROM teacher_accounts WHERE id=:id AND is_active=1",
        {"id": int(account_id)},
    )


def create_teacher_account(
    full_name: str,
    username: str,
    email: str,
    institution: str,
    specialization: str,
    password: str,
    preferred_language: str = "ar",
) -> Dict[str, Any]:
    """Create a password-protected teacher account.

    User-facing validation is performed in the teacher UI; uniqueness and
    password hashing are enforced again here at the persistence boundary.
    """
    clean_name = str(full_name or "").strip()
    clean_username = str(username or "").strip().lower()
    clean_email = str(email or "").strip().lower()
    clean_language = str(preferred_language or "ar").strip().lower()
    if not clean_name:
        raise ValueError("Full name is required.")
    if not clean_username:
        raise ValueError("Username is required.")
    if not clean_email or "@" not in clean_email:
        raise ValueError("A valid email address is required.")
    if get_teacher_account(clean_username):
        raise ValueError("This username or email is already registered.")
    existing_email = query_one(
        "SELECT id FROM teacher_accounts WHERE LOWER(email)=:email",
        {"email": clean_email},
    )
    if existing_email:
        raise ValueError("This email address is already registered.")
    if clean_language not in {"ar", "fr", "en"}:
        clean_language = "ar"
    password_hash = hash_password(password)
    account_id = execute_returning_id(
        """
        INSERT INTO teacher_accounts
        (username, email, full_name, institution, specialization, preferred_language, password_hash,
         is_active, created_at, last_login_at)
        VALUES
        (:username, :email, :full_name, :institution, :specialization, :preferred_language, :password_hash,
         1, :created_at, NULL)
        """ + (" RETURNING id" if dialect() != "sqlite" else ""),
        {
            "username": clean_username,
            "email": clean_email,
            "full_name": clean_name,
            "institution": str(institution or "").strip(),
            "specialization": str(specialization or "").strip(),
            "preferred_language": clean_language,
            "password_hash": password_hash,
            "created_at": utc_now(),
        },
    )
    return get_teacher_account_by_id(account_id) or {"id": account_id, "username": clean_username}


def authenticate_teacher(identifier: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a database-backed teacher account."""
    account = get_teacher_account(identifier)
    if account and verify_password(password, account.get("password_hash")):
        exec_sql(
            "UPDATE teacher_accounts SET last_login_at=:ts WHERE id=:id",
            {"ts": utc_now(), "id": int(account["id"])},
        )
        return get_teacher_account_by_id(int(account["id"]))
    return None


def set_teacher_preferred_language(account_id: int, language: str) -> None:
    clean = str(language or "ar").strip().lower()
    if clean not in {"ar", "fr", "en"}:
        raise ValueError("language must be ar, fr, or en")
    exec_sql(
        "UPDATE teacher_accounts SET preferred_language=:lang WHERE id=:id",
        {"lang": clean, "id": int(account_id)},
    )


def teacher_account_count() -> int:
    row = query_one("SELECT COUNT(*) AS n FROM teacher_accounts WHERE is_active=1")
    return int((row or {}).get("n") or 0)


def save_teacher_project(data: Dict[str, Any]) -> int:
    """Create or update a teacher-authored educational production brief."""
    payload = {
        "teacher_username": str(data.get("teacher_username") or "teacher").strip(),
        "project_name": str(data.get("project_name") or "").strip(),
        "domain": str(data.get("domain") or "").strip(),
        "program_name": str(data.get("program_name") or "").strip(),
        "unit_title": str(data.get("unit_title") or "").strip(),
        "target_concept": str(data.get("target_concept") or "").strip(),
        "target_learners": str(data.get("target_learners") or "").strip(),
        "learner_level": str(data.get("learner_level") or "").strip(),
        "prerequisites": str(data.get("prerequisites") or "").strip(),
        "target_languages_json": json.dumps(data.get("target_languages") or [], ensure_ascii=False),
        "primary_language": str(data.get("primary_language") or "English").strip(),
        "primary_language_code": str(data.get("primary_language_code") or "en").strip(),
        "expected_duration": str(data.get("expected_duration") or "").strip(),
        "technical_environment": str(data.get("technical_environment") or "").strip(),
        "platform_components_json": json.dumps(data.get("platform_components") or [], ensure_ascii=False),
        "source_material": str(data.get("source_material") or "").strip(),
        "teaching_preferences": str(data.get("teaching_preferences") or "").strip(),
        "assessment_preferences": str(data.get("assessment_preferences") or "").strip(),
        "additional_notes": str(data.get("additional_notes") or "").strip(),
        "requested_outputs_json": json.dumps(data.get("requested_outputs") or [], ensure_ascii=False),
        "current_phase": int(data.get("current_phase") or 1),
        "status": str(data.get("status") or "draft"),
        "updated_at": utc_now(),
    }
    project_id = data.get("id")
    if project_id:
        payload["id"] = int(project_id)
        exec_sql(
            """
            UPDATE teacher_projects SET
                teacher_username=:teacher_username, project_name=:project_name, domain=:domain, program_name=:program_name,
                unit_title=:unit_title, target_concept=:target_concept, target_learners=:target_learners, learner_level=:learner_level,
                prerequisites=:prerequisites, target_languages_json=:target_languages_json, primary_language=:primary_language,
                primary_language_code=:primary_language_code, expected_duration=:expected_duration,
                technical_environment=:technical_environment, platform_components_json=:platform_components_json,
                source_material=:source_material, teaching_preferences=:teaching_preferences, assessment_preferences=:assessment_preferences,
                additional_notes=:additional_notes, requested_outputs_json=:requested_outputs_json, current_phase=:current_phase,
                status=:status, updated_at=:updated_at
            WHERE id=:id
            """,
            payload,
        )
        return int(project_id)
    payload["created_at"] = payload["updated_at"]
    return execute_returning_id(
        """
        INSERT INTO teacher_projects
        (teacher_username, project_name, domain, program_name, unit_title, target_concept, target_learners, learner_level,
         prerequisites, target_languages_json, primary_language, primary_language_code, expected_duration, technical_environment,
         platform_components_json, source_material, teaching_preferences, assessment_preferences, additional_notes,
         requested_outputs_json, current_phase, status, created_at, updated_at)
        VALUES
        (:teacher_username, :project_name, :domain, :program_name, :unit_title, :target_concept, :target_learners, :learner_level,
         :prerequisites, :target_languages_json, :primary_language, :primary_language_code, :expected_duration, :technical_environment,
         :platform_components_json, :source_material, :teaching_preferences, :assessment_preferences, :additional_notes,
         :requested_outputs_json, :current_phase, :status, :created_at, :updated_at)
        """ + (" RETURNING id" if dialect() != "sqlite" else ""),
        payload,
    )


def teacher_projects_df(teacher_username: str) -> pd.DataFrame:
    return query_df(
        "SELECT * FROM teacher_projects WHERE teacher_username=:username ORDER BY updated_at DESC, id DESC",
        {"username": str(teacher_username)},
    )


def get_teacher_project(project_id: int, teacher_username: str) -> Optional[Dict[str, Any]]:
    return query_one(
        "SELECT * FROM teacher_projects WHERE id=:id AND teacher_username=:username",
        {"id": int(project_id), "username": str(teacher_username)},
    )


def save_teacher_generation(
    project_id: int,
    phase_number: int,
    prompt_text: str,
    response_text: str,
    provider: str,
    model: str,
    status: str,
    diagnostic: str = "",
    *,
    latency_ms: int = 0,
    validation_status: str = "",
    is_fallback_used: bool = False,
) -> int:
    return execute_returning_id(
        """
        INSERT INTO teacher_generation_runs
        (project_id, phase_number, prompt_text, response_text, provider, model, status, diagnostic,
         latency_ms, validation_status, is_fallback_used, created_at)
        VALUES (:project_id, :phase_number, :prompt_text, :response_text, :provider, :model, :status, :diagnostic,
                :latency_ms, :validation_status, :is_fallback_used, :created_at)
        """ + (" RETURNING id" if dialect() != "sqlite" else ""),
        {
            "project_id": int(project_id),
            "phase_number": int(phase_number),
            "prompt_text": str(prompt_text),
            "response_text": str(response_text),
            "provider": str(provider),
            "model": str(model),
            "status": str(status),
            "diagnostic": str(diagnostic or ""),
            "latency_ms": int(latency_ms or 0),
            "validation_status": str(validation_status or ""),
            "is_fallback_used": 1 if is_fallback_used else 0,
            "created_at": utc_now(),
        },
    )


def save_teacher_research_run(
    project_id: int,
    phase_number: int,
    research_mode: str,
    query_plan_json: str,
    report_text: str,
    sources_json: str,
    provider: str,
    model: str,
    status: str,
    diagnostic: str = "",
    *,
    source_count: int = 0,
    latency_ms: int = 0,
    is_fallback_used: bool = False,
) -> int:
    """Persist a reusable web-research dossier for one production phase."""
    return execute_returning_id(
        """
        INSERT INTO teacher_research_runs
        (project_id, phase_number, research_mode, query_plan_json, report_text, sources_json,
         provider, model, status, diagnostic, source_count, latency_ms, is_fallback_used, created_at)
        VALUES (:project_id, :phase_number, :research_mode, :query_plan_json, :report_text, :sources_json,
                :provider, :model, :status, :diagnostic, :source_count, :latency_ms, :is_fallback_used, :created_at)
        """ + (" RETURNING id" if dialect() != "sqlite" else ""),
        {
            "project_id": int(project_id),
            "phase_number": int(phase_number),
            "research_mode": str(research_mode or "balanced"),
            "query_plan_json": str(query_plan_json or "[]"),
            "report_text": str(report_text or ""),
            "sources_json": str(sources_json or "[]"),
            "provider": str(provider or ""),
            "model": str(model or ""),
            "status": str(status or ""),
            "diagnostic": str(diagnostic or ""),
            "source_count": int(source_count or 0),
            "latency_ms": int(latency_ms or 0),
            "is_fallback_used": 1 if is_fallback_used else 0,
            "created_at": utc_now(),
        },
    )


def latest_teacher_research(project_id: int, phase_number: int) -> Optional[Dict[str, Any]]:
    return query_one(
        """
        SELECT * FROM teacher_research_runs
        WHERE project_id=:project_id AND phase_number=:phase_number
        ORDER BY id DESC LIMIT 1
        """,
        {"project_id": int(project_id), "phase_number": int(phase_number)},
    )


def teacher_research_runs_df(project_id: int, phase_number: Optional[int] = None) -> pd.DataFrame:
    if phase_number is None:
        return query_df(
            "SELECT * FROM teacher_research_runs WHERE project_id=:project_id ORDER BY id DESC",
            {"project_id": int(project_id)},
        )
    return query_df(
        """
        SELECT * FROM teacher_research_runs
        WHERE project_id=:project_id AND phase_number=:phase_number
        ORDER BY id DESC
        """,
        {"project_id": int(project_id), "phase_number": int(phase_number)},
    )


def save_teacher_evidence_bundle(
    project_id: int,
    phase_number: int,
    research_run_id: Optional[int],
    prompt_text: str,
    response_text: str,
    sources: Sequence[Dict[str, Any]],
    evidence_cards: Sequence[Dict[str, Any]],
    concepts: Sequence[Dict[str, Any]],
    quality: Dict[str, Any],
    provider: str,
    model: str,
    status: str,
    diagnostic: str = "",
    *,
    latency_ms: int = 0,
    is_fallback_used: bool = False,
) -> int:
    """Persist one normalized evidence-synthesis run and its child records."""
    run_id = execute_returning_id(
        """
        INSERT INTO teacher_evidence_runs
        (project_id, phase_number, research_run_id, prompt_text, response_text, provider, model, status,
         diagnostic, quality_json, source_count, evidence_card_count, concept_count, latency_ms,
         is_fallback_used, approved_by_teacher, approved_at, created_at)
        VALUES
        (:project_id, :phase_number, :research_run_id, :prompt_text, :response_text, :provider, :model, :status,
         :diagnostic, :quality_json, :source_count, :evidence_card_count, :concept_count, :latency_ms,
         :is_fallback_used, 0, NULL, :created_at)
        """ + (" RETURNING id" if dialect() != "sqlite" else ""),
        {
            "project_id": int(project_id),
            "phase_number": int(phase_number),
            "research_run_id": int(research_run_id) if research_run_id else None,
            "prompt_text": str(prompt_text or ""),
            "response_text": str(response_text or ""),
            "provider": str(provider or ""),
            "model": str(model or ""),
            "status": str(status or "needs_review"),
            "diagnostic": str(diagnostic or ""),
            "quality_json": json.dumps(quality or {}, ensure_ascii=False),
            "source_count": len(sources or []),
            "evidence_card_count": len(evidence_cards or []),
            "concept_count": len(concepts or []),
            "latency_ms": int(latency_ms or 0),
            "is_fallback_used": 1 if is_fallback_used else 0,
            "created_at": utc_now(),
        },
    )
    for source in sources or []:
        exec_sql(
            """
            INSERT INTO teacher_evidence_sources
            (evidence_run_id, source_id, title, url, canonical_url, domain, source_type, language,
             publication_date, access_date, snippet, authority_score, relevance_score, freshness_score,
             pedagogical_score, accessibility_score, license_score, composite_score, status, rationale, fingerprint)
            VALUES
            (:evidence_run_id, :source_id, :title, :url, :canonical_url, :domain, :source_type, :language,
             :publication_date, :access_date, :snippet, :authority_score, :relevance_score, :freshness_score,
             :pedagogical_score, :accessibility_score, :license_score, :composite_score, :status, :rationale, :fingerprint)
            """,
            {
                "evidence_run_id": int(run_id),
                "source_id": str(source.get("source_id") or ""),
                "title": str(source.get("title") or ""),
                "url": str(source.get("url") or ""),
                "canonical_url": str(source.get("canonical_url") or ""),
                "domain": str(source.get("domain") or ""),
                "source_type": str(source.get("source_type") or ""),
                "language": str(source.get("language") or "unknown"),
                "publication_date": str(source.get("publication_date") or "unknown"),
                "access_date": str(source.get("access_date") or ""),
                "snippet": str(source.get("snippet") or ""),
                "authority_score": float(source.get("authority_score") or 0),
                "relevance_score": float(source.get("relevance_score") or 0),
                "freshness_score": float(source.get("freshness_score") or 0),
                "pedagogical_score": float(source.get("pedagogical_score") or 0),
                "accessibility_score": float(source.get("accessibility_score") or 0),
                "license_score": float(source.get("license_score") or 0),
                "composite_score": float(source.get("composite_score") or 0),
                "status": str(source.get("status") or "review"),
                "rationale": str(source.get("rationale") or ""),
                "fingerprint": str(source.get("fingerprint") or ""),
            },
        )
    for card in evidence_cards or []:
        exec_sql(
            """
            INSERT INTO teacher_evidence_cards
            (evidence_run_id, evidence_id, claim_text, source_ids_json, evidence_excerpt,
             confidence, intended_use_json, review_status)
            VALUES (:evidence_run_id, :evidence_id, :claim_text, :source_ids_json, :evidence_excerpt,
                    :confidence, :intended_use_json, :review_status)
            """,
            {
                "evidence_run_id": int(run_id),
                "evidence_id": str(card.get("evidence_id") or ""),
                "claim_text": str(card.get("claim") or card.get("claim_text") or ""),
                "source_ids_json": json.dumps(card.get("source_ids") or [], ensure_ascii=False),
                "evidence_excerpt": str(card.get("evidence_excerpt") or ""),
                "confidence": str(card.get("confidence") or "moderate"),
                "intended_use_json": json.dumps(card.get("intended_use") or [], ensure_ascii=False),
                "review_status": str(card.get("review_status") or "pending"),
            },
        )
    for concept in concepts or []:
        exec_sql(
            """
            INSERT INTO teacher_evidence_concepts
            (evidence_run_id, concept_id, concept_name, description, prerequisites_json,
             source_ids_json, difficulty, review_status)
            VALUES (:evidence_run_id, :concept_id, :concept_name, :description, :prerequisites_json,
                    :source_ids_json, :difficulty, :review_status)
            """,
            {
                "evidence_run_id": int(run_id),
                "concept_id": str(concept.get("concept_id") or ""),
                "concept_name": str(concept.get("name") or concept.get("concept_name") or ""),
                "description": str(concept.get("description") or ""),
                "prerequisites_json": json.dumps(concept.get("prerequisites") or [], ensure_ascii=False),
                "source_ids_json": json.dumps(concept.get("source_ids") or [], ensure_ascii=False),
                "difficulty": str(concept.get("difficulty") or "introductory"),
                "review_status": str(concept.get("review_status") or "pending"),
            },
        )
    return int(run_id)


def teacher_evidence_bundle(run_id: int) -> Optional[Dict[str, Any]]:
    run = query_one("SELECT * FROM teacher_evidence_runs WHERE id=:id", {"id": int(run_id)})
    if not run:
        return None
    sources = query_df(
        "SELECT * FROM teacher_evidence_sources WHERE evidence_run_id=:id ORDER BY composite_score DESC, id ASC",
        {"id": int(run_id)},
    ).to_dict("records")
    cards = query_df(
        "SELECT * FROM teacher_evidence_cards WHERE evidence_run_id=:id ORDER BY id ASC",
        {"id": int(run_id)},
    ).to_dict("records")
    concepts = query_df(
        "SELECT * FROM teacher_evidence_concepts WHERE evidence_run_id=:id ORDER BY id ASC",
        {"id": int(run_id)},
    ).to_dict("records")
    for card in cards:
        try:
            card["source_ids"] = json.loads(card.get("source_ids_json") or "[]")
        except Exception:
            card["source_ids"] = []
        try:
            card["intended_use"] = json.loads(card.get("intended_use_json") or "[]")
        except Exception:
            card["intended_use"] = []
        card["claim"] = card.get("claim_text") or ""
    for concept in concepts:
        try:
            concept["prerequisites"] = json.loads(concept.get("prerequisites_json") or "[]")
        except Exception:
            concept["prerequisites"] = []
        try:
            concept["source_ids"] = json.loads(concept.get("source_ids_json") or "[]")
        except Exception:
            concept["source_ids"] = []
        concept["name"] = concept.get("concept_name") or ""
    try:
        quality = json.loads(run.get("quality_json") or "{}")
    except Exception:
        quality = {}
    run["sources"] = sources
    run["evidence_cards"] = cards
    run["concepts"] = concepts
    run["quality"] = quality
    return run


def latest_teacher_evidence(
    project_id: int,
    phase_number: int,
    *,
    approved_only: bool = False,
) -> Optional[Dict[str, Any]]:
    sql = """
        SELECT id FROM teacher_evidence_runs
        WHERE project_id=:project_id AND phase_number=:phase_number
    """
    if approved_only:
        sql += " AND approved_by_teacher=1"
    sql += " ORDER BY id DESC LIMIT 1"
    row = query_one(sql, {"project_id": int(project_id), "phase_number": int(phase_number)})
    return teacher_evidence_bundle(int(row["id"])) if row else None


def teacher_evidence_runs_df(project_id: int, phase_number: Optional[int] = None) -> pd.DataFrame:
    if phase_number is None:
        return query_df(
            "SELECT * FROM teacher_evidence_runs WHERE project_id=:project_id ORDER BY id DESC",
            {"project_id": int(project_id)},
        )
    return query_df(
        """
        SELECT * FROM teacher_evidence_runs
        WHERE project_id=:project_id AND phase_number=:phase_number
        ORDER BY id DESC
        """,
        {"project_id": int(project_id), "phase_number": int(phase_number)},
    )


def approve_teacher_evidence_run(run_id: int, project_id: int, teacher_username: str) -> None:
    project = get_teacher_project(int(project_id), str(teacher_username))
    if not project:
        raise ValueError("Teacher project not found or access denied")
    run = query_one(
        "SELECT * FROM teacher_evidence_runs WHERE id=:id AND project_id=:project_id",
        {"id": int(run_id), "project_id": int(project_id)},
    )
    if not run:
        raise ValueError("Evidence synthesis run not found")
    if str(run.get("status") or "") == "error":
        raise ValueError("An evidence synthesis run with errors cannot be approved")
    exec_sql(
        """
        UPDATE teacher_evidence_runs
        SET approved_by_teacher=1, approved_at=:approved_at, status='approved'
        WHERE id=:id AND project_id=:project_id
        """,
        {"approved_at": utc_now(), "id": int(run_id), "project_id": int(project_id)},
    )
    exec_sql(
        "UPDATE teacher_projects SET updated_at=:updated_at WHERE id=:id AND teacher_username=:username",
        {"updated_at": utc_now(), "id": int(project_id), "username": str(teacher_username)},
    )


def set_teacher_project_phase(project_id: int, teacher_username: str, phase_number: int) -> None:
    """Advance or reposition a project phase with an ownership check."""
    phase = int(phase_number)
    if phase < 1 or phase > 11:
        raise ValueError("phase_number must be between 1 and 11")
    project = get_teacher_project(int(project_id), str(teacher_username))
    if not project:
        raise ValueError("Teacher project not found or access denied")
    exec_sql(
        """
        UPDATE teacher_projects
        SET current_phase=:phase, updated_at=:updated_at
        WHERE id=:id AND teacher_username=:username
        """,
        {
            "phase": phase,
            "updated_at": utc_now(),
            "id": int(project_id),
            "username": str(teacher_username),
        },
    )


def latest_teacher_generation(project_id: int) -> Optional[Dict[str, Any]]:
    return query_one(
        "SELECT * FROM teacher_generation_runs WHERE project_id=:project_id ORDER BY id DESC LIMIT 1",
        {"project_id": int(project_id)},
    )

def save_teacher_manual_revision(
    project_id: int,
    teacher_username: str,
    phase_number: int,
    response_text: str,
    *,
    source_run_id: Optional[int] = None,
) -> int:
    """Save a teacher-edited output as the accepted result for a phase."""
    project = get_teacher_project(int(project_id), str(teacher_username))
    if not project:
        raise ValueError("Teacher project not found or access denied")
    phase = int(phase_number)
    if phase < 1 or phase > 11:
        raise ValueError("phase_number must be between 1 and 11")
    clean = str(response_text or "").strip()
    if len(clean) < 100:
        raise ValueError("The reviewed output is too short to approve")

    params: Dict[str, Any] = {"project_id": int(project_id), "phase": phase}
    sql = (
        "SELECT * FROM teacher_generation_runs "
        "WHERE project_id=:project_id AND phase_number=:phase "
    )
    if source_run_id is not None:
        sql += "AND id=:run_id "
        params["run_id"] = int(source_run_id)
    sql += "ORDER BY id DESC LIMIT 1"
    source = query_one(sql, params) or {}
    run_id = save_teacher_generation(
        project_id=int(project_id),
        phase_number=phase,
        prompt_text=str(source.get("prompt_text") or "Teacher-authored revision"),
        response_text=clean,
        provider="teacher",
        model="manual-review",
        status="completed",
        diagnostic=f"Teacher-reviewed revision based on run #{int(source.get('id') or 0)}.",
        validation_status="teacher_approved",
        is_fallback_used=False,
    )
    current_phase = int(project.get("current_phase") or 1)
    if current_phase <= phase:
        set_teacher_project_phase(int(project_id), str(teacher_username), min(phase + 1, 11))
    else:
        exec_sql(
            "UPDATE teacher_projects SET updated_at=:updated_at WHERE id=:id AND teacher_username=:username",
            {"updated_at": utc_now(), "id": int(project_id), "username": str(teacher_username)},
        )
    return int(run_id)

def teacher_generation_runs_df(project_id: int) -> pd.DataFrame:
    return query_df(
        "SELECT * FROM teacher_generation_runs WHERE project_id=:project_id ORDER BY id DESC",
        {"project_id": int(project_id)},
    )



def set_teacher_project_status(project_id: int, teacher_username: str, status: str) -> None:
    """Update the lifecycle state of a teacher project with ownership checks."""
    clean_status = str(status or "draft").strip().lower()
    if clean_status not in {"draft", "review", "published", "archived"}:
        raise ValueError("Unsupported teacher project status")
    project = get_teacher_project(int(project_id), str(teacher_username))
    if not project:
        raise ValueError("Teacher project not found or access denied")
    if clean_status == "published":
        core = query_one(
            """
            SELECT id FROM teacher_generation_runs
            WHERE project_id=:project_id AND phase_number=3 AND status='completed'
            ORDER BY id DESC LIMIT 1
            """,
            {"project_id": int(project_id)},
        )
        if not core:
            raise ValueError("Phase 3 core educational content must be completed before publication")
    now = utc_now()
    published_at = now if clean_status == "published" else project.get("published_at")
    reviewed_at = now if clean_status in {"review", "published"} else project.get("reviewed_at")
    exec_sql(
        """
        UPDATE teacher_projects
        SET status=:status, published_at=:published_at, reviewed_at=:reviewed_at, updated_at=:updated_at
        WHERE id=:id AND teacher_username=:username
        """,
        {
            "status": clean_status,
            "published_at": published_at,
            "reviewed_at": reviewed_at,
            "updated_at": now,
            "id": int(project_id),
            "username": str(teacher_username),
        },
    )


def teacher_projects_with_progress_df(teacher_username: str) -> pd.DataFrame:
    """Return a teacher's projects with distinct completed production phases."""
    return query_df(
        """
        SELECT p.*,
               COUNT(DISTINCT CASE WHEN r.status='completed' THEN r.phase_number END) AS completed_phases,
               COUNT(r.id) AS generation_runs
        FROM teacher_projects p
        LEFT JOIN teacher_generation_runs r ON r.project_id=p.id
        WHERE p.teacher_username=:username
        GROUP BY p.id
        ORDER BY p.updated_at DESC, p.id DESC
        """,
        {"username": str(teacher_username)},
    )


def teacher_project_phase_outputs(
    project_id: int,
    *,
    prefer_completed: bool = True,
) -> Dict[int, Dict[str, Any]]:
    """Return one representative generation run for every project phase.

    Progress and learner previews must not regress when a later regeneration
    attempt fails. Therefore a completed run is preferred over a newer failed
    run for the same phase. Set ``prefer_completed=False`` to obtain the latest
    run regardless of status.
    """
    frame = teacher_generation_runs_df(int(project_id))
    outputs: Dict[int, Dict[str, Any]] = {}
    if frame.empty:
        return outputs
    rows = [row.to_dict() for _, row in frame.iterrows()]
    for row in rows:
        phase = int(row.get("phase_number") or 0)
        if not phase:
            continue
        current = outputs.get(phase)
        if current is None:
            outputs[phase] = row
            continue
        if prefer_completed:
            current_completed = str(current.get("status") or "") == "completed"
            row_completed = str(row.get("status") or "") == "completed"
            if row_completed and not current_completed:
                outputs[phase] = row
    return outputs

def published_teacher_projects_df() -> pd.DataFrame:
    """List public teacher-authored projects for the learner catalogue."""
    return query_df(
        """
        SELECT p.*,
               COUNT(DISTINCT CASE WHEN r.status='completed' THEN r.phase_number END) AS completed_phases
        FROM teacher_projects p
        LEFT JOIN teacher_generation_runs r ON r.project_id=p.id
        WHERE p.status='published'
        GROUP BY p.id
        ORDER BY COALESCE(p.published_at, p.updated_at) DESC, p.id DESC
        """
    )


def get_published_teacher_project(project_id: int) -> Optional[Dict[str, Any]]:
    return query_one(
        "SELECT * FROM teacher_projects WHERE id=:id AND status='published'",
        {"id": int(project_id)},
    )
