from __future__ import annotations

import io
import json
import secrets as py_secrets
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

import content
import db
import feedback_engine
from security import hash_password, verify_password
from media_utils import render_image, render_video

APP_DIR = Path(__file__).resolve().parent
LESSON_MEDIA_DIR = APP_DIR / "assets" / "lesson_media"

LESSON_MEDIA = {
    "orientation": {
        "image": "orientation_professional.png",
        "video": "orientation_microvideo.mp4",
        "caption": "Code-to-circuit map: qubit wire, measurement symbol, and classical output bit.",
        "notice": "Follow the code, then the visual circuit, then the classical output. This makes the quantum/classical boundary visible.",
        "resource_label": "IBM Quantum Learning",
        "resource_url": "https://quantum.cloud.ibm.com/learning/en",
    },
    "qubit_measurement": {
        "image": "measurement_professional.png",
        "video": "measurement_microvideo.mp4",
        "caption": "Measurement transforms a prepared quantum state into one classical outcome per shot.",
        "notice": "The important transition is not from code to printout, but from quantum state to classical data.",
        "resource_label": "IBM Quantum documentation: visualization",
        "resource_url": "https://quantum.cloud.ibm.com/docs/en/api/qiskit/visualization",
    },
    "hadamard_superposition": {
        "image": "hadamard_professional.png",
        "video": "hadamard_microvideo.mp4",
        "caption": "Hadamard prepares a balanced probability pattern; the histogram reveals it after repeated shots.",
        "notice": "Compare the state before H, the state after H, and the approximate 50/50 counts after measurement.",
        "resource_label": "Bloch sphere explanation",
        "resource_url": "https://qiskit.qotlabs.org/learning/courses/general-formulation-of-quantum-information/density-matrices/bloch-sphere",
    },
    "shots_counts": {
        "image": "counts_professional.png",
        "video": "counts_microvideo.mp4",
        "caption": "Counts are sampled frequencies. More shots generally make the distribution clearer.",
        "notice": "Compare 10 shots with 1000 shots: both are samples, but one is much easier to interpret.",
        "resource_label": "Qiskit guide: visualize results",
        "resource_url": "https://qiskit.qotlabs.org/docs/guides/visualize-results",
    },
    "cnot_correlation": {
        "image": "cnot_professional.png",
        "video": "cnot_microvideo.mp4",
        "caption": "CNOT uses a control and a target; with H it can produce correlated two-bit outcomes.",
        "notice": "Use the rule table before interpreting the two-qubit histogram. The target flips only when the control is 1.",
        "resource_label": "Microsoft Quantum Katas",
        "resource_url": "https://quantum.microsoft.com/en-us/tools/quantum-katas",
    },
    "qiskit_debugging": {
        "image": "debugging_professional.png",
        "video": "debugging_microvideo.mp4",
        "caption": "Debugging starts with resources: qubits, classical bits, and measurement indices.",
        "notice": "The incorrect code does not allocate a classical bit; the corrected version does.",
        "resource_label": "Qiskit documentation",
        "resource_url": "https://qiskit.qotlabs.org/docs/guides/construct-circuits",
    },
}

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def current_app_base_url() -> str:
    """Return the public URL used in password reset emails."""
    base = secret("APP_BASE_URL", "").strip().rstrip("/")
    if base:
        return base
    # Fallback is useful for local testing; set APP_BASE_URL in Streamlit Cloud for production.
    return "http://localhost:8501"


def smtp_is_configured() -> bool:
    return bool(secret("SMTP_HOST", "").strip() and secret("SMTP_USERNAME", "").strip() and secret("SMTP_PASSWORD", "").strip())


def send_password_reset_email(to_email: str, full_name: str, reset_link: str, expires_minutes: int = 30) -> Tuple[bool, str]:
    """Send a one-time password reset link using SMTP settings from Streamlit secrets."""
    host = secret("SMTP_HOST", "").strip()
    port = int(secret("SMTP_PORT", "587") or 587)
    username = secret("SMTP_USERNAME", "").strip()
    password = secret("SMTP_PASSWORD", "").strip()
    sender = secret("SMTP_FROM", username).strip() or username
    use_ssl = secret("SMTP_USE_SSL", "false").strip().lower() in {"1", "true", "yes"}

    if not (host and username and password and sender):
        return False, "SMTP email is not configured."

    msg = EmailMessage()
    msg["Subject"] = "QAI platform password reset"
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(
        f"Hello {full_name},\n\n"
        "We received a request to reset your password for the QAI Learning Evaluation Platform.\n\n"
        f"Reset your password using this link:\n{reset_link}\n\n"
        f"This link is valid for {expires_minutes} minutes and can be used only once.\n"
        "If you did not request this reset, you can ignore this email.\n\n"
        "QAI Learning Evaluation Platform"
    )

    try:
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context, timeout=20) as server:
                server.login(username, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(username, password)
                server.send_message(msg)
        return True, "sent"
    except Exception as exc:
        return False, str(exc)


def get_query_param(name: str) -> str:
    try:
        value = st.query_params.get(name, "")
        if isinstance(value, list):
            return str(value[0]) if value else ""
        return str(value or "")
    except Exception:
        try:
            params = st.experimental_get_query_params()
            values = params.get(name, [""])
            return str(values[0]) if values else ""
        except Exception:
            return ""


def clear_reset_token_from_url() -> None:
    try:
        if "reset_token" in st.query_params:
            del st.query_params["reset_token"]
    except Exception:
        try:
            st.experimental_set_query_params()
        except Exception:
            pass


def init_state() -> None:
    defaults = {
        "role": None,
        "student_id": None,
        "student_page": "Student Home",
        "student_access_page": "Sign in",
        "evaluator_logged_in": False,
        "evaluator_page": "Evaluator Dashboard",
        "last_tutor_result": None,
        "new_participant_code": None,
        "current_lesson_id": None,
        "last_ai_interaction_id": None,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def switch_role(role: Optional[str] = None) -> None:
    st.session_state.role = role
    st.session_state.student_page = "Student Home"
    st.session_state.student_access_page = "Sign in"
    st.session_state.evaluator_page = "Evaluator Dashboard"
    st.rerun()


def set_student_page(page: str) -> None:
    st.session_state.student_page = page
    st.rerun()


def set_evaluator_page(page: str) -> None:
    st.session_state.evaluator_page = page
    st.rerun()


def hero(title: str, subtitle: str) -> None:
    st.markdown(f"""
    <div class="qai-hero">
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def card(title: str, body: str, pill: Optional[str] = None) -> None:
    pill_html = f'<span class="qai-pill">{pill}</span>' if pill else ""
    st.markdown(f"""
    <div class="qai-card">
      {pill_html}
      <h3>{title}</h3>
      <p>{body}</p>
    </div>
    """, unsafe_allow_html=True)


def ux_note(text: str) -> None:
    st.markdown(f"<div class='qai-ux-note'>{text}</div>", unsafe_allow_html=True)


def interactive_note(text: str) -> None:
    st.markdown(f"<div class='qai-interactive'>{text}</div>", unsafe_allow_html=True)


def render_self_eval_scale_help() -> None:
    st.markdown("""
    <div class='qai-scale-box'>
      <b>How to choose the 0–3 level:</b><br>
      <b>0</b> = No prior knowledge.<br>
      <b>1</b> = Basic awareness: I have heard about it, but I cannot explain it well.<br>
      <b>2</b> = Some understanding: I can explain basic ideas with help.<br>
      <b>3</b> = Good understanding: I can apply or explain it confidently.
    </div>
    """, unsafe_allow_html=True)


def current_student() -> Optional[Dict[str, Any]]:
    sid = st.session_state.get("student_id")
    if not sid:
        return None
    return db.get_student(int(sid))


def student_profile(student: Dict[str, Any]) -> Dict[str, Any]:
    pre = db.get_test_attempt(student["id"], "pre")
    rec = db.get_recommendation(student["id"])
    progress = db.get_lesson_progress(student["id"])
    return {
        "participant_code": student.get("participant_code"),
        "academic_level": student.get("academic_level"),
        "prior_python_level": student.get("prior_python_level"),
        "prior_quantum_level": student.get("prior_quantum_level"),
        "pre_test_score": pre.get("score") if pre else None,
        "weak_concepts": rec.get("weak_concepts") if rec else [],
        "recommended_lessons": rec.get("recommended_lessons") if rec else [],
        "completed_lessons": progress[progress["completed"] == 1]["lesson_id"].tolist() if not progress.empty else [],
    }


def test_is_done(student_id: int, kind: str) -> bool:
    return db.get_test_attempt(student_id, kind) is not None


def all_lessons_done(student_id: int) -> bool:
    progress = db.get_lesson_progress(student_id)
    if progress.empty:
        return False
    done = set(progress[progress["completed"] == 1]["lesson_id"].tolist())
    return all(lesson["id"] in done for lesson in content.LESSONS)


def has_minimum_ai_interaction(student_id: int) -> bool:
    return db.ai_interaction_count(student_id) >= 1


def has_minimum_lesson_activity(student_id: int) -> bool:
    """Return True once the learner has completed at least one reflective lesson activity.

    The pilot protocol treats one completed learning activity as the minimum
    exposure condition. Requiring all lessons before the post-test increased
    attrition and made the workflow feel blocked for novice learners.
    """
    progress = db.get_lesson_progress(student_id)
    if progress.empty:
        return False
    return int((progress["completed"] == 1).sum()) >= 1


def lesson_completion_count(student_id: int) -> int:
    progress = db.get_lesson_progress(student_id)
    if progress.empty:
        return 0
    return int((progress["completed"] == 1).sum())




def required_lesson_count_for_posttest() -> int:
    """Return the number of learning modules required before unlocking the post-test.

    v6.1 introduced a stricter learning workflow, but the helper was missing
    from app.py. Keeping it as a dedicated function makes the rule easy to
    adjust later if the study protocol changes.
    """
    return len(content.LESSONS)


def learning_path_ready_for_posttest(student_id: int) -> bool:
    """Return True only when the required learning path has been completed."""
    return lesson_completion_count(student_id) >= required_lesson_count_for_posttest()


def has_research_consent(student_id: int) -> bool:
    return db.has_consent(student_id)


def render_participant_code_box(code: str) -> None:
    st.markdown("<div class='qai-warn'><b>Important:</b> Save your participant code now. You will need it if you return later. Do not create a second account.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='qai-code-badge'>{code}</div>", unsafe_allow_html=True)
    st.code(code, language=None)
    st.caption("Tip: copy the code to your notes or take a screenshot before continuing.")


def completion_items(student: Dict[str, Any]) -> List[tuple[str, bool, str]]:
    sid = student["id"]
    lesson_count = lesson_completion_count(sid)
    required_lessons = required_lesson_count_for_posttest()
    return [
        ("1. Consent", has_research_consent(sid), "Read and confirm the study notice"),
        ("2. Pre-test", test_is_done(sid, "pre"), "Answer the initial questions"),
        ("3. Learning path", lesson_count >= required_lessons, f"Complete all learning modules ({lesson_count}/{required_lessons})"),
        ("4. AI Tutor", has_minimum_ai_interaction(sid), "Ask the tutor at least once inside a module or in the AI lab"),
        ("5. Post-test", test_is_done(sid, "post"), "Unlocked after completing the learning path"),
        ("6. Survey", db.get_survey(sid) is not None, "Submit usability feedback"),
    ]


def next_action_text(student: Dict[str, Any]) -> str:
    page = next_student_page(student)
    messages = {
        "Research Notice": "Next: read and confirm the research notice.",
        "Pre-test": "Next: complete the pre-test. Do not worry about the score; it only helps personalize the learning path.",
        "Adaptive Plan": "Next: review your adaptive learning plan, then start the recommended learning section.",
        "Learning Module": "Next: continue the learning path and complete the remaining module reflections.",
        "AI Tutor Lab": "Next: ask the AI Tutor at least one question about a concept you found difficult.",
        "Post-test": "Next: complete the post-test after finishing all learning modules.",
        "Satisfaction Survey": "Next: submit the short satisfaction survey.",
        "Student Home": "All required stages are complete. Thank you for participating.",
    }
    return messages.get(page, "Continue to the next required step.")



def lesson_completion_status(student_id: int) -> Dict[str, bool]:
    progress = db.get_lesson_progress(student_id)
    if progress.empty:
        return {lesson["id"]: False for lesson in content.LESSONS}
    completed = set(progress[progress["completed"] == 1]["lesson_id"].tolist())
    return {lesson["id"]: lesson["id"] in completed for lesson in content.LESSONS}


def first_incomplete_lesson_id(student_id: int) -> str:
    status = lesson_completion_status(student_id)
    for lesson in content.LESSONS:
        if not status.get(lesson["id"], False):
            return lesson["id"]
    return content.LESSONS[-1]["id"]


def current_or_resume_lesson_id(student_id: int) -> str:
    current = st.session_state.get("current_lesson_id")
    valid_ids = {lesson["id"] for lesson in content.LESSONS}
    if current in valid_ids:
        return current
    last = db.get_last_open_lesson(student_id)
    if last in valid_ids:
        st.session_state.current_lesson_id = last
        return last
    lesson_id = first_incomplete_lesson_id(student_id)
    st.session_state.current_lesson_id = lesson_id
    return lesson_id


def set_current_lesson(student_id: int, lesson_id: str) -> None:
    st.session_state.current_lesson_id = lesson_id
    db.log_event(student_id, "student", "open_module", lesson_id)


def render_student_top_progress(student: Dict[str, Any], page: str) -> None:
    items = completion_items(student)
    done_count = sum(1 for _, ok, _ in items if ok)
    lesson_count = lesson_completion_count(student["id"])
    required_lessons = required_lesson_count_for_posttest()
    current_lesson = current_or_resume_lesson_id(student["id"]) if test_is_done(student["id"], "pre") else "not started"
    lesson_title = next((l.get("short_title", l["title"]) for l in content.LESSONS if l["id"] == current_lesson), "Learning not started")
    next_action = next_action_text(student)
    study_percent = int(round((done_count / len(items)) * 100)) if items else 0
    learning_percent = int(round((lesson_count / max(required_lessons, 1)) * 100))
    st.markdown(
        f"""
        <div class='qai-sticky-progress'>
          <div class='qai-sticky-title'>QAI guided study · {study_percent}% study workflow · {learning_percent}% learning path</div>
          <div class='qai-sticky-meta'>Current page: <b>{page}</b> · Completed modules: <b>{lesson_count}/{required_lessons}</b> · Resume: <b>{lesson_title}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(lesson_count / max(required_lessons, 1), text=next_action)


def render_completion_requirements(student: Dict[str, Any], compact: bool = False) -> None:
    items = completion_items(student)
    done_count = sum(1 for _, ok, _ in items if ok)
    st.markdown("<div class='qai-roadmap'><div class='qai-roadmap-title'>Study roadmap</div>", unsafe_allow_html=True)
    st.progress(done_count / len(items), text=f"Required workflow progress: {done_count}/{len(items)}")
    st.markdown(f"<div class='qai-next-action'><b>{next_action_text(student)}</b></div>", unsafe_allow_html=True)
    if compact:
        st.markdown("</div>", unsafe_allow_html=True)
        return
    cols = st.columns(3)
    for idx, (label, ok, detail) in enumerate(items):
        klass = "qai-step-done" if ok else "qai-step-pending"
        value = "Done" if ok else detail
        icon = "✅" if ok else "⬜"
        with cols[idx % 3]:
            st.markdown(
                f"<div class='qai-step {klass}'><div class='qai-step-title'>{icon} {label}</div><div class='qai-step-value'>{value}</div></div>",
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)
    if done_count == len(items):
        st.success("This participation is complete for analysis.")
    else:
        st.caption("Tip: use the Continue button on the Student Home page whenever you are unsure what to do next.")


def render_status_badge(target=st) -> None:
    status = feedback_engine.provider_status()
    if status["provider"] in ("gemini", "openai", "groq") and status["available"]:
        target.success(f"AI tutor: {status['provider']} mode ({status['model']})")
    else:
        target.info("AI tutor: local fallback mode")


def evaluator_password_is_valid(username: str, password: str) -> bool:
    expected_user = secret("EVALUATOR_USERNAME", "evaluator")
    if username.strip() != expected_user:
        return False
    stored_hash = secret("EVALUATOR_PASSWORD_HASH", "").strip()
    if stored_hash:
        return verify_password(password, stored_hash)
    return password == secret("ADMIN_PASSWORD", "admin123")


def registration_code_required() -> str:
    return secret("REGISTRATION_ACCESS_CODE", "").strip()


def to_excel_bytes(dfs: Dict[str, pd.DataFrame]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in dfs.items():
            clean_name = sheet_name[:31]
            df.to_excel(writer, sheet_name=clean_name, index=False)
    return output.getvalue()


def log_tutor_interaction(
    student_id: int,
    module: str,
    concept: str,
    task: str,
    prompt: str,
    tutor: Any,
    lesson_id: str = "",
    activity_id: str = "",
    selected_text: str = "",
) -> Optional[int]:
    interaction_id = db.log_ai_interaction(
        student_id,
        module,
        concept,
        task,
        prompt,
        tutor.response,
        tutor.mode,
        tutor.provider,
        tutor.model,
        tutor.diagnostic,
        latency_ms=getattr(tutor, "latency_ms", None),
        response_word_count=getattr(tutor, "response_word_count", None),
        student_input_language=getattr(tutor, "student_input_language", ""),
        response_language=getattr(tutor, "response_language", ""),
        error_type=getattr(tutor, "error_type", ""),
        is_fallback_used=getattr(tutor, "is_fallback_used", 0),
        lesson_id=lesson_id,
        activity_id=activity_id,
        selected_text=selected_text,
    )
    try:
        db.log_event(student_id, "student", "ai_response_received", f"{module}|{concept}|{task}|interaction_id={interaction_id}")
    except Exception:
        pass
    return interaction_id


def render_ai_usefulness_feedback(interaction_id: Optional[int], key_prefix: str) -> None:
    if not interaction_id:
        return
    st.markdown("<div class='qai-inline-ai'><b>Was this AI response useful for your learning?</b><br><span class='qai-small-muted'>This helps the evaluator assess the pedagogical quality of AI support.</span></div>", unsafe_allow_html=True)
    rating = st.select_slider(
        "Usefulness rating",
        options=[1, 2, 3, 4, 5],
        value=4,
        format_func=lambda x: {1: "1 - Not useful", 2: "2", 3: "3 - Acceptable", 4: "4", 5: "5 - Very useful"}[x],
        key=f"{key_prefix}_rating_{interaction_id}",
    )
    comment = st.text_input("Optional short comment", key=f"{key_prefix}_comment_{interaction_id}")
    if st.button("Save AI usefulness rating", key=f"{key_prefix}_save_{interaction_id}"):
        db.update_ai_student_feedback(interaction_id, int(rating), comment)
        db.log_event(None, "student", "student_ai_rating", f"interaction_id={interaction_id}; rating={rating}")
        st.success("AI usefulness rating saved.")


def render_progress_bars(df: pd.DataFrame, label_col: str, value_col: str, title: str = "") -> None:
    """Render lightweight progress bars without st.bar_chart.

    Some Python/Streamlit/Altair combinations can fail inside st.bar_chart;
    these HTML/progress bars are more stable for local and cloud deployment.
    """
    if df is None or df.empty or label_col not in df.columns or value_col not in df.columns:
        return
    if title:
        st.markdown(f"#### {title}")
    view = df[[label_col, value_col]].copy()
    view[value_col] = pd.to_numeric(view[value_col], errors="coerce").fillna(0)
    max_value = float(view[value_col].max()) if len(view) else 0.0
    max_value = max(max_value, 1.0)
    for _, row in view.iterrows():
        label = str(row[label_col])
        value = float(row[value_col])
        st.caption(f"{label}: {value:g}")
        st.progress(min(max(value / max_value, 0.0), 1.0))

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------

def render_sidebar(target=st) -> None:
    role = st.session_state.get("role")
    # Use both plain Streamlit text and CSS-styled HTML so the sidebar remains visible
    # even if custom CSS fails to load on Streamlit Cloud.
    target.markdown("<div class='qai-side-brand'>QAI Learning Platform</div>", unsafe_allow_html=True)
    target.caption("Guided quantum programming study with contextual AI support.")
    target.divider()

    if role == "student":
        student = current_student()
        if student:
            lesson_count = lesson_completion_count(student["id"])
            required_lessons = required_lesson_count_for_posttest()
            learning_pct = int(round(100 * lesson_count / max(required_lessons, 1)))
            current_id = current_or_resume_lesson_id(student["id"]) if test_is_done(student["id"], "pre") else None
            current_title = next((l.get("short_title", l["title"]) for l in content.LESSONS if l["id"] == current_id), "Not started")
            target.markdown(
                f"""
                <div class='qai-side-profile'>
                  <div class='qai-side-code'>Student · {student['participant_code']}</div>
                  <div class='qai-side-progress-label'><span>Learning path</span><b>{lesson_count}/{required_lessons}</b></div>
                  <div class='qai-side-bar'><div class='qai-side-fill' style='width:{learning_pct}%;'></div></div>
                  <div style='font-size:0.78rem;color:#64748b;'>Current module: <b>{current_title}</b></div>
                </div>
                <div class='qai-side-next'><b>Next step</b><br>{next_action_text(student)}</div>
                """,
                unsafe_allow_html=True,
            )
        else:
            target.markdown("<div class='qai-side-profile'><b>No student signed in</b><br><span style='color:#64748b;font-size:0.8rem;'>Create an account or sign in to start the study.</span></div>", unsafe_allow_html=True)

        allowed = student_pages_allowed(student)
        current_page = st.session_state.get("student_page", "Student Home")
        nav_items = [
            ("Student Home", "Dashboard", "Overview and next action"),
            ("Research Notice", "Research notice", "Consent step"),
            ("Pre-test", "Pre-test", "Initial knowledge check"),
            ("Learning Module", "Learning path", "Six guided modules"),
            ("AI Tutor Lab", "AI tutor", "Ask for hints and explanations"),
            ("Post-test", "Post-test", "Unlocked after learning path"),
            ("Satisfaction Survey", "Survey", "Final feedback"),
        ]
        target.markdown("<div class='qai-side-section'>Student navigation</div>", unsafe_allow_html=True)
        if student and target.button("▶ Resume recommended step", key="student_resume_step", type="primary", use_container_width=True):
            st.session_state.student_page = next_student_page(student)
            st.rerun()
        if not student:
            for page, label, _ in [("Sign in", "Sign in", ""), ("Create account", "Create account", "")]:
                prefix = "● " if current_page == page else ""
                if target.button(prefix + label, key=f"student_nav_{page}", use_container_width=True):
                    st.session_state.student_page = page
                    st.rerun()
        else:
            for page, label, detail in nav_items:
                if page in allowed:
                    prefix = "● " if current_page == page else ""
                    if target.button(prefix + label, key=f"student_nav_{page}", use_container_width=True):
                        st.session_state.student_page = page
                        st.rerun()
                    if current_page == page:
                        target.markdown(f"<div class='qai-side-active-note'>{detail}</div>", unsafe_allow_html=True)
                else:
                    if page in {"Post-test", "Satisfaction Survey"}:
                        target.markdown(f"<div class='qai-side-lock'>Locked · {label} · {detail}</div>", unsafe_allow_html=True)
        target.divider()
        if student and target.button("Sign out", use_container_width=True):
            db.log_event(student["id"], "student", "sign_out", "Student signed out from sidebar")
            st.session_state.student_id = None
            st.session_state.student_page = "Student Home"
            st.session_state.student_access_page = "Sign in"
            st.rerun()
        if target.button("Switch workspace", use_container_width=True):
            switch_role(None)
        target.markdown("<div class='qai-side-footer'>AI tutor interactions and progress events are logged for the evaluator dashboard.</div>", unsafe_allow_html=True)
        render_status_badge(target)

    elif role == "evaluator":
        target.markdown("<div class='qai-side-profile'><b>Evaluator workspace</b><br><span style='color:#64748b;font-size:0.8rem;'>Monitor progress, AI usage, and exports.</span></div>", unsafe_allow_html=True)
        if st.session_state.evaluator_logged_in:
            pages = [
                "Evaluator Dashboard",
                "Students",
                "Registration Accounts",
                "Student Details",
                "AI Tutor Logs",
                "AI Response Evaluation",
                "AI Metrics",
                "Exports",
            ]
            compact_labels = {
                "Evaluator Dashboard": "Dashboard",
                "Registration Accounts": "Accounts",
                "Student Details": "Student details",
                "AI Tutor Logs": "AI logs",
                "AI Response Evaluation": "Response evaluation",
                "AI Metrics": "AI metrics",
            }
            target.markdown("<div class='qai-side-section'>Evaluator navigation</div>", unsafe_allow_html=True)
            for page in pages:
                label_text = compact_labels.get(page, page)
                prefix = "● " if st.session_state.evaluator_page == page else ""
                if target.button(prefix + label_text, key=f"eval_nav_btn_{page}", use_container_width=True):
                    st.session_state.evaluator_page = page
                    st.rerun()
            target.divider()
            if target.button("Sign out", use_container_width=True):
                st.session_state.evaluator_logged_in = False
                st.session_state.evaluator_page = "Evaluator Dashboard"
                st.rerun()
        if target.button("Switch workspace", use_container_width=True):
            switch_role(None)
    else:
        target.info("Select Student workspace or Evaluator workspace from the main page to start.")


def student_pages_allowed(student: Optional[Dict[str, Any]]) -> List[str]:
    if not student:
        return ["Student Home", "Sign in", "Create account"]
    pages = ["Student Home"]
    if not has_research_consent(student["id"]):
        pages.append("Research Notice")
        return pages
    if not test_is_done(student["id"], "pre"):
        pages.append("Pre-test")
        return pages
    pages += ["Learning Module", "AI Tutor Lab"]
    if learning_path_ready_for_posttest(student["id"]) and has_minimum_ai_interaction(student["id"]):
        pages.append("Post-test")
    if test_is_done(student["id"], "post"):
        pages.append("Satisfaction Survey")
    return pages

# -----------------------------------------------------------------------------
# Landing and access
# -----------------------------------------------------------------------------

def render_role_selection() -> None:
    hero(
        "Quantum AI Learning Evaluation Platform",
        "Pilot platform for AI-supported introductory quantum programming with Qiskit."
    )

    ux_note(
        "<b>Please choose your workspace.</b><br>"
        "Students should use the Student workspace to complete the learning activities, AI tutor interaction, pre-test, post-test, and survey.<br>"
        "The Evaluator workspace is reserved for the researcher/teacher to monitor progress, review logs, and export anonymized research data."
    )

    col1, col2 = st.columns(2)
    with col1:
        card(
            "Student workspace",
            "Use this option if you are a participant. You will create an account or sign in, complete the learning workflow, interact with the AI tutor, and submit the final survey.",
            "For students"
        )
        if st.button("Enter as student", type="primary", use_container_width=True):
            switch_role("student")

    with col2:
        card(
            "Evaluator workspace",
            "Reserved for the professor/researcher. It is used to monitor participant progress, review pre/post-test results, inspect AI tutor logs, and export anonymized research data.",
            "For evaluator only"
        )
        st.caption("Students do not need to use this option.")
        if st.button("Enter as evaluator", use_container_width=True):
            switch_role("evaluator")

def render_student_app() -> None:
    reset_token = get_query_param("reset_token").strip()
    if reset_token:
        render_password_reset_form(reset_token)
        return
    student = current_student()
    page = st.session_state.student_page
    if page not in student_pages_allowed(student):
        st.session_state.student_page = "Student Home"
        page = "Student Home"
    if student and page not in {"Sign in", "Create account"}:
        render_student_top_progress(student, page)
    if page == "Student Home":
        render_student_home(student)
    elif page == "Sign in":
        render_student_signin()
    elif page == "Create account":
        render_student_registration()
    elif page == "Research Notice":
        require_student(render_research_notice)
    elif page == "Pre-test":
        require_student(render_test_page, "pre")
    elif page == "Adaptive Plan":
        require_student(render_adaptive_plan)
    elif page == "Learning Module":
        require_student(render_learning_module)
    elif page == "AI Tutor Lab":
        require_student(render_ai_tutor_lab)
    elif page == "Post-test":
        require_student(render_test_page, "post")
    elif page == "Satisfaction Survey":
        require_student(render_survey)


def require_student(func, *args) -> None:
    student = current_student()
    if not student:
        st.warning("Please sign in first.")
        if st.button("Go to sign in"):
            set_student_page("Sign in")
        return
    func(student, *args)


def render_student_home(student: Optional[Dict[str, Any]]) -> None:
    hero("Student Dashboard", "A guided quantum programming workspace with progress, contextual AI support, and research-grade learning analytics.")
    if not student:
        st.markdown("""
        <div class='qai-hero-grid'>
          <div class='qai-glass-card'>
            <div class='qai-module-kicker'>Guided pilot workflow</div>
            <div class='qai-module-title'>Learn Qiskit step by step</div>
            <p>The platform combines a structured learning path, short visual explanations, pre/post assessment, and an AI tutor that encourages reasoning rather than copy-paste answers.</p>
            <span class='qai-stage-chip'>6 modules</span><span class='qai-stage-chip'>AI tutor</span><span class='qai-stage-chip'>Progress tracking</span>
          </div>
          <div class='qai-glass-card'>
            <div class='qai-panel-title'>Recommended path</div>
            <ol>
              <li>Create or sign in to your account</li>
              <li>Complete the pre-test</li>
              <li>Follow the learning path</li>
              <li>Use the AI tutor when needed</li>
              <li>Complete the post-test and survey</li>
            </ol>
          </div>
        </div>
        """, unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            card("Sign in", "Use your participant code, email, or exact registered name with your password.", "Returning participant")
            if st.button("Sign in", type="primary", use_container_width=True):
                st.session_state.student_page = "Sign in"
                st.rerun()
        with c2:
            card("Create account", "Register as a study participant. If the study is protected, you will need the registration access code.", "New participant")
            if st.button("Create account", use_container_width=True):
                st.session_state.student_page = "Create account"
                st.rerun()
        return

    st.markdown(f"<div class='qai-ok'><b>Signed in:</b> {student['full_name']} ({student['participant_code']})</div>", unsafe_allow_html=True)
    if st.session_state.get("new_participant_code"):
        st.success("Account created successfully. Save your participant code before continuing.")
        render_participant_code_box(st.session_state["new_participant_code"])
        if st.button("I saved my participant code", type="primary"):
            st.session_state.new_participant_code = None
            st.session_state.student_page = next_student_page(student)
            st.rerun()
        return

    summary = db.progress_summary_df(len(content.LESSONS))
    row = summary[summary["student_id"] == student["id"]] if not summary.empty and "student_id" in summary.columns else pd.DataFrame()
    progress_percent = float(row["progress_percent"].iloc[0]) if not row.empty and "progress_percent" in row.columns else 0.0
    modules_done = lesson_completion_count(student["id"])
    ai_count = db.ai_interaction_count(student["id"])
    next_page = next_student_page(student)
    current_lesson_id = current_or_resume_lesson_id(student["id"]) if test_is_done(student["id"], "pre") else content.LESSONS[0]["id"]
    current_lesson = content.lesson_by_id(current_lesson_id)

    st.markdown(
        f"""
        <div class='qai-dashboard-grid'>
          <div class='qai-dashboard-tile'><div class='qai-tile-value'>{progress_percent:.0f}%</div><div class='qai-tile-label'>Overall study workflow</div></div>
          <div class='qai-dashboard-tile'><div class='qai-tile-value'>{modules_done}/{len(content.LESSONS)}</div><div class='qai-tile-label'>Learning modules completed</div></div>
          <div class='qai-dashboard-tile'><div class='qai-tile-value'>{ai_count}</div><div class='qai-tile-label'>AI tutor interactions recorded</div></div>
        </div>
        <div class='qai-learning-shell'>
          <div class='qai-module-kicker'>Resume point</div>
          <div class='qai-module-title'>{current_lesson.get('short_title', current_lesson['title'])}</div>
          <div class='qai-module-meta'>Next required action: <b>{next_action_text(student)}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(progress_percent / 100, text=f"Overall progress: {progress_percent:.0f}%")
    render_completion_requirements(student)

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(f"Continue: {next_page}", type="primary", use_container_width=True):
            st.session_state.student_page = next_page
            st.rerun()
    with c2:
        if st.button("Resume learning module", use_container_width=True, disabled=not test_is_done(student["id"], "pre")):
            st.session_state.student_page = "Learning Module"
            st.rerun()
    with c3:
        if st.button("AI Tutor Lab", use_container_width=True, disabled=not test_is_done(student["id"], "pre")):
            set_student_page("AI Tutor Lab")

    if st.button("Sign out", use_container_width=True):
        db.log_event(student["id"], "student", "sign_out", "Student signed out from home")
        st.session_state.student_id = None
        st.session_state.student_page = "Student Home"
        st.rerun()


def next_student_page(student: Dict[str, Any]) -> str:
    sid = student["id"]
    if not has_research_consent(sid):
        return "Research Notice"
    if not test_is_done(sid, "pre"):
        return "Pre-test"
    if db.get_recommendation(sid) is None:
        try:
            db.compute_adaptive_recommendation(sid, content.CONCEPT_TO_LESSONS)
        except Exception:
            pass
        return "Learning Module"
    if not learning_path_ready_for_posttest(sid):
        return "Learning Module"
    if not has_minimum_ai_interaction(sid):
        return "AI Tutor Lab"
    if not test_is_done(sid, "post"):
        return "Post-test"
    if db.get_survey(sid) is None:
        return "Satisfaction Survey"
    return "Student Home"


def render_research_notice(student: Dict[str, Any]) -> None:
    hero("Research Notice and Consent", "Please read this notice before continuing the study workflow.")
    if has_research_consent(student["id"]):
        st.success("Research notice already confirmed.")
        render_completion_requirements(student, compact=True)
        if st.button("Continue", type="primary"):
            st.session_state.student_page = next_student_page(student)
            st.rerun()
        return

    st.markdown("""
    <div class='qai-card'>
    <h3>Study notice</h3>
    <p>This platform is used for a pilot evaluation of AI-supported learning for introductory quantum programming.</p>
    <ul>
      <li>Your pre-test, post-test, learning progress, reflections, survey answers, and AI tutor interactions will be recorded for research analysis.</li>
      <li>Your participant code is used to organize the data. Avoid creating multiple accounts.</li>
      <li>AI tutor responses may be reviewed by the evaluator to assess conceptual accuracy, relevance, scaffolding, and feedback quality.</li>
      <li>The AI tutor is a learning support tool. It should not replace your own reasoning.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    agree = st.checkbox("I have read the study notice and agree to participate in this pilot evaluation.")
    if st.button("Confirm and continue", type="primary", disabled=not agree):
        consent_text = "Participant confirmed research notice and consented to recording learning data and AI tutor interactions."
        db.save_consent(student["id"], consent_text, consent_version="v2")
        db.log_event(student["id"], "student", "consent_confirmed", "Research notice confirmed")
        st.session_state.student_page = next_student_page(student)
        st.rerun()


def render_password_reset_request() -> None:
    st.markdown("#### Forgot your password?")
    st.caption("Enter the email address used during registration. If it exists in the study database, a reset link will be sent.")
    with st.form("password_reset_request_form"):
        email = st.text_input("Registered email", key="reset_email_request")
        submitted = st.form_submit_button("Send password reset link", use_container_width=True)
    if submitted:
        email_clean = email.strip().lower()
        if not email_clean or "@" not in email_clean:
            st.error("Please enter a valid email address.")
            return
        result = db.create_password_reset_token(email_clean, minutes_valid=30)
        # Avoid revealing whether the email exists.
        generic_msg = "If this email is registered, a password reset link will be sent shortly."
        if result:
            student, token, _expires_at = result
            reset_link = f"{current_app_base_url()}/?reset_token={token}"
            ok, diagnostic = send_password_reset_email(student.get("email", email_clean), student.get("full_name", "student"), reset_link)
            db.log_event(student["id"], "student", "password_reset_requested", "Password reset requested")
            if not ok:
                st.warning("Password reset was created, but email delivery is not configured or failed. Please contact the instructor.")
                if secret("SHOW_RESET_LINK_FOR_DEBUG", "false").strip().lower() in {"1", "true", "yes"}:
                    st.code(reset_link)
                return
        st.success(generic_msg)


def render_password_reset_form(token: str) -> None:
    hero("Reset Password", "Create a new password for your QAI platform account.")
    st.info("Please enter and confirm your new password. Reset links are valid for a limited time and can be used only once.")
    with st.form("password_reset_form"):
        new_password = st.text_input("New password", type="password")
        new_password2 = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Update password", type="primary", use_container_width=True)
    if submitted:
        if new_password != new_password2:
            st.error("Passwords do not match.")
            return
        ok, message = db.reset_student_password(token, new_password)
        if ok:
            st.success(message)
            clear_reset_token_from_url()
            st.session_state.role = "student"
            st.session_state.student_id = None
            st.session_state.student_page = "Sign in"
            st.info("You can now sign in using your email, participant code, or exact full name.")
            if st.button("Go to sign in", type="primary"):
                st.rerun()
        else:
            st.error(message)
            st.caption("If the link expired, request a new password reset from the sign-in page.")


def render_student_signin() -> None:
    hero("Student Sign in", "Access your existing participant account.")
    st.markdown("<div class='qai-card'>", unsafe_allow_html=True)
    with st.form("student_signin_form"):
        identifier = st.text_input("Participant code, email, or exact registered full name")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    with st.expander("Forgot password?", expanded=False):
        render_password_reset_request()
    if submitted:
        student = db.authenticate_student(identifier, password)
        if student:
            db.log_event(student["id"], "student", "sign_in", "Student signed in")
            st.session_state.student_id = student["id"]
            st.session_state.current_lesson_id = db.get_last_open_lesson(student["id"]) or first_incomplete_lesson_id(student["id"])
            st.session_state.student_page = next_student_page(student)
            st.success("Signed in successfully.")
            st.rerun()
        else:
            st.error("Invalid identifier or password.")


def render_student_registration() -> None:
    hero("Create Student Account", "Register as a participant before starting the pilot study.")
    access_required = registration_code_required()
    with st.form("student_register_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full name")
            email = st.text_input("Email")
            institution = st.text_input("Institution")
        with col2:
            academic_level = st.selectbox("Academic level", ["Licence", "Master", "PhD", "Other"])
            render_self_eval_scale_help()
            prior_python = st.slider(
                "Prior Python level",
                0, 3, 1,
                help="0 = no prior knowledge; 1 = basic awareness; 2 = some understanding; 3 = confident use."
            )
            prior_quantum = st.slider(
                "Prior quantum programming knowledge",
                0, 3, 0,
                help="0 = no prior knowledge; 1 = basic awareness; 2 = some understanding; 3 = confident use."
            )
        password = st.text_input("Password", type="password")
        password2 = st.text_input("Confirm password", type="password")
        study_code = ""
        if access_required:
            study_code = st.text_input("Study registration access code", type="password")
        st.markdown("#### Research notice")
        st.caption("Your learning data, pre/post-test results, reflections, survey answers, and AI tutor interactions will be recorded for research analysis. Please create only one account and save your participant code.")
        consent = st.checkbox("I have read the study notice and agree to participate in this pilot evaluation.")
        submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
    if submitted:
        try:
            if access_required and study_code.strip() != access_required:
                st.error("Invalid registration access code.")
                return
            if password != password2:
                st.error("Passwords do not match.")
                return
            if not consent:
                st.error("Please confirm the study notice before creating an account.")
                return
            student = db.create_student(full_name, email, institution, academic_level, prior_python, prior_quantum, password)
            consent_text = "Participant confirmed that answers and AI interactions may be recorded for the pilot evaluation."
            db.save_consent(student["id"], consent_text, consent_version="v1")
            db.log_event(student["id"], "student", "account_created", "Student created account and confirmed consent notice")
            st.session_state.student_id = student["id"]
            st.session_state.current_lesson_id = content.LESSONS[0]["id"]
            st.session_state.new_participant_code = student["participant_code"]
            st.session_state.student_page = "Student Home"
            st.success(f"Account created. Your participant code is: {student['participant_code']}")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not create account: {exc}")

# -----------------------------------------------------------------------------
# Student study flow
# -----------------------------------------------------------------------------

def render_test_page(student: Dict[str, Any], kind: str) -> None:
    title = "Pre-test" if kind == "pre" else "Post-test"
    subtitle = "Answer the questions individually. This is used to evaluate learning progress, not to grade you."
    hero(title, subtitle)
    if kind == "post" and not has_minimum_lesson_activity(student["id"]):
        st.warning("Please complete at least one learning section and save its reflection before the post-test.")
        if st.button("Go to learning module", type="primary"):
            set_student_page("Learning Module")
        return
    if kind == "post" and not has_minimum_ai_interaction(student["id"]):
        st.warning("Please complete at least one AI Tutor interaction before the post-test. This is required for the AI-supported learning evaluation.")
        if st.button("Go to AI Tutor Lab", type="primary"):
            set_student_page("AI Tutor Lab")
        return
    existing = db.get_test_attempt(student["id"], kind)
    if existing:
        st.success(f"{title} already submitted. Score: {existing['score']:.1f}%")
        if st.button("Continue", type="primary"):
            if kind == "pre":
                try:
                    db.compute_adaptive_recommendation(student["id"], content.CONCEPT_TO_LESSONS)
                except Exception:
                    pass
                st.session_state.student_page = "Learning Module"
            else:
                st.session_state.student_page = "Satisfaction Survey"
            st.rerun()
        return

    questions = content.questions_for(kind)
    with st.form(f"{kind}_test_form"):
        answers: Dict[str, int] = {}
        for i, q in enumerate(questions, start=1):
            st.markdown(f"**Q{i}. {q.question}**")
            answers[q.id] = st.radio(
                label="Choose one answer",
                options=list(range(len(q.options))),
                format_func=lambda idx, opts=q.options: opts[idx],
                key=f"{kind}_{q.id}",
                label_visibility="collapsed",
            )
            st.caption(f"Concept: {q.concept}")
            st.divider()
        submitted = st.form_submit_button(f"Submit {title}", type="primary", use_container_width=True)
    if submitted:
        result = db.save_test_attempt(student["id"], kind, answers, questions)
        if kind == "pre":
            db.compute_adaptive_recommendation(student["id"], content.CONCEPT_TO_LESSONS)
            db.log_event(student["id"], "student", "pre_test_submitted", f"Score: {result['score']:.1f}%")
        else:
            db.log_event(student["id"], "student", "post_test_submitted", f"Score: {result['score']:.1f}%")
        st.success(f"Submitted. Score: {result['score']:.1f}%")
        st.rerun()


def render_adaptive_plan(student: Dict[str, Any]) -> None:
    hero("Adaptive Learning Plan", "The platform uses your pre-test results to recommend learning sections and AI-supported practice.")
    if not test_is_done(student["id"], "pre"):
        st.warning("Complete the pre-test first.")
        return
    rec = db.get_recommendation(student["id"]) or db.compute_adaptive_recommendation(student["id"], content.CONCEPT_TO_LESSONS)
    weak = rec.get("weak_concepts", [])
    recommended = rec.get("recommended_lessons", [])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Concepts to reinforce")
        if weak:
            for concept in weak:
                st.markdown(f"- {concept}")
        else:
            st.markdown("No major weakness detected. Continue with the full learning sequence.")
    with c2:
        st.markdown("### Recommended lesson sequence")
        lesson_map = {lesson["id"]: lesson["title"] for lesson in content.LESSONS}
        for lesson_id in recommended:
            st.markdown(f"- {lesson_map.get(lesson_id, lesson_id)}")

    st.divider()
    plan_language = st.selectbox(
        "AI response language",
        ["Auto-detect", "English", "Arabic", "French"],
        index=1,
        key="adaptive_plan_language",
    )
    if st.button("Generate AI personalized study plan", type="primary"):
        profile = student_profile(student)
        tutor = feedback_engine.generate_tutor_response(
            task="Generate a personalized study plan",
            concept="Adaptive quantum programming learning",
            student_input="Generate a concise study plan based on the learner profile and weak concepts.",
            student_profile=profile,
            lesson_context={"recommended_lessons": recommended, "weak_concepts": weak, "response_language": plan_language},
        )
        log_tutor_interaction(
            student["id"], "adaptive_plan", "Adaptive learning", "Generate personalized study plan",
            "Generate a concise study plan based on pre-test results.", tutor,
        )
        st.markdown("### 📋 AI-generated study plan")
        ux_note(
            "<b>How to read this plan:</b><br>"
            "1. Start with the concepts listed as weak or recommended.<br>"
            "2. Complete the learning module before relying on the AI tutor.<br>"
            "3. Use the AI tutor for hints and explanations, not for copying final answers."
        )
        st.markdown("#### Personalized plan")
        st.write(tutor.response)
        interactive_note("Next interactive step: click “Start learning module” and complete at least one learning activity.")
        if tutor.mode == "llm_error":
            st.info("The LLM service was unavailable, so a local fallback was shown and logged for the evaluator.")
    if st.button("Start learning module →", type="primary", use_container_width=True):
        set_student_page("Learning Module")



def lesson_diagram_html(lesson_id: str) -> str:
    """Return a small text-based diagram for the concept instead of one crowded image."""
    diagrams = {
        "orientation": "Qiskit code\n  QuantumCircuit(1, 1)\n        ↓\nCircuit\n  q0 ── M ──\n        │\n  c0 ◄──0\n        ↓\nClassical output: {'0': shots}",
        "qubit_measurement": "Before measurement\n  qubit state: |0⟩ or α|0⟩ + β|1⟩\n        ↓ measurement\nAfter measurement\n  one classical result per shot: 0 or 1",
        "hadamard_superposition": "Start\n  |0⟩\n        ↓ H gate\nBefore measurement\n  (|0⟩ + |1⟩) / √2\n        ↓ many shots\nCounts\n  0 ≈ 50%   1 ≈ 50%",
        "shots_counts": "Run circuit once = one shot\n        ↓\nRun 10 shots → small noisy sample\n        ↓\nRun 1000 shots → clearer distribution\n        ↓\nCounts are frequencies, not certainty",
        "cnot_correlation": "q0: ── H ── ● ── M ──\n             │\nq1: ─────── ⊕ ── M ──\n\nRule: if control q0 = 1, target q1 flips\nBell-style output: mostly 00 and 11",
        "qiskit_debugging": "Common error\n  QuantumCircuit(1, 0)\n  qc.measure(0, 0)  ← no classical bit exists\n\nFix\n  QuantumCircuit(1, 1)\n  qc.measure(0, 0)",
    }
    return diagrams.get(lesson_id, "Diagram is being prepared for this lesson.")



def render_lesson_media(lesson_id: str) -> None:
    """Render one optimized lesson visual and one MP4 micro-video with explicit checks."""
    media = LESSON_MEDIA.get(lesson_id)
    lesson = content.lesson_by_id(lesson_id)
    if not media:
        st.warning(f"No media mapping was found for lesson: {lesson_id}")
        return

    image_name = media.get("image", "")
    video_name = media.get("video", "")
    image_path = LESSON_MEDIA_DIR / image_name
    video_path = LESSON_MEDIA_DIR / video_name

    st.markdown("### Visual and video support")
    st.markdown(
        f"<div class='qai-big-idea'><b>Purpose:</b> {media.get('caption', '')}</div>",
        unsafe_allow_html=True,
    )

    visual_col, video_col = st.columns([1.15, 0.85])
    with visual_col:
        st.markdown("#### Lesson visual")
        render_image(image_path, caption=media.get("caption", "Lesson visual"))

        steps = lesson.get("visual_steps", [])
        if steps:
            st.markdown("**Read the visual in this order**")
            for i, step in enumerate(steps, start=1):
                st.markdown(
                    f"<div class='qai-v73-step'><span class='qai-v73-badge'>{i}</span><div>{step}</div></div>",
                    unsafe_allow_html=True,
                )

    with video_col:
        st.markdown("#### Micro-video")
        render_video(video_path, caption="Short lesson micro-video")
        st.markdown(
            f"<div class='qai-v73-note'><b>What to notice:</b> {media.get('notice', lesson.get('misconception', ''))}</div>",
            unsafe_allow_html=True,
        )

    with st.expander("Connect the visual to code and output"):
        left, right = st.columns(2)
        with left:
            st.markdown("**Tiny Qiskit example**")
            st.code(lesson.get("qiskit_code", ""), language="python")
            if lesson.get("code_focus"):
                st.markdown("**Code reading focus**")
                for point in lesson.get("code_focus", []):
                    st.markdown(f"- {point}")
        with right:
            st.markdown(f"**Before measurement:** {lesson.get('before_measurement', '')}")
            st.markdown(f"**After measurement / output:** {lesson.get('after_measurement', '')}")

    resource_url = media.get("resource_url")
    resource_label = media.get("resource_label", "Optional external resource")
    if resource_url:
        st.markdown(f"Optional enrichment: [{resource_label}]({resource_url})")

def render_learning_path_cards(student: Dict[str, Any], selected_id: str, recommended_set: set, completed: set) -> None:
    st.markdown("### Learning path")
    st.caption("Six compact modules. Choose a card to open it; the platform remembers your latest module.")
    cols = st.columns(3)
    for idx, lesson in enumerate(content.LESSONS):
        with cols[idx % 3]:
            status = "Completed" if lesson["id"] in completed else ("Current" if lesson["id"] == selected_id else "Available")
            klass = "qai-path-done" if lesson["id"] in completed else ("qai-path-current" if lesson["id"] == selected_id else "")
            badge = "✓" if lesson["id"] in completed else ("▶" if lesson["id"] == selected_id else str(idx + 1))
            rec = "Recommended" if lesson["id"] in recommended_set else lesson.get("level", "Module")
            concepts = "".join([f"<span class='qai-concept-pill'>{c}</span>" for c in lesson.get("concepts", [])[:2]])
            st.markdown(
                f"""
                <div class='qai-path-card {klass}'>
                  <div class='qai-path-num'>{badge} Module {idx + 1}</div>
                  <div class='qai-card-title'>{lesson.get('short_title', lesson['title'])}</div>
                  <div class='qai-card-mini'>{lesson.get('duration', '')} · {rec}</div>
                  <div>{concepts}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Open" if lesson["id"] != selected_id else "Opened", key=f"open_path_{lesson['id']}", use_container_width=True, disabled=lesson["id"] == selected_id):
                set_current_lesson(student["id"], lesson["id"])
                st.rerun()


def inline_ai_explain_button(student: Dict[str, Any], lesson: Dict[str, Any], label: str, selected_text: str, key: str) -> None:
    st.markdown("<div class='qai-ai-actions'><b>AI support for this part</b><br>Use the tutor for explanation, hints, or a reflective question without leaving the module.</div>", unsafe_allow_html=True)
    cols = st.columns([1, 1, 1])
    actions = [
        ("Explain simply", "Explain selected text simply"),
        ("Give a hint", "Give a hint without full answer"),
        ("Ask me a question", "Ask one reflective check question"),
    ]
    for col, (button_label, task) in zip(cols, actions):
        if col.button(button_label, key=f"{key}_{button_label}", use_container_width=True):
            tutor = feedback_engine.generate_tutor_response(
                task=task,
                concept=", ".join(lesson["concepts"]),
                student_input=f"Selected lesson text: {selected_text}",
                student_profile=student_profile(student),
                lesson_context={**lesson, "source": "inline_lesson_help", "response_language": "Auto-detect"},
            )
            interaction_id = log_tutor_interaction(
                student["id"], "inline_lesson_help", ", ".join(lesson["concepts"]), task,
                f"Explain selected text: {selected_text}", tutor, lesson_id=lesson["id"], activity_id=key, selected_text=selected_text,
            )
            st.markdown("#### AI tutor explanation")
            st.write(tutor.response)
            render_ai_usefulness_feedback(interaction_id, f"inline_{key}")


def render_learning_module(student: Dict[str, Any]) -> None:
    hero("Learning Path", "Professional micro-lessons: visual explanation, tiny Qiskit example, AI support, and reflection.")
    if not test_is_done(student["id"], "pre"):
        st.warning("Please complete the pre-test before opening the learning path.")
        if st.button("Go to pre-test", type="primary"):
            set_student_page("Pre-test")
        return

    rec = db.get_recommendation(student["id"]) or db.compute_adaptive_recommendation(student["id"], content.CONCEPT_TO_LESSONS)
    recommended_set = set(rec.get("recommended_lessons", [])) if rec else set()
    progress = db.get_lesson_progress(student["id"])
    completed = set(progress[progress["completed"] == 1]["lesson_id"].tolist()) if not progress.empty else set()
    selected_id = current_or_resume_lesson_id(student["id"])
    valid_ids = {l["id"] for l in content.LESSONS}
    if selected_id not in valid_ids:
        selected_id = first_incomplete_lesson_id(student["id"])
    lesson = content.lesson_by_id(selected_id)
    db.log_event(student["id"], "student", "open_module", selected_id)

    st.markdown("<div class='qai-learning-shell'>", unsafe_allow_html=True)
    st.progress(len(completed) / len(content.LESSONS), text=f"Learning path progress: {len(completed)}/{len(content.LESSONS)} modules completed")
    render_learning_path_cards(student, selected_id, recommended_set, completed)
    st.markdown("</div>", unsafe_allow_html=True)

    status_msg = "Completed" if lesson["id"] in completed else ("Recommended" if lesson["id"] in recommended_set else "Available")
    concept_html = "".join([f"<span class='qai-concept-pill'>{c}</span>" for c in lesson.get("concepts", [])])
    st.markdown(
        f"""
        <div class='qai-module-header'>
          <div>
            <div class='qai-module-kicker'>{status_msg} · {lesson.get('level','Module')} · {lesson.get('duration','')}</div>
            <div class='qai-module-title'>{lesson['title']}</div>
            <div class='qai-module-meta'>{lesson['objective']}</div>
          </div>
          <div>{concept_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if lesson["id"] in completed:
        st.success("This module is completed. You may review it or continue to the next module.")

    media_tab, overview, concepts_tab, code_tab, check_tab = st.tabs([
        "Visual and video",
        "Overview",
        "Concept",
        "Code and output",
        "Check and reflect",
    ])

    with overview:
        st.markdown(f"<div class='qai-big-idea'><b>Big idea:</b> {lesson.get('big_idea', lesson['concept'])}</div>", unsafe_allow_html=True)
        a, b = st.columns([1.1, 0.9])
        with a:
            st.markdown("#### Core explanation")
            st.write(lesson["concept"])
            st.markdown("#### Why this matters")
            st.write(lesson["why_it_matters"])
        with b:
            if lesson.get("can_do"):
                st.markdown("#### By the end of this module you can")
                st.markdown("<ul class='qai-focus-list'>" + "".join([f"<li>{o}</li>" for o in lesson.get("can_do", [])]) + "</ul>", unsafe_allow_html=True)
            st.markdown("#### Misconception to avoid")
            st.warning(lesson["misconception"])
        inline_ai_explain_button(student, lesson, "concept", lesson["concept"], f"concept_{lesson['id']}")

    with concepts_tab:
        st.markdown("#### Concept scaffold")
        st.info(lesson["objective"])
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Before measurement")
            st.write(lesson["before_measurement"])
        with c2:
            st.markdown("#### After measurement")
            st.write(lesson["after_measurement"])
        if lesson.get("visual_steps"):
            st.markdown("#### Learn it step by step")
            cols = st.columns(len(lesson.get("visual_steps", [])))
            for i, step in enumerate(lesson.get("visual_steps", []), start=1):
                with cols[i - 1]:
                    st.markdown(f"<div class='qai-dashboard-tile'><div class='qai-tile-value'>{i}</div><div class='qai-tile-label'>{step}</div></div>", unsafe_allow_html=True)

    with code_tab:
        c1, c2 = st.columns([1.05, 0.95])
        with c1:
            st.markdown("#### Tiny Qiskit example")
            st.code(lesson["qiskit_code"], language="python")
        with c2:
            st.markdown("#### Code reading focus")
            for point in lesson.get("code_focus", []):
                st.markdown(f"- {point}")
            inline_ai_explain_button(student, lesson, "qiskit", lesson["qiskit_code"], f"code_{lesson['id']}")

    with media_tab:
        render_lesson_media(lesson["id"])
        try:
            db.log_event(student["id"], "student", "view_professional_media", lesson["id"])
        except Exception:
            pass

    with check_tab:
        st.markdown(f"<div class='qai-check-card'><b>Mini task before asking AI:</b> {lesson.get('mini_task','Predict the output or identify the key line in the Qiskit example.')}</div>", unsafe_allow_html=True)
        if lesson.get("check_question"):
            st.info("Check your understanding: " + lesson.get("check_question"))
        st.markdown("#### Reflection prompt")
        st.write(lesson["reflective_prompt"])

    st.divider()
    st.markdown("### AI-supported activity inside this module")
    activity_language = st.selectbox(
        "AI response language",
        ["Auto-detect", "English", "Arabic", "French"],
        index=0,
        key=f"lesson_ai_language_{lesson['id']}",
        help="Choose Arabic if you want the tutor to explain this learning activity in Arabic.",
    )
    c1, c2, c3, c4 = st.columns(4)
    task = None
    if c1.button("Explain visual", use_container_width=True):
        task = "Explain the lesson visual"
    if c2.button("Practice exercise", use_container_width=True):
        task = "Generate a practice exercise"
    if c3.button("Hint only", use_container_width=True):
        task = "Give a hint without the full answer"
    if c4.button("Ask one question", use_container_width=True):
        task = "Ask one reflective check question"
    if task:
        tutor = feedback_engine.generate_tutor_response(
            task=task,
            concept=", ".join(lesson["concepts"]),
            student_input=f"Lesson: {lesson['title']}. Mini task: {lesson.get('mini_task','')}",
            student_profile=student_profile(student),
            lesson_context={**lesson, "response_language": activity_language},
        )
        interaction_id = log_tutor_interaction(
            student["id"], "learning_module", ", ".join(lesson["concepts"]), task,
            f"Lesson activity for {lesson['title']}", tutor, lesson_id=lesson["id"], activity_id="module_ai_activity",
        )
        st.session_state.last_ai_interaction_id = interaction_id
        st.markdown("#### AI tutor response")
        st.write(tutor.response)
        render_ai_usefulness_feedback(interaction_id, f"lesson_{lesson['id']}")

    st.divider()
    st.markdown("### Reflection and completion")
    st.info(lesson["reflective_prompt"])
    reflection_default = ""
    if not progress.empty:
        row = progress[progress["lesson_id"] == lesson["id"]]
        if not row.empty:
            reflection_default = str(row["reflection_text"].iloc[0] or "")
    with st.form(f"reflection_{lesson['id']}"):
        reflection = st.text_area("Write your reflection in your own words", value=reflection_default, height=130)
        submitted = st.form_submit_button("Save reflection and mark module complete", type="primary")
    if submitted:
        if len(reflection.strip()) < 20:
            st.error("Please write a short reflection before marking the module complete.")
        else:
            db.save_lesson_progress(student["id"], lesson["id"], reflection, completed=True)
            db.log_event(student["id"], "student", "lesson_completed", lesson["id"])
            completed.add(lesson["id"])
            current_idx = [l["id"] for l in content.LESSONS].index(lesson["id"])
            if current_idx + 1 < len(content.LESSONS):
                st.session_state.current_lesson_id = content.LESSONS[current_idx + 1]["id"]
            st.success("Reflection saved. Module completed.")
            st.rerun()

    st.divider()
    nav1, nav2, nav3 = st.columns(3)
    ids = [l["id"] for l in content.LESSONS]
    idx = ids.index(lesson["id"])
    if nav1.button("← Previous module", use_container_width=True, disabled=idx == 0):
        set_current_lesson(student["id"], ids[idx - 1])
        st.rerun()
    if nav2.button("Ask AI about this module", use_container_width=True):
        st.session_state.current_lesson_id = lesson["id"]
        st.session_state.student_page = "AI Tutor Lab"
        st.rerun()
    if nav3.button("Next module →", type="primary", use_container_width=True, disabled=idx >= len(ids) - 1):
        set_current_lesson(student["id"], ids[idx + 1])
        st.rerun()

    if learning_path_ready_for_posttest(student["id"]) and has_minimum_ai_interaction(student["id"]):
        st.success("Learning path and AI interaction requirements are complete. You may continue to the post-test when ready.")
        if st.button("Go to post-test", type="primary", use_container_width=True):
            set_student_page("Post-test")
    else:
        remaining = required_lesson_count_for_posttest() - lesson_completion_count(student["id"])
        if remaining > 0:
            st.info(f"Post-test is locked until the full learning path is complete. Remaining modules: {remaining}.")
        elif not has_minimum_ai_interaction(student["id"]):
            st.info("Post-test is locked until at least one AI Tutor interaction is recorded.")


def render_ai_tutor_lab(student: Dict[str, Any]) -> None:
    hero(
        "AI Tutor Lab",
        "A continuous learning conversation with context from the current module. The tutor is designed to guide, not replace, your reasoning.",
    )
    ux_note(
        "<b>How to use the AI Tutor:</b><br>"
        "Ask a specific question, paste a small Qiskit snippet, or write your current explanation first. "
        "The tutor will keep the visible conversation history during the session and log each interaction for research analytics."
    )

    status = feedback_engine.provider_status()
    if status["available"]:
        st.success(f"LLM provider configured: {status['provider']} ({status['model']})")
    else:
        st.info("No external LLM is configured. The lab will use a local formative fallback.")

    current_lesson_id = current_or_resume_lesson_id(student["id"]) if test_is_done(student["id"], "pre") else content.LESSONS[0]["id"]
    current_lesson = content.lesson_by_id(current_lesson_id)
    concepts = sorted({c for lesson in content.LESSONS for c in lesson["concepts"]})
    default_concept = current_lesson["concepts"][0] if current_lesson.get("concepts") else concepts[0]
    default_index = concepts.index(default_concept) if default_concept in concepts else 0

    c1, c2, c3 = st.columns([1.15, 1, 1])
    with c1:
        task = st.selectbox(
            "Tutor task",
            ["Explain a concept", "Generate a practice exercise", "Check my explanation", "Debug or interpret Qiskit code"],
        )
    with c2:
        concept = st.selectbox("Concept focus", concepts, index=default_index)
    with c3:
        tutor_language = st.selectbox(
            "Response language",
            ["Auto-detect", "English", "Arabic", "French"],
            index=0,
            help="Auto-detect uses the language of your question. Select Arabic to force Arabic responses.",
        )

    st.markdown(
        f"""
        <div class="qai-chat-context">
          <b>Current learning context:</b> {current_lesson['title']}<br>
          <span>The tutor will connect answers to this module unless your question asks for something else.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Return to current learning module", use_container_width=True):
        st.session_state.student_page = "Learning Module"
        st.rerun()

    chat_key = f"ai_chat_history_{student['id']}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    quick_prompts = {
        "Explain simply": f"I am confused about {concept}. Explain it simply, then ask me one question to check my understanding.",
        "Give practice": f"Give me one short beginner exercise about {concept}. Do not give the full solution first.",
        "Check my idea": f"Here is my explanation of {concept}: ... Please tell me what is correct and what I should improve.",
        "Help with code": "Here is my Qiskit code:\n\n# paste code here\n\nPlease help me interpret it or find the mistake without giving a long answer.",
    }

    st.markdown("#### Quick-start prompts")
    qcols = st.columns(4)
    for i, (label, example) in enumerate(quick_prompts.items()):
        with qcols[i]:
            if st.button(label, key=f"chat_quick_{i}", use_container_width=True):
                st.session_state.pending_chat_prompt = example
                st.rerun()

    pending = st.session_state.get("pending_chat_prompt", "")
    if pending:
        st.markdown("<div class='qai-chat-draft'><b>Draft prompt selected:</b></div>", unsafe_allow_html=True)
        st.text_area("Edit the selected prompt before sending", key="pending_chat_prompt", height=120)
        send_draft = st.button("Send selected prompt", type="primary", use_container_width=True)
    else:
        send_draft = False

    st.markdown("### Conversation")
    if not st.session_state[chat_key]:
        st.caption("No messages yet. Ask a question below or start from one of the prompt buttons.")
    for msg in st.session_state[chat_key]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("interaction_id") and msg["role"] == "assistant":
                render_ai_usefulness_feedback(msg["interaction_id"], f"chat_{msg['interaction_id']}")

    prompt = st.chat_input("Ask about the current module, a concept, or a Qiskit code snippet...")
    if send_draft:
        prompt = st.session_state.get("pending_chat_prompt", "")
        st.session_state.pending_chat_prompt = ""

    if prompt:
        if len(prompt.strip()) < 10:
            st.warning("Please write at least a short attempt or question before asking the AI tutor.")
            return

        st.session_state[chat_key].append({"role": "user", "content": prompt})
        with st.spinner("AI tutor is thinking..."):
            tutor = feedback_engine.generate_tutor_response(
                task=task,
                concept=concept,
                student_input=prompt,
                student_profile=student_profile(student),
                lesson_context={
                    "source": "AI Tutor Lab",
                    "response_language": tutor_language,
                    "current_lesson": current_lesson,
                    "chat_history": st.session_state[chat_key][-6:],
                },
            )
        interaction_id = log_tutor_interaction(
            student["id"], "ai_tutor_lab", concept, task, prompt, tutor, lesson_id=current_lesson_id, activity_id="free_tutor_chat"
        )
        st.session_state.last_ai_interaction_id = interaction_id
        st.session_state[chat_key].append({"role": "assistant", "content": tutor.response, "interaction_id": interaction_id})
        if tutor.mode == "llm_error":
            st.info("The external LLM was unavailable. A local hint was shown and the error was logged for the evaluator.")
        if learning_path_ready_for_posttest(student["id"]):
            st.success("AI interaction recorded. Your learning path is complete, so the post-test is available.")
        else:
            st.info("AI interaction recorded. Continue the learning path; the post-test unlocks after all modules are complete.")
        st.rerun()

    st.divider()
    if st.button("Clear visible chat history", use_container_width=True):
        st.session_state[chat_key] = []
        st.rerun()

def render_survey(student: Dict[str, Any]) -> None:
    hero("Usability Questionnaire and Open-ended Feedback", "Your feedback helps evaluate the AI-supported learning framework.")
    if not test_is_done(student["id"], "post"):
        st.warning("Please complete the post-test before the survey.")
        return
    existing = db.get_survey(student["id"])
    if existing:
        st.success("Survey already submitted. Thank you.")
        return
    with st.form("survey_form"):
        st.markdown("Rate each item from 1 = strongly disagree to 5 = strongly agree.")
        responses: Dict[str, int] = {}
        for key, label in content.SURVEY_ITEMS:
            responses[key] = st.slider(label, 1, 5, 3, key=f"survey_{key}")
        open_feedback: Dict[str, str] = {}
        st.markdown("### Open-ended feedback")
        for key, label in content.OPEN_ENDED_ITEMS:
            open_feedback[key] = st.text_area(label, key=f"open_{key}")
        submitted = st.form_submit_button("Submit survey", type="primary", use_container_width=True)
    if submitted:
        db.save_survey(student["id"], responses, open_feedback)
        db.log_event(student["id"], "student", "survey_submitted", "Usability questionnaire and open-ended feedback submitted")
        st.success("Thank you. Your responses have been recorded. Your participation is now complete.")
        st.balloons()
        st.rerun()

# -----------------------------------------------------------------------------
# Evaluator workspace
# -----------------------------------------------------------------------------

def render_evaluator_app() -> None:
    if not st.session_state.evaluator_logged_in:
        render_evaluator_login()
        return
    page = st.session_state.evaluator_page
    if page == "Evaluator Dashboard":
        render_evaluator_dashboard()
    elif page == "Students":
        render_students_admin()
    elif page == "Registration Accounts":
        render_registration_accounts()
    elif page == "Student Details":
        render_student_details()
    elif page == "Progress Monitor":
        render_progress_monitor()
    elif page == "Learning Analytics":
        render_learning_analytics()
    elif page == "Paper-ready Analysis":
        render_paper_ready_analysis()
    elif page == "LLM Performance Evaluation":
        render_llm_performance_evaluation()
    elif page == "Feedback Logs":
        render_feedback_logs()
    elif page == "Survey Results":
        render_survey_results()
    elif page == "Event Logs":
        render_event_logs()
    elif page == "System Readiness":
        render_system_readiness()
    elif page == "Results Export":
        render_results_export()


def render_evaluator_login() -> None:
    hero("Evaluator Sign in", "Protected workspace for monitoring participants and exporting study data.")
    if secret("ADMIN_PASSWORD", "admin123") == "admin123" and not secret("EVALUATOR_PASSWORD_HASH", ""):
        st.warning("Default evaluator password is still active. Change ADMIN_PASSWORD or use EVALUATOR_PASSWORD_HASH before cloud deployment.")
    with st.form("eval_login"):
        username = st.text_input("Evaluator username", value=secret("EVALUATOR_USERNAME", "evaluator"))
        password = st.text_input("Evaluator password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
    if submitted:
        if evaluator_password_is_valid(username, password):
            db.log_event(None, "evaluator", "sign_in", f"Evaluator username: {username.strip()}")
            st.session_state.evaluator_logged_in = True
            st.success("Signed in.")
            st.rerun()
        else:
            st.error("Invalid evaluator credentials.")


def render_evaluator_dashboard() -> None:
    hero("Evaluator Dashboard", "Monitor study progress, learning outcomes, AI tutor usage, reflections, and exports.")
    df = db.progress_summary_df(len(content.LESSONS))
    survey_count = db.count_rows("survey_responses")
    ai_count = db.count_rows("ai_interactions")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Students", len(df))
    c2.metric("Pre-tests", int(df["pre_done"].sum()) if not df.empty else 0)
    c3.metric("Post-tests", int(df["post_done"].sum()) if not df.empty else 0)
    c4.metric("Complete cases", int(df["is_complete_case"].sum()) if not df.empty and "is_complete_case" in df else 0)
    c5.metric("Surveys", survey_count)
    c6.metric("AI logs", ai_count)

    status = feedback_engine.provider_status()
    readiness = db.system_readiness(len(content.LESSONS))
    st.markdown("### Deployment status")
    st.write({
        "app_version": readiness.get("app_version"),
        "database_dialect": readiness.get("database_dialect"),
        "database_ok": readiness.get("database_ok"),
        "provider": status["provider"],
        "available": status["available"],
        "model": status["model"],
        "gemini_key_detected": status["gemini_key_detected"],
        "openai_key_detected": status["openai_key_detected"],
        "groq_key_detected": status.get("groq_key_detected", False),
    })

    usage = db.ai_usage_df()
    if not usage.empty:
        st.markdown("### AI tutor usage by mode")
        st.dataframe(usage, use_container_width=True, hide_index=True)
        usage_bar = usage.copy()
        usage_bar["provider_mode"] = usage_bar["provider"].astype(str) + " / " + usage_bar["mode"].astype(str)
        render_progress_bars(usage_bar, "provider_mode", "interactions", "Interactions by provider and mode")

    if not df.empty:
        st.markdown("### Recent participants")
        recent_cols = ["participant_code", "full_name", "academic_level", "pre_score", "post_score", "learning_gain", "progress_percent", "ai_interactions", "is_complete_case", "complete_case_missing"]
        recent = df[[c for c in recent_cols if c in df.columns]].head(30)
        st.dataframe(recent, use_container_width=True, hide_index=True)
        if len(df) > 30:
            st.caption(f"Showing 30 most recent participants out of {len(df)}. Use Results Export for the full dataset.")

def render_students_admin() -> None:
    hero("Students", "Create participant accounts, review student list, and manage access.")
    with st.expander("Create participant account as evaluator", expanded=False):
        with st.form("evaluator_create_student"):
            c1, c2 = st.columns(2)
            with c1:
                full_name = st.text_input("Full name")
                email = st.text_input("Email")
                institution = st.text_input("Institution")
            with c2:
                academic_level = st.selectbox("Academic level", ["Licence", "Master", "PhD", "Other"], key="eval_level")
                prior_python = st.slider("Prior Python level", 0, 3, 1, key="eval_python")
                prior_quantum = st.slider("Prior quantum knowledge", 0, 3, 0, key="eval_quantum")
            password = st.text_input("Initial password", type="password", help="Give this to the student; ask them to keep it private.")
            submitted = st.form_submit_button("Create participant", type="primary")
        if submitted:
            try:
                student = db.create_student(full_name, email, institution, academic_level, prior_python, prior_quantum, password)
                db.log_event(student["id"], "evaluator", "account_created_by_evaluator", "Evaluator created participant account")
                st.success(f"Created: {student['participant_code']} | Initial password set.")
            except Exception as exc:
                st.error(f"Could not create participant: {exc}")

    df = db.students_df()
    st.markdown("### Registered students")
    if df.empty:
        st.info("No students registered yet.")
        return
    st.dataframe(df, use_container_width=True)



def render_registration_accounts() -> None:
    hero("Registration Accounts", "Review account-registration information, sign-in status, and access readiness for participants.")
    st.info(
        "This evaluator view shows registration metadata needed to support the pilot study. "
        "It never displays student passwords, password hashes, or password-reset tokens."
    )

    df = db.students_df()
    if df.empty:
        st.info("No registered student accounts yet.")
        return

    accounts = df.copy()
    for col in ["email", "institution", "academic_level", "created_at", "last_login_at"]:
        if col not in accounts.columns:
            accounts[col] = ""
        accounts[col] = accounts[col].fillna("")
    accounts["is_active"] = accounts.get("is_active", 1).fillna(1).astype(int)
    accounts["email_missing"] = accounts["email"].astype(str).str.strip().eq("")
    accounts["has_signed_in"] = accounts["last_login_at"].astype(str).str.strip().ne("")

    total = len(accounts)
    active = int(accounts["is_active"].sum())
    email_missing = int(accounts["email_missing"].sum())
    signed_in = int(accounts["has_signed_in"].sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registered accounts", total)
    c2.metric("Active accounts", active)
    c3.metric("Missing email", email_missing)
    c4.metric("Signed in at least once", signed_in)

    st.markdown("### Search and filters")
    q = st.text_input("Search by participant code, name, email, or institution")
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        only_active = st.checkbox("Only active accounts", value=False)
    with fc2:
        only_missing_email = st.checkbox("Only accounts missing email", value=False)
    with fc3:
        only_never_signed = st.checkbox("Only never signed in", value=False)

    filtered = accounts.copy()
    if q.strip():
        query = q.strip().lower()
        searchable = (
            filtered["participant_code"].astype(str) + " "
            + filtered["full_name"].astype(str) + " "
            + filtered["email"].astype(str) + " "
            + filtered["institution"].astype(str)
        ).str.lower()
        filtered = filtered[searchable.str.contains(query, na=False)]
    if only_active:
        filtered = filtered[filtered["is_active"] == 1]
    if only_missing_email:
        filtered = filtered[filtered["email_missing"]]
    if only_never_signed:
        filtered = filtered[~filtered["has_signed_in"]]

    st.markdown("### Registration account list")
    display_cols = [
        "participant_code", "full_name", "email", "institution", "academic_level",
        "prior_python_level", "prior_quantum_level", "created_at", "last_login_at", "is_active",
    ]
    display = filtered[[c for c in display_cols if c in filtered.columns]].copy()
    display = display.rename(columns={
        "participant_code": "Participant code",
        "full_name": "Full name",
        "email": "Email",
        "institution": "Institution",
        "academic_level": "Academic level",
        "prior_python_level": "Python level",
        "prior_quantum_level": "Quantum level",
        "created_at": "Created at",
        "last_login_at": "Last login",
        "is_active": "Active",
    })
    st.dataframe(display, use_container_width=True, hide_index=True)

    csv = display.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download account registration list (CSV)",
        data=csv,
        file_name="qai_registration_accounts.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown("### Account support notes")
    st.markdown(
        "- Use this page to identify students who forgot their participant code, used the wrong email, or never signed in after registration.\n"
        "- For password recovery, students should use the **Forgot password** link on the sign-in page.\n"
        "- The evaluator can see registration contact information, but passwords remain protected and are not recoverable."
    )

def render_student_details() -> None:
    hero("Student Details", "Inspect a participant's tests, lesson reflections, AI interactions, and survey data.")
    df = db.students_df()
    if df.empty:
        st.info("No students registered yet.")
        return
    code = st.selectbox("Select participant", df["participant_code"].tolist(), format_func=lambda c: f"{c} - {df[df['participant_code']==c]['full_name'].iloc[0]}")
    student = db.get_student_by_code(code)
    if not student:
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("Participant code", student["participant_code"])
    c2.metric("Academic level", student.get("academic_level") or "-")
    c3.metric("Active", "Yes" if student.get("is_active") else "No")

    pre = db.get_test_attempt(student["id"], "pre")
    post = db.get_test_attempt(student["id"], "post")
    c1, c2, c3 = st.columns(3)
    c1.metric("Pre-test", f"{pre['score']:.1f}%" if pre else "Pending")
    c2.metric("Post-test", f"{post['score']:.1f}%" if post else "Pending")
    if pre and post:
        c3.metric("Learning gain", f"{post['score'] - pre['score']:.1f}")
    else:
        c3.metric("Learning gain", "-")

    st.markdown("### Completion requirements")
    render_completion_requirements(student)

    st.markdown("### Lesson reflections")
    progress = db.get_lesson_progress(student["id"])
    st.dataframe(progress, use_container_width=True)

    st.markdown("### Learning timeline")
    timeline = db.student_events_df(student["id"], limit=150)
    st.dataframe(timeline, use_container_width=True, hide_index=True)

    st.markdown("### AI interactions")
    logs = db.ai_logs_df(limit=100, participant_code=student["participant_code"])
    st.dataframe(logs, use_container_width=True, hide_index=True)
    if len(logs) >= 100:
        st.caption("Showing the latest 100 AI interactions for this participant.")


def render_progress_monitor() -> None:
    hero("Progress Monitor", "Track completion of the one-group pre-test/post-test learning flow.")
    df = db.progress_summary_df(len(content.LESSONS))
    if df.empty:
        st.info("No students registered yet.")
        return
    cols = ["participant_code", "full_name", "consent_done", "pre_done", "completed_lessons", "ai_interactions", "post_done", "survey_done", "is_complete_case", "complete_case_missing", "progress_percent"]
    st.dataframe(df[[c for c in cols if c in df.columns]], use_container_width=True, hide_index=True)
    render_progress_bars(df, "participant_code", "progress_percent", "Completion progress")


def render_learning_analytics() -> None:
    hero("Learning Analytics", "Analyze pre/post scores, concept-level performance, and learning gain.")
    df = db.progress_summary_df(len(content.LESSONS))
    if df.empty:
        st.info("No student data yet.")
        return
    st.markdown("### Score summary")
    show_cols = ["participant_code", "full_name", "pre_score", "post_score", "learning_gain", "completed_lessons", "ai_interactions", "is_complete_case", "complete_case_missing"]
    show = df[[c for c in show_cols if c in df.columns]]
    st.dataframe(show, use_container_width=True)
    numeric = show[["pre_score", "post_score", "learning_gain", "completed_lessons", "ai_interactions"]].dropna(how="all")
    if not numeric.empty:
        st.write(numeric.describe())

    st.markdown("### AI-supported learning observer")
    observer = db.ai_learning_observer_df()
    if observer.empty:
        st.info("No AI interaction analytics available yet.")
    else:
        st.dataframe(observer, use_container_width=True, hide_index=True)
        if "interactions" in observer.columns:
            render_progress_bars(observer, "module", "interactions", "AI interactions by module")

    concept_df = db.concept_scores_df()
    if not concept_df.empty:
        st.markdown("### Concept-level performance")
        pivot = concept_df.pivot_table(index="concept", columns="attempt_type", values="percentage", aggfunc="mean").reset_index()
        st.dataframe(pivot, use_container_width=True)
        # Stable, Streamlit-version-safe visualization.
        for col in [c for c in pivot.columns if c != "concept"]:
            bars = pivot[["concept", col]].rename(columns={col: "percentage"}).copy()
            render_progress_bars(bars, "concept", "percentage", f"Mean {col} score by concept")
    else:
        st.info("No concept scores available yet.")



def render_paper_ready_analysis() -> None:
    hero("Paper-ready Analysis", "Generate the core tables and indicators needed for the Results and Discussion section of the paper.")
    progress = db.progress_summary_df(len(content.LESSONS))
    ai_usage_source = db.ai_usage_df()
    concept_df = db.concept_scores_df()
    survey = db.survey_df()

    if progress.empty:
        st.info("No participant data yet.")
        return

    complete = progress.dropna(subset=["pre_score", "post_score"]).copy()
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Registered", len(progress))
    c2.metric("Pre-tests", int(progress["pre_done"].sum()))
    c3.metric("Post-tests", int(progress["post_done"].sum()))
    c4.metric("Complete pairs", len(complete))
    c5.metric("Complete cases", int(progress["is_complete_case"].sum()) if "is_complete_case" in progress else 0)
    c6.metric("Surveys", len(survey))

    st.markdown("### Completion validity for analysis")
    completion_cols = ["participant_code", "full_name", "consent_done", "pre_done", "completed_lessons", "ai_interactions", "post_done", "survey_done", "is_complete_case", "complete_case_missing"]
    st.dataframe(progress[[c for c in completion_cols if c in progress.columns]], use_container_width=True, hide_index=True)

    st.markdown("### Pre-test / Post-test summary")
    if complete.empty:
        st.warning("No paired pre/post results yet.")
    else:
        complete["learning_gain"] = pd.to_numeric(complete["learning_gain"], errors="coerce")
        pre_mean = float(complete["pre_score"].mean())
        post_mean = float(complete["post_score"].mean())
        gain_mean = float(complete["learning_gain"].mean())
        gain_sd = float(complete["learning_gain"].std(ddof=1)) if len(complete) > 1 else 0.0
        cohens_dz = gain_mean / gain_sd if gain_sd else None
        summary_rows = pd.DataFrame([
            {"indicator": "Mean pre-test score (%)", "value": round(pre_mean, 2)},
            {"indicator": "Mean post-test score (%)", "value": round(post_mean, 2)},
            {"indicator": "Mean learning gain (percentage points)", "value": round(gain_mean, 2)},
            {"indicator": "Median learning gain", "value": round(float(complete["learning_gain"].median()), 2)},
            {"indicator": "Cohen's dz (paired effect size)", "value": round(cohens_dz, 3) if cohens_dz is not None else "Not available"},
        ])
        st.dataframe(summary_rows, use_container_width=True)
        st.caption("Cohen's dz is computed as mean paired gain divided by the standard deviation of paired gains. For formal significance testing, export the data and report paired t-test or Wilcoxon results according to sample size and assumptions.")

    st.markdown("### Concept-level gain")
    concept_gain = pd.DataFrame()
    if not concept_df.empty:
        pivot = concept_df.pivot_table(index="concept", columns="attempt_type", values="percentage", aggfunc="mean").reset_index()
        if "pre" in pivot.columns and "post" in pivot.columns:
            pivot["gain"] = pivot["post"] - pivot["pre"]
            concept_gain = pivot.sort_values("gain", ascending=False)
            st.dataframe(concept_gain, use_container_width=True)
            render_progress_bars(concept_gain.rename(columns={"gain": "percentage_gain"}), "concept", "percentage_gain", "Mean gain by concept")
        else:
            st.dataframe(pivot, use_container_width=True)
    else:
        st.info("No concept-level scores yet.")

    st.markdown("### Generative AI / LLM usage evidence")
    ai_usage = pd.DataFrame()
    if not ai_usage_source.empty:
        ai_usage = ai_usage_source.copy()
        total = int(ai_usage["interactions"].sum())
        ai_usage["percentage"] = (ai_usage["interactions"] / max(total, 1) * 100).round(2)
        st.dataframe(ai_usage, use_container_width=True, hide_index=True)
        render_progress_bars(ai_usage.assign(provider_mode=ai_usage["provider"].astype(str) + " / " + ai_usage["mode"].astype(str)), "provider_mode", "interactions", "Interactions by provider and mode")
        llm_count = int(ai_usage.loc[ai_usage["mode"] == "llm", "interactions"].sum()) if "mode" in ai_usage else 0
        st.info(f"Paper evidence: {llm_count} of {total} AI tutor interactions were completed through an external LLM provider.")
    else:
        st.warning("No AI interactions recorded yet.")

    st.markdown("### Usability questionnaire means")
    survey_means = pd.DataFrame()
    if not survey.empty:
        rows = []
        for _, row in survey.iterrows():
            responses = json.loads(row.get("responses_json") or "{}")
            rows.append(responses)
        survey_items = pd.DataFrame(rows)
        numeric_cols = [key for key, _ in content.SURVEY_ITEMS if key in survey_items]
        if numeric_cols:
            survey_means = survey_items[numeric_cols].mean().reset_index()
            survey_means.columns = ["item", "mean_score"]
            label_map = dict(content.SURVEY_ITEMS)
            survey_means["item_text"] = survey_means["item"].map(label_map)
            st.dataframe(survey_means[["item", "item_text", "mean_score"]], use_container_width=True)
    else:
        st.info("No survey responses yet.")

    st.markdown("### LLM pedagogical performance evaluation")
    eval_summary = db.llm_evaluation_summary_df()
    if not eval_summary.empty:
        st.dataframe(eval_summary, use_container_width=True, hide_index=True)
        render_progress_bars(eval_summary, "metric", "mean_score", "Mean expert rating by criterion")
    else:
        st.info("No expert ratings have been recorded yet. Use the LLM Performance Evaluation page to rate AI tutor responses.")

    technical_logs = db.ai_logs_df(limit=10000)
    if not technical_logs.empty:
        tech_rows = []
        total_ai = len(technical_logs)
        for label, condition in [
            ("LLM success rate", technical_logs["mode"].astype(str).eq("llm")),
            ("LLM error rate", technical_logs["mode"].astype(str).eq("llm_error")),
            ("Fallback/rule-based rate", technical_logs["mode"].astype(str).isin(["rule_based", "llm_error"])),
        ]:
            n = int(condition.sum())
            tech_rows.append({"metric": label, "count": n, "percentage": round(n / max(total_ai, 1) * 100, 2)})
        if "latency_ms" in technical_logs:
            latency = pd.to_numeric(technical_logs["latency_ms"], errors="coerce").dropna()
            if not latency.empty:
                tech_rows.append({"metric": "Mean response latency (ms)", "count": round(float(latency.mean()), 2), "percentage": None})
        technical_summary = pd.DataFrame(tech_rows)
        st.dataframe(technical_summary, use_container_width=True, hide_index=True)

    st.markdown("### Download paper-ready tables")
    export_tables = {
        "paper_summary": pd.DataFrame([{
            "n_registered": len(progress),
            "n_pre": int(progress["pre_done"].sum()),
            "n_post": int(progress["post_done"].sum()),
            "n_complete_pairs": len(complete),
            "mean_pre": round(float(complete["pre_score"].mean()), 2) if not complete.empty else None,
            "mean_post": round(float(complete["post_score"].mean()), 2) if not complete.empty else None,
            "mean_gain": round(float(complete["learning_gain"].mean()), 2) if not complete.empty else None,
        }]),
        "paired_scores": complete,
        "concept_gain": concept_gain,
        "ai_usage": ai_usage,
        "survey_means": survey_means,
        "llm_evaluation_summary": db.llm_evaluation_summary_df(),
        "llm_evaluations": db.llm_evaluations_df(),
    }
    st.download_button(
        "Download paper-ready analysis workbook",
        data=to_excel_bytes(export_tables),
        file_name="qai_paper_ready_analysis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )


def render_llm_performance_evaluation() -> None:
    hero("LLM Performance Evaluation", "Rate AI tutor responses using a pedagogical rubric for journal-level analysis.")
    st.markdown("""
    This page evaluates the LLM tutor itself, not the student. Rate sampled AI responses from 1 to 5 across
    conceptual, pedagogical, and technical criteria. These ratings will be used to report LLM pedagogical
    quality in addition to student learning gain.
    """)

    c1, c2, c3 = st.columns(3)
    limit = c1.selectbox("Responses to load", [10, 20, 50, 100], index=1)
    only_unrated = c2.checkbox("Show only unrated responses", value=True)
    only_llm = c3.checkbox("Focus on LLM / LLM-error responses", value=True)
    candidates = db.llm_candidate_interactions_df(limit=limit, only_unrated=only_unrated, only_llm=only_llm)
    if candidates.empty:
        st.info("No AI responses match these filters.")
        summary = db.llm_evaluation_summary_df()
        if not summary.empty:
            st.markdown("### Current rating summary")
            st.dataframe(summary, use_container_width=True, hide_index=True)
        return

    st.markdown("### Candidate AI responses")
    preview_cols = [
        "interaction_id", "created_at", "participant_code", "concept", "task", "mode", "provider", "model",
        "latency_ms", "response_word_count", "existing_quality_score",
    ]
    available_preview = [c for c in preview_cols if c in candidates.columns]
    st.dataframe(candidates[available_preview], use_container_width=True, hide_index=True)

    interaction_ids = candidates["interaction_id"].astype(int).tolist()
    selected_id = st.selectbox("Select an AI interaction to evaluate", interaction_ids)
    row = candidates[candidates["interaction_id"] == selected_id].iloc[0].to_dict()

    st.markdown("### Prompt and AI response")
    st.caption(f"Participant: {row.get('participant_code', '-')} | Concept: {row.get('concept', '-')} | Task: {row.get('task', '-')}")
    with st.expander("Student prompt / input", expanded=True):
        st.write(row.get("prompt") or "[No student free text recorded]")
    with st.expander("AI tutor response", expanded=True):
        st.write(row.get("response") or "")
    if row.get("diagnostic"):
        with st.expander("Technical diagnostic"):
            st.code(str(row.get("diagnostic"))[:3000])

    st.markdown("### Expert rubric rating")
    st.caption("1 = poor/incorrect, 3 = acceptable/partial, 5 = excellent/highly appropriate")
    with st.form(f"llm_eval_{selected_id}"):
        c1, c2 = st.columns(2)
        with c1:
            conceptual_accuracy = st.slider("Conceptual accuracy", 1, 5, 3, help="Scientific correctness of quantum/Qiskit explanation.")
            answer_relevance = st.slider("Answer relevance", 1, 5, 3, help="How directly the response addresses the student's request.")
            pedagogical_clarity = st.slider("Pedagogical clarity", 1, 5, 3, help="Clarity and usefulness for an introductory learner.")
            scaffolding_quality = st.slider("Scaffolding quality", 1, 5, 3, help="Stepwise guidance rather than direct answer dumping.")
        with c2:
            qiskit_alignment = st.slider("Qiskit alignment", 1, 5, 3, help="Correctness and appropriateness of Qiskit examples or interpretation.")
            reflection_support = st.slider("Reflection support", 1, 5, 3, help="Encourages learner reflection and reduces over-reliance.")
            personalization = st.slider("Personalization", 1, 5, 3, help="Adapts to learner profile, pre-test weaknesses, or question language.")
        overall_comment = st.text_area("Evaluator comment", height=100, placeholder="Optional notes about strengths, errors, or pedagogical value.")
        submitted = st.form_submit_button("Save LLM evaluation", type="primary", use_container_width=True)
    if submitted:
        db.save_llm_evaluation(
            selected_id,
            secret("EVALUATOR_USERNAME", "evaluator"),
            conceptual_accuracy,
            answer_relevance,
            pedagogical_clarity,
            scaffolding_quality,
            qiskit_alignment,
            reflection_support,
            personalization,
            overall_comment,
        )
        st.success("LLM evaluation saved.")
        st.rerun()

    st.markdown("### Current LLM performance summary")
    summary = db.llm_evaluation_summary_df()
    if summary.empty:
        st.info("No expert ratings saved yet.")
    else:
        st.dataframe(summary, use_container_width=True, hide_index=True)
        render_progress_bars(summary, "metric", "mean_score", "Mean rating by criterion")

    with st.expander("Full saved evaluations"):
        saved = db.llm_evaluations_df()
        st.dataframe(saved, use_container_width=True, hide_index=True)


def render_feedback_logs() -> None:
    hero("Feedback Logs", "Review prompts, AI tutor responses, provider mode, and diagnostics recorded during the study.")
    options = db.ai_filter_options()
    if not any(options.values()) and db.count_rows("ai_interactions") == 0:
        st.info("No AI tutor interactions recorded yet.")
        return

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    mode_filter = c1.multiselect("Mode", options.get("mode", []))
    module_filter = c2.multiselect("Module", options.get("module", []))
    concept_filter = c3.multiselect("Concept", options.get("concept", []))
    max_rows = c4.selectbox("Rows", [50, 100, 200, 500], index=1)

    filtered = db.ai_logs_df(limit=max_rows, mode=mode_filter, module=module_filter, concept=concept_filter)
    if filtered.empty:
        st.info("No logs match the selected filters.")
        return
    st.caption(f"Showing up to {max_rows} most recent rows. Use Results Export to download the full dataset.")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    if "diagnostic" in filtered.columns:
        errors = filtered[filtered["mode"] == "llm_error"]
        if not errors.empty:
            st.markdown("### LLM error diagnostics")
            st.dataframe(errors[["created_at", "participant_code", "provider", "model", "diagnostic"]], use_container_width=True, hide_index=True)

def render_survey_results() -> None:
    hero("Survey Results", "Review usability questionnaire and open-ended feedback.")
    survey = db.survey_df()
    if survey.empty:
        st.info("No survey responses yet.")
        return
    rows = []
    open_rows = []
    for _, row in survey.iterrows():
        responses = json.loads(row.get("responses_json") or "{}")
        open_feedback = json.loads(row.get("open_feedback_json") or "{}")
        rows.append({"participant_code": row["participant_code"], "full_name": row["full_name"], **responses})
        open_rows.append({"participant_code": row["participant_code"], "full_name": row["full_name"], **open_feedback})
    likert_df = pd.DataFrame(rows)
    open_df = pd.DataFrame(open_rows)
    st.markdown("### Likert responses")
    st.dataframe(likert_df, use_container_width=True)
    numeric_cols = [key for key, _ in content.SURVEY_ITEMS if key in likert_df]
    if numeric_cols:
        st.write(likert_df[numeric_cols].describe())
        means = likert_df[numeric_cols].mean().reset_index()
        means.columns = ["item", "mean_score"]
        st.dataframe(means, use_container_width=True)
        render_progress_bars(means, "item", "mean_score", "Mean usability scores")
    st.markdown("### Open-ended feedback")
    st.dataframe(open_df, use_container_width=True)



def render_event_logs() -> None:
    hero("Event Logs", "Review sign-ins, sign-outs, test submissions, lesson completions, and survey submissions.")
    max_rows = st.selectbox("Rows to load", [50, 100, 200, 500], index=1)
    events = db.events_log_df(limit=max_rows)
    if events.empty:
        st.info("No platform events recorded yet.")
        return
    roles = sorted(events["actor_role"].dropna().unique().tolist())
    types = sorted(events["event_type"].dropna().unique().tolist())
    c1, c2 = st.columns(2)
    role_filter = c1.multiselect("Actor role", roles)
    type_filter = c2.multiselect("Event type", types)
    filtered = events.copy()
    if role_filter:
        filtered = filtered[filtered["actor_role"].isin(role_filter)]
    if type_filter:
        filtered = filtered[filtered["event_type"].isin(type_filter)]
    st.caption(f"Showing the latest {max_rows} events.")
    st.dataframe(filtered, use_container_width=True, hide_index=True)

def render_system_readiness() -> None:
    hero("System Readiness", "Non-destructive checks for the live pilot deployment on Streamlit Cloud and Neon.")
    readiness = db.system_readiness(len(content.LESSONS))
    provider = feedback_engine.provider_status()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Database OK", "Yes" if readiness.get("database_ok") else "No")
    c2.metric("DB dialect", readiness.get("database_dialect", "unknown"))
    c3.metric("App version", readiness.get("app_version", "unknown"))
    c4.metric("AI provider", provider.get("provider", "unknown"))

    if readiness.get("database_error"):
        st.error(readiness["database_error"])

    st.markdown("### Live counts")
    rows = []
    for key, value in readiness.items():
        if key.startswith("n_"):
            rows.append({"metric": key, "value": value})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("### Pilot-safety checks")
    checks = [
        {"check": "Using PostgreSQL/Neon, not local SQLite", "status": readiness.get("database_dialect") == "postgresql"},
        {"check": "Database connection succeeds", "status": bool(readiness.get("database_ok"))},
        {"check": "Pre/post attempts are now locked after first submission", "status": True},
        {"check": "Survey is now locked after first submission", "status": True},
        {"check": "Anonymized research export is available", "status": True},
    ]
    st.dataframe(pd.DataFrame(checks), use_container_width=True, hide_index=True)
    st.warning("Before changing database schema manually, download a backup from Results Export or Neon. These checks do not modify student data.")


def render_results_export() -> None:
    hero("Results Export", "Download pilot-safe study data without losing existing participant information.")
    st.info("Use the anonymized workbook for analysis and manuscript tables. Use the full backup only for secure administrative backup.")

    col_a, col_b = st.columns(2)
    with col_a:
        prepare_anon = st.button("Prepare anonymized research export", type="primary", use_container_width=True)
    with col_b:
        prepare_full = st.button("Prepare full admin backup", use_container_width=True)

    if prepare_anon:
        with st.spinner("Preparing anonymized workbook from Neon..."):
            dfs = db.research_export_tables(len(content.LESSONS), anonymized=True)
            st.session_state["export_tables"] = dfs
            st.session_state["export_excel"] = to_excel_bytes(dfs)
            st.session_state["export_filename"] = "qai_research_export_anonymized.xlsx"
            db.log_event(None, "evaluator", "anonymized_export_prepared", "Evaluator prepared anonymized research export")

    if prepare_full:
        with st.spinner("Preparing full administrative backup from Neon..."):
            dfs = {
                "students": db.students_df(),
                **db.research_export_tables(len(content.LESSONS), anonymized=False),
            }
            st.session_state["export_tables"] = dfs
            st.session_state["export_excel"] = to_excel_bytes(dfs)
            st.session_state["export_filename"] = "qai_full_admin_backup.xlsx"
            db.log_event(None, "evaluator", "full_backup_prepared", "Evaluator prepared full administrative backup")

    if "export_excel" in st.session_state:
        st.download_button(
            "Download prepared workbook",
            data=st.session_state["export_excel"],
            file_name=st.session_state.get("export_filename", "qai_export.xlsx"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
        dfs = st.session_state.get("export_tables", {})
        if dfs:
            st.markdown("### Preview")
            selected = st.selectbox("Dataset", list(dfs.keys()))
            preview = dfs[selected].head(200) if hasattr(dfs[selected], "head") else dfs[selected]
            st.dataframe(preview, use_container_width=True, hide_index=True)
            if hasattr(dfs[selected], "__len__") and len(dfs[selected]) > 200:
                st.caption(f"Preview shows first 200 rows out of {len(dfs[selected])}. Download the workbook for all rows.")

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> None:
    db.init_db()
    init_state()

    left_col, right_col = st.columns([0.28, 0.72], gap="large")
    with left_col:
        st.markdown("<div class='qai-app-sidebar'>", unsafe_allow_html=True)
        render_sidebar(st)
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        role = st.session_state.get("role")
        if role == "student":
            render_student_app()
        elif role == "evaluator":
            render_evaluator_app()
        else:
            render_role_selection()


if __name__ == "__main__":
    main()
