from __future__ import annotations

import io
import json
import secrets as py_secrets
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

import content
import db
import feedback_engine
from security import hash_password, verify_password

st.set_page_config(
    page_title="QAI Learning Evaluation Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Styling
# -----------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
:root {
  --qai-navy: #172042;
  --qai-teal: #0f7b79;
  --qai-soft: #f4f7fb;
  --qai-border: #d8e2ef;
  --qai-text: #0f172a;
}
.block-container {padding-top: 2rem; max-width: 1180px;}
[data-testid="stSidebar"] {background: #ffffff; border-right: 1px solid #eef2f7;}
.qai-hero {
  background: linear-gradient(120deg, var(--qai-navy), var(--qai-teal));
  color: white; padding: 2.3rem 2.5rem; border-radius: 1.5rem;
  margin-bottom: 1.5rem; box-shadow: 0 18px 40px rgba(15, 23, 42, 0.14);
}
.qai-hero h1 {font-size: 2.1rem; margin: 0 0 0.6rem 0; color: white;}
.qai-hero p {font-size: 1rem; margin: 0; opacity: 0.92;}
.qai-card {
  background: #ffffff; border: 1px solid var(--qai-border); border-radius: 1.1rem;
  padding: 1.25rem; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); margin-bottom: 1rem;
}
.qai-card h3, .qai-card h4 {margin-top: 0;}
.qai-pill {display: inline-block; padding: 0.28rem 0.7rem; border-radius: 999px; background: #e9efff; color: #263da8; font-weight: 600; font-size: 0.83rem; margin-bottom: 0.5rem;}
.qai-ok {background: #e8f7ee; color: #087443; padding: 0.9rem 1rem; border-radius: 0.8rem; border: 1px solid #bfe7cd;}
.qai-warn {background: #fff6db; color: #8a5a00; padding: 0.9rem 1rem; border-radius: 0.8rem; border: 1px solid #f5d47a;}
.qai-danger {background: #fdecec; color: #a72525; padding: 0.9rem 1rem; border-radius: 0.8rem; border: 1px solid #f4b7b7;}
.qai-muted {color: #64748b; font-size: 0.95rem;}
.qai-code {background: #f8fafc; padding: 1rem; border-radius: 0.8rem; border: 1px solid #e5e7eb; white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;}
div.stButton > button {border-radius: 0.8rem; min-height: 2.7rem;}
[data-testid="stMetric"] {background: #fff; border: 1px solid var(--qai-border); border-radius: 1rem; padding: 1rem; box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def init_state() -> None:
    defaults = {
        "role": None,
        "student_id": None,
        "student_page": "Student Home",
        "student_access_page": "Sign in",
        "evaluator_logged_in": False,
        "evaluator_page": "Evaluator Dashboard",
        "last_tutor_result": None,
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


def render_status_badge() -> None:
    status = feedback_engine.provider_status()
    if status["provider"] in ("gemini", "openai", "groq") and status["available"]:
        st.sidebar.success(f"AI tutor: {status['provider']} mode ({status['model']})")
    else:
        st.sidebar.info("AI tutor: local fallback mode")


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

def render_sidebar() -> None:
    st.sidebar.title("QAI Platform")
    role = st.session_state.get("role")

    if role == "student":
        student = current_student()
        if student:
            st.sidebar.success(f"Student: {student['participant_code']}")
        else:
            st.sidebar.info("No student signed in")
        st.sidebar.caption("Student menu")
        student_menu = student_pages_allowed(student)
        for page in student_menu:
            label = f"● {page}" if st.session_state.student_page == page else page
            if st.sidebar.button(label, key=f"student_nav_btn_{page}", use_container_width=True):
                st.session_state.student_page = page
                st.rerun()
        st.sidebar.divider()
        if student and st.sidebar.button("Sign out", use_container_width=True):
            db.log_event(student["id"], "student", "sign_out", "Student signed out from sidebar")
            st.session_state.student_id = None
            st.session_state.student_page = "Student Home"
            st.session_state.student_access_page = "Sign in"
            st.rerun()
        if st.sidebar.button("Switch role", use_container_width=True):
            switch_role(None)
        render_status_badge()

    elif role == "evaluator":
        st.sidebar.info("Evaluator workspace")
        if st.session_state.evaluator_logged_in:
            pages = [
                "Evaluator Dashboard",
                "Students",
                "Student Details",
                "Progress Monitor",
                "Learning Analytics",
                "Paper-ready Analysis",
                "Feedback Logs",
                "Survey Results",
                "Event Logs",
                "Results Export",
            ]
            st.sidebar.caption("Evaluator menu")
            for page in pages:
                label = f"● {page}" if st.session_state.evaluator_page == page else page
                if st.sidebar.button(label, key=f"eval_nav_btn_{page}", use_container_width=True):
                    st.session_state.evaluator_page = page
                    st.rerun()
            st.sidebar.divider()
            if st.sidebar.button("Sign out", use_container_width=True):
                db.log_event(None, "evaluator", "sign_out", "Evaluator signed out")
                st.session_state.evaluator_logged_in = False
                st.session_state.evaluator_page = "Evaluator Dashboard"
                st.rerun()
        if st.sidebar.button("Switch role", use_container_width=True):
            switch_role(None)
        render_status_badge()
    else:
        st.sidebar.info("Select a workspace to start.")


def student_pages_allowed(student: Optional[Dict[str, Any]]) -> List[str]:
    if not student:
        return ["Student Home", "Sign in", "Create account"]
    pages = ["Student Home", "Pre-test"]
    if test_is_done(student["id"], "pre"):
        pages += ["Adaptive Plan", "Learning Module", "AI Tutor Lab"]
    if all_lessons_done(student["id"]):
        pages += ["Post-test"]
    if test_is_done(student["id"], "post"):
        pages += ["Satisfaction Survey"]
    return pages

# -----------------------------------------------------------------------------
# Landing and access
# -----------------------------------------------------------------------------

def render_role_selection() -> None:
    hero("Quantum AI Learning Evaluation Platform", "Pilot platform for AI-supported introductory quantum programming with Qiskit.")
    col1, col2 = st.columns(2)
    with col1:
        card("Student workspace", "Create a study account or sign in to complete the pre-test, scaffolded learning activities, AI tutor tasks, post-test, and survey.", "For participants")
        if st.button("Enter as student", type="primary", use_container_width=True):
            switch_role("student")
    with col2:
        card("Evaluator workspace", "Monitor participant accounts, progress, pre/post scores, AI tutor logs, reflections, survey responses, and exports.", "For evaluator")
        if st.button("Enter as evaluator", use_container_width=True):
            switch_role("evaluator")


def render_student_app() -> None:
    student = current_student()
    page = st.session_state.student_page
    if page not in student_pages_allowed(student):
        st.session_state.student_page = "Student Home"
        page = "Student Home"
    if page == "Student Home":
        render_student_home(student)
    elif page == "Sign in":
        render_student_signin()
    elif page == "Create account":
        render_student_registration()
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
    hero("Student Workspace", "Complete the study stages in order. Your progress is saved automatically.")
    if not student:
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
    summary = db.progress_summary_df(len(content.LESSONS))
    row = summary[summary["student_id"] == student["id"]]
    progress = float(row["progress_percent"].iloc[0]) if not row.empty else 0.0
    st.progress(progress / 100, text=f"Overall progress: {progress:.0f}%")

    cols = st.columns(5)
    steps = [
        ("1", "Pre-test", test_is_done(student["id"], "pre")),
        ("2", "Adaptive Plan", db.get_recommendation(student["id"]) is not None),
        ("3", "Learning", all_lessons_done(student["id"])),
        ("4", "Post-test", test_is_done(student["id"], "post")),
        ("5", "Survey", db.get_survey(student["id"]) is not None),
    ]
    for col, (num, label, done) in zip(cols, steps):
        with col:
            st.metric(label=f"{num}. {label}", value="Done" if done else "Pending")

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Continue", type="primary", use_container_width=True):
            next_page = next_student_page(student)
            st.session_state.student_page = next_page
            st.rerun()
    with c2:
        if st.button("AI Tutor Lab", use_container_width=True, disabled=not test_is_done(student["id"], "pre")):
            set_student_page("AI Tutor Lab")
    with c3:
        if st.button("Sign out", use_container_width=True):
            db.log_event(student["id"], "student", "sign_out", "Student signed out from home")
            st.session_state.student_id = None
            st.session_state.student_page = "Student Home"
            st.rerun()


def next_student_page(student: Dict[str, Any]) -> str:
    sid = student["id"]
    if not test_is_done(sid, "pre"):
        return "Pre-test"
    if db.get_recommendation(sid) is None:
        return "Adaptive Plan"
    if not all_lessons_done(sid):
        return "Learning Module"
    if not test_is_done(sid, "post"):
        return "Post-test"
    if db.get_survey(sid) is None:
        return "Satisfaction Survey"
    return "Student Home"


def render_student_signin() -> None:
    hero("Student Sign in", "Access your existing participant account.")
    st.markdown("<div class='qai-card'>", unsafe_allow_html=True)
    with st.form("student_signin_form"):
        identifier = st.text_input("Participant code, email, or exact registered full name")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    if submitted:
        student = db.authenticate_student(identifier, password)
        if student:
            db.log_event(student["id"], "student", "sign_in", "Student signed in")
            st.session_state.student_id = student["id"]
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
            prior_python = st.slider("Prior Python level", 0, 3, 1, help="0 none, 1 basic, 2 intermediate, 3 advanced")
            prior_quantum = st.slider("Prior quantum knowledge", 0, 3, 0, help="0 none, 1 basic, 2 intermediate, 3 advanced")
        password = st.text_input("Password", type="password")
        password2 = st.text_input("Confirm password", type="password")
        study_code = ""
        if access_required:
            study_code = st.text_input("Study registration access code", type="password")
        consent = st.checkbox("I understand that my answers and interactions will be recorded for the pilot evaluation.")
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
            st.session_state.student_page = "Pre-test"
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
    if kind == "post" and not all_lessons_done(student["id"]):
        st.warning("Please complete the learning module before the post-test.")
        return
    existing = db.get_test_attempt(student["id"], kind)
    if existing:
        st.success(f"{title} already submitted. Score: {existing['score']:.1f}%")
        if st.button("Continue", type="primary"):
            if kind == "pre":
                st.session_state.student_page = "Adaptive Plan"
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
        db.log_ai_interaction(
            student["id"], "adaptive_plan", "Adaptive learning", "Generate personalized study plan",
            "Generate a concise study plan based on pre-test results.", tutor.response, tutor.mode, tutor.provider, tutor.model, tutor.diagnostic,
        )
        st.markdown("### AI-generated study plan")
        st.write(tutor.response)
        if tutor.mode == "llm_error":
            st.info("The LLM service was unavailable, so a local fallback was shown and logged for the evaluator.")
    if st.button("Start learning module", use_container_width=True):
        set_student_page("Learning Module")


def render_learning_module(student: Dict[str, Any]) -> None:
    hero("Scaffolded Qiskit Learning Module", "Each section combines conceptual scaffolding, a guided Qiskit example, AI-mediated support, and a reflective prompt.")
    rec = db.get_recommendation(student["id"])
    recommended_set = set(rec.get("recommended_lessons", [])) if rec else set()
    progress = db.get_lesson_progress(student["id"])
    completed = set(progress[progress["completed"] == 1]["lesson_id"].tolist()) if not progress.empty else set()

    lesson_titles = [lesson["title"] + (" ★" if lesson["id"] in recommended_set else "") for lesson in content.LESSONS]
    selected_title = st.selectbox("Select a learning section", lesson_titles)
    lesson_index = lesson_titles.index(selected_title)
    lesson = content.LESSONS[lesson_index]

    if lesson["id"] in completed:
        st.success("This section is marked as completed.")
    elif lesson["id"] in recommended_set:
        st.info("Recommended based on your pre-test results.")

    st.markdown(f"## {lesson['title']}")
    col1, col2 = st.columns([1.1, 1])
    with col1:
        st.markdown("<div class='qai-card'>", unsafe_allow_html=True)
        st.markdown("#### Learning objective")
        st.write(lesson["objective"])
        st.markdown("#### Conceptual scaffold")
        st.write(lesson["concept"])
        st.markdown("#### Why it matters")
        st.write(lesson["why_it_matters"])
        st.markdown("#### Misconception to avoid")
        st.warning(lesson["misconception"])
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='qai-card'>", unsafe_allow_html=True)
        st.markdown("#### Guided Qiskit example")
        st.code(lesson["qiskit_code"], language="python")
        st.markdown("#### Before measurement")
        st.write(lesson["before_measurement"])
        st.markdown("#### After measurement")
        st.write(lesson["after_measurement"])
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### AI-supported activity")
    activity_language = st.selectbox(
        "AI response language",
        ["Auto-detect", "English", "Arabic", "French"],
        index=0,
        key=f"lesson_ai_language_{lesson['id']}",
        help="Choose Arabic if you want the tutor to explain this learning activity in Arabic.",
    )
    c1, c2, c3 = st.columns(3)
    task = None
    if c1.button("Generate guided explanation", use_container_width=True):
        task = "Explain a concept"
    if c2.button("Generate practice exercise", use_container_width=True):
        task = "Generate a practice exercise"
    if c3.button("Ask for a hint", use_container_width=True):
        task = "Give a hint without the full answer"
    if task:
        tutor = feedback_engine.generate_tutor_response(
            task=task,
            concept=", ".join(lesson["concepts"]),
            student_input=f"Lesson: {lesson['title']}",
            student_profile=student_profile(student),
            lesson_context={**lesson, "response_language": activity_language},
        )
        db.log_ai_interaction(
            student["id"], "learning_module", ", ".join(lesson["concepts"]), task,
            f"Lesson activity for {lesson['title']}", tutor.response, tutor.mode, tutor.provider, tutor.model, tutor.diagnostic,
        )
        st.markdown("#### AI tutor response")
        st.write(tutor.response)

    st.divider()
    st.markdown("### Reflection prompt")
    st.info(lesson["reflective_prompt"])
    reflection_default = ""
    if not progress.empty:
        row = progress[progress["lesson_id"] == lesson["id"]]
        if not row.empty:
            reflection_default = str(row["reflection_text"].iloc[0] or "")
    with st.form(f"reflection_{lesson['id']}"):
        reflection = st.text_area("Write your reflection in your own words", value=reflection_default, height=140)
        submitted = st.form_submit_button("Save reflection and mark section complete", type="primary")
    if submitted:
        if len(reflection.strip()) < 20:
            st.error("Please write a short reflection before marking the section complete.")
        else:
            db.save_lesson_progress(student["id"], lesson["id"], reflection, completed=True)
            db.log_event(student["id"], "student", "lesson_completed", lesson["id"])
            st.success("Reflection saved. Section completed.")
            st.rerun()

    if all_lessons_done(student["id"]):
        st.success("All sections are completed. You can continue to the post-test.")
        if st.button("Go to post-test", type="primary"):
            set_student_page("Post-test")


def render_ai_tutor_lab(student: Dict[str, Any]) -> None:
    hero("AI Tutor Lab", "Use the tutor for explanation, feedback, exercise generation, and Qiskit interpretation. Write your own reasoning before relying on generated answers.")
    status = feedback_engine.provider_status()
    if status["available"]:
        st.success(f"LLM provider configured: {status['provider']} ({status['model']})")
    else:
        st.info("No external LLM is configured. The lab will use a local formative fallback.")

    task = st.selectbox(
        "Tutor task",
        ["Explain a concept", "Generate a practice exercise", "Check my explanation", "Debug or interpret Qiskit code"],
    )
    tutor_language = st.selectbox(
        "Tutor response language",
        ["Auto-detect", "English", "Arabic", "French"],
        index=0,
        help="Auto-detect uses the language of your question. Select Arabic to force Arabic responses.",
    )
    concepts = sorted({c for lesson in content.LESSONS for c in lesson["concepts"]})
    concept = st.selectbox("Concept focus", concepts)
    prompt = st.text_area("Your question, explanation, or Qiskit code", height=180, placeholder="Example: Please explain this in Arabic because I did not understand the concept.")
    st.caption("For research validity, write your current understanding first. The tutor is designed to guide, not replace, your reasoning. The tutor should answer in the selected language or the language of your question.")
    if st.button("Ask AI tutor", type="primary", use_container_width=True):
        if not prompt.strip() and task in ["Check my explanation", "Debug or interpret Qiskit code"]:
            st.warning("Please write your explanation or code first.")
            return
        tutor = feedback_engine.generate_tutor_response(
            task=task,
            concept=concept,
            student_input=prompt,
            student_profile=student_profile(student),
            lesson_context={"source": "AI Tutor Lab", "response_language": tutor_language},
        )
        db.log_ai_interaction(
            student["id"], "ai_tutor_lab", concept, task, prompt, tutor.response, tutor.mode, tutor.provider, tutor.model, tutor.diagnostic
        )
        st.markdown("### AI tutor response")
        st.write(tutor.response)
        if tutor.mode == "llm_error":
            st.info("The external LLM was unavailable. A local hint was shown and the error was logged for the evaluator.")


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
        st.success("Thank you. Your responses have been recorded.")
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
    elif page == "Student Details":
        render_student_details()
    elif page == "Progress Monitor":
        render_progress_monitor()
    elif page == "Learning Analytics":
        render_learning_analytics()
    elif page == "Paper-ready Analysis":
        render_paper_ready_analysis()
    elif page == "Feedback Logs":
        render_feedback_logs()
    elif page == "Survey Results":
        render_survey_results()
    elif page == "Event Logs":
        render_event_logs()
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
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Students", len(df))
    c2.metric("Pre-tests", int(df["pre_done"].sum()) if not df.empty else 0)
    c3.metric("Post-tests", int(df["post_done"].sum()) if not df.empty else 0)
    c4.metric("Surveys", survey_count)
    c5.metric("AI logs", ai_count)

    status = feedback_engine.provider_status()
    st.markdown("### AI tutor configuration")
    st.write({
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
        recent = df[["participant_code", "full_name", "academic_level", "pre_score", "post_score", "learning_gain", "progress_percent", "ai_interactions"]].head(30)
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

    st.markdown("### Lesson reflections")
    progress = db.get_lesson_progress(student["id"])
    st.dataframe(progress, use_container_width=True)

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
    st.dataframe(df[["participant_code", "full_name", "pre_done", "completed_lessons", "post_done", "survey_done", "progress_percent", "ai_interactions"]], use_container_width=True)
    render_progress_bars(df, "participant_code", "progress_percent", "Completion progress")


def render_learning_analytics() -> None:
    hero("Learning Analytics", "Analyze pre/post scores, concept-level performance, and learning gain.")
    df = db.progress_summary_df(len(content.LESSONS))
    if df.empty:
        st.info("No student data yet.")
        return
    st.markdown("### Score summary")
    show = df[["participant_code", "full_name", "pre_score", "post_score", "learning_gain", "completed_lessons", "ai_interactions"]]
    st.dataframe(show, use_container_width=True)
    numeric = show[["pre_score", "post_score", "learning_gain", "completed_lessons", "ai_interactions"]].dropna(how="all")
    if not numeric.empty:
        st.write(numeric.describe())
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
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Registered", len(progress))
    c2.metric("Pre-tests", int(progress["pre_done"].sum()))
    c3.metric("Post-tests", int(progress["post_done"].sum()))
    c4.metric("Complete pairs", len(complete))
    c5.metric("Surveys", len(survey))

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
    }
    st.download_button(
        "Download paper-ready analysis workbook",
        data=to_excel_bytes(export_tables),
        file_name="qai_paper_ready_analysis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )


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

def render_results_export() -> None:
    hero("Results Export", "Download anonymized study data for statistical analysis and paper reporting.")
    st.info("To keep the cloud app fast, full export tables are prepared only when you click the button below.")

    if st.button("Prepare full export workbook", type="primary"):
        with st.spinner("Preparing workbook from the database..."):
            dfs = {
                "students": db.students_df(),
                "progress_summary": db.progress_summary_df(len(content.LESSONS)),
                "test_attempts": db.attempts_df(),
                "question_responses": db.question_responses_df(),
                "concept_scores": db.concept_scores_df(),
                "lesson_reflections": db.query_df("SELECT * FROM lesson_progress"),
                "ai_interactions": db.ai_logs_df(),
                "surveys": db.survey_df(),
                "consent_records": db.consent_records_df(),
                "event_logs": db.events_log_df(),
            }
            st.session_state["export_tables"] = dfs
            st.session_state["export_excel"] = to_excel_bytes(dfs)

    if "export_excel" in st.session_state:
        st.download_button(
            "Download Excel workbook",
            data=st.session_state["export_excel"],
            file_name="qai_study_export.xlsx",
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
    render_sidebar()
    role = st.session_state.get("role")
    if role == "student":
        render_student_app()
    elif role == "evaluator":
        render_evaluator_app()
    else:
        render_role_selection()


if __name__ == "__main__":
    main()
