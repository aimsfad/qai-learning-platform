"""Database layer for the QAI Streamlit platform."""

from __future__ import annotations

import json
import os
import secrets as py_secrets
import string
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
import streamlit as st
from sqlalchemy import bindparam, create_engine, text
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
            prior_python_level INTEGER DEFAULT 1,
            prior_quantum_level INTEGER DEFAULT 0,
            password_hash TEXT,
            created_at {created_default},
            last_login_at {created_default},
            is_active INTEGER DEFAULT 1
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
    ensure_column("ai_interactions", "provider", "TEXT")
    ensure_column("ai_interactions", "model", "TEXT")
    ensure_column("ai_interactions", "diagnostic", "TEXT")
    ensure_column("ai_interactions", "latency_ms", "INTEGER")
    ensure_column("ai_interactions", "response_word_count", "INTEGER")
    ensure_column("ai_interactions", "student_input_language", "TEXT")
    ensure_column("ai_interactions", "response_language", "TEXT")
    ensure_column("ai_interactions", "error_type", "TEXT")
    ensure_column("ai_interactions", "is_fallback_used", "INTEGER DEFAULT 0")
    ensure_column("question_responses", "question_text", "TEXT")
    ensure_column("question_responses", "selected_answer", "TEXT")
    ensure_column("question_responses", "correct_answer", "TEXT")
    ensure_column("question_responses", "explanation", "TEXT")


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


def generate_code(prefix: str = "QAI") -> str:
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
) -> Dict[str, Any]:
    if not full_name.strip():
        raise ValueError("Full name is required.")
    password_hash = hash_password(password)
    code = participant_code or generate_code()
    student_id = execute_returning_id(
        """
        INSERT INTO students
        (participant_code, full_name, email, institution, academic_level, prior_python_level,
         prior_quantum_level, password_hash, created_at, last_login_at, is_active)
        VALUES
        (:participant_code, :full_name, :email, :institution, :academic_level, :prior_python_level,
         :prior_quantum_level, :password_hash, :created_at, NULL, 1)
        """ + (" RETURNING id" if dialect() != "sqlite" else ""),
        {
            "participant_code": code,
            "full_name": full_name.strip(),
            "email": email.strip().lower(),
            "institution": institution.strip(),
            "academic_level": academic_level,
            "prior_python_level": int(prior_python_level),
            "prior_quantum_level": int(prior_quantum_level),
            "password_hash": password_hash,
            "created_at": utc_now(),
        },
    )
    return get_student(student_id) or {"id": student_id, "participant_code": code}


def get_student(student_id: int) -> Optional[Dict[str, Any]]:
    return query_one("SELECT * FROM students WHERE id=:id", {"id": int(student_id)})


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


def set_student_active(student_id: int, is_active: bool) -> None:
    exec_sql("UPDATE students SET is_active=:active WHERE id=:id", {"active": 1 if is_active else 0, "id": student_id})


def save_test_attempt(student_id: int, attempt_type: str, answers: Dict[str, int], questions: Sequence[Any]) -> Dict[str, Any]:
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
    }
    d = dialect()
    if d == "sqlite":
        sql = """
        INSERT OR REPLACE INTO test_attempts
        (student_id, attempt_type, score, correct_count, total_count, answers_json, per_concept_json, created_at)
        VALUES
        (:student_id, :attempt_type, :score, :correct_count, :total_count, :answers_json, :per_concept_json, :created_at)
        """
    else:
        sql = """
        INSERT INTO test_attempts
        (student_id, attempt_type, score, correct_count, total_count, answers_json, per_concept_json, created_at)
        VALUES
        (:student_id, :attempt_type, :score, :correct_count, :total_count, :answers_json, :per_concept_json, :created_at)
        ON CONFLICT (student_id, attempt_type) DO UPDATE SET
        score=EXCLUDED.score, correct_count=EXCLUDED.correct_count, total_count=EXCLUDED.total_count,
        answers_json=EXCLUDED.answers_json, per_concept_json=EXCLUDED.per_concept_json, created_at=EXCLUDED.created_at
        """
    exec_sql(sql, payload)
    save_question_responses(student_id, attempt_type, answers, questions)
    return {"score": score, "correct_count": correct, "total_count": total, "per_concept": per_concept}



def save_question_responses(student_id: int, attempt_type: str, answers: Dict[str, int], questions: Sequence[Any]) -> None:
    """Store per-question responses for concept-level paper analysis."""
    exec_sql(
        "DELETE FROM question_responses WHERE student_id=:sid AND attempt_type=:attempt_type",
        {"sid": student_id, "attempt_type": attempt_type},
    )
    for q in questions:
        selected = int(answers.get(q.id, -1))
        selected_answer = q.options[selected] if 0 <= selected < len(q.options) else ""
        correct_answer = q.options[q.answer_index] if 0 <= q.answer_index < len(q.options) else ""
        exec_sql(
            """
            INSERT INTO question_responses
            (student_id, attempt_type, question_id, concept, question_text, selected_index,
             selected_answer, correct_index, correct_answer, is_correct, explanation, created_at)
            VALUES
            (:student_id, :attempt_type, :question_id, :concept, :question_text, :selected_index,
             :selected_answer, :correct_index, :correct_answer, :is_correct, :explanation, :created_at)
            """,
            {
                "student_id": student_id,
                "attempt_type": attempt_type,
                "question_id": q.id,
                "concept": q.concept,
                "question_text": q.question,
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
) -> None:
    exec_sql(
        """
        INSERT INTO ai_interactions
        (student_id, module, concept, task, prompt, response, mode, provider, model, diagnostic,
         latency_ms, response_word_count, student_input_language, response_language, error_type,
         is_fallback_used, created_at)
        VALUES
        (:student_id, :module, :concept, :task, :prompt, :response, :mode, :provider, :model, :diagnostic,
         :latency_ms, :response_word_count, :student_input_language, :response_language, :error_type,
         :is_fallback_used, :created_at)
        """,
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
            "created_at": utc_now(),
        },
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


def save_survey(student_id: int, responses: Dict[str, int], open_feedback: Dict[str, str]) -> None:
    payload = {
        "student_id": student_id,
        "responses_json": json.dumps(responses),
        "open_feedback_json": json.dumps(open_feedback),
        "created_at": utc_now(),
    }
    if dialect() == "sqlite":
        sql = """
        INSERT OR REPLACE INTO survey_responses
        (student_id, responses_json, open_feedback_json, created_at)
        VALUES (:student_id, :responses_json, :open_feedback_json, :created_at)
        """
    else:
        sql = """
        INSERT INTO survey_responses
        (student_id, responses_json, open_feedback_json, created_at)
        VALUES (:student_id, :responses_json, :open_feedback_json, :created_at)
        ON CONFLICT (student_id) DO UPDATE SET
        responses_json=EXCLUDED.responses_json, open_feedback_json=EXCLUDED.open_feedback_json, created_at=EXCLUDED.created_at
        """
    exec_sql(sql, payload)


def get_survey(student_id: int) -> Optional[Dict[str, Any]]:
    return query_one("SELECT * FROM survey_responses WHERE student_id=:sid", {"sid": student_id})


def students_df(limit: Optional[int] = None) -> pd.DataFrame:
    sql = """
        SELECT id, participant_code, full_name, email, institution, academic_level,
               prior_python_level, prior_quantum_level, created_at, last_login_at, is_active
        FROM students
        ORDER BY created_at DESC
    """
    params: Dict[str, Any] = {}
    if limit is not None:
        sql += " LIMIT :limit"
        params["limit"] = int(limit)
    return query_df(sql, params)


def count_rows(table: str) -> int:
    allowed = {"students", "test_attempts", "survey_responses", "ai_interactions", "events_log", "consent_records", "lesson_progress"}
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
               a.error_type, a.is_fallback_used
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

