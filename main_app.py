from __future__ import annotations

import io
import json
import secrets as py_secrets
import smtplib
import ssl
import time
from email.message import EmailMessage
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

import content
import db
import feedback_engine
import branding
import i18n
import router
from content_locales import MEDIA_TRANSLATIONS
from security import hash_password, verify_password
from media_utils import render_image, render_video, render_simulator, render_micro_animation

APP_DIR = Path(__file__).resolve().parent
LESSON_MEDIA_DIR = APP_DIR / "assets" / "lesson_media"
INTERACTIVE_MEDIA_DIR = LESSON_MEDIA_DIR / "interactive"
ANIMATION_MEDIA_DIR = LESSON_MEDIA_DIR / "animations"

LESSON_MEDIA = {
    "orientation": {
        "caption": "Code-to-circuit map: qubit wire, measurement symbol, and classical output bit.",
        "notice": "Follow the code, then the visual circuit, then the classical output. This makes the quantum/classical boundary visible.",
        "resource_label": "IBM Quantum Learning",
        "resource_url": "https://quantum.cloud.ibm.com/learning/en",
    },
    "qubit_measurement": {
        "caption": "Measurement transforms a prepared quantum state into one classical outcome per shot.",
        "notice": "The important transition is not from code to printout, but from quantum state to classical data.",
        "resource_label": "IBM Quantum documentation: visualization",
        "resource_url": "https://quantum.cloud.ibm.com/docs/en/api/qiskit/visualization",
    },
    "hadamard_superposition": {
        "caption": "Hadamard prepares a balanced probability pattern; the histogram reveals it after repeated shots.",
        "notice": "Compare the state before H, the state after H, and the approximate 50/50 counts after measurement.",
        "resource_label": "Bloch sphere explanation",
        "resource_url": "https://qiskit.qotlabs.org/learning/courses/general-formulation-of-quantum-information/density-matrices/bloch-sphere",
    },
    "shots_counts": {
        "caption": "Counts are sampled frequencies. More shots generally make the distribution clearer.",
        "notice": "Compare 10 shots with 1000 shots: both are samples, but one is much easier to interpret.",
        "resource_label": "Qiskit guide: visualize results",
        "resource_url": "https://qiskit.qotlabs.org/docs/guides/visualize-results",
    },
    "cnot_correlation": {
        "caption": "CNOT uses a control and a target; with H it can produce correlated two-bit outcomes.",
        "notice": "Use the rule table before interpreting the two-qubit histogram. The target flips only when the control is 1.",
        "resource_label": "Microsoft Quantum Katas",
        "resource_url": "https://quantum.microsoft.com/en-us/tools/quantum-katas",
    },
    "qiskit_debugging": {
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


def bool_secret(name: str, default: str = "false") -> bool:
    return secret(name, default).strip().lower() in {"1", "true", "yes", "on"}


def control_group_enabled() -> bool:
    """Optional RCT-style study design switch.

    Default is off to protect ongoing single-arm pilot data. When enabled,
    new students are balanced between control and experimental groups.
    """
    return bool_secret("ENABLE_CONTROL_GROUP", "false")


def study_group_label(student: Optional[Dict[str, Any]]) -> str:
    if not student:
        return "single_arm"
    group = str(student.get("study_group") or "single_arm").strip().lower()
    if control_group_enabled() and group not in {"control", "experimental"}:
        try:
            group = db.assign_study_group(int(student["id"]))
            student["study_group"] = group
        except Exception:
            group = "experimental"
    if not control_group_enabled() and group in {"", "none", "null"}:
        group = "single_arm"
    return group


def is_control_student(student: Optional[Dict[str, Any]]) -> bool:
    return control_group_enabled() and study_group_label(student) == "control"


def ai_features_available(student: Optional[Dict[str, Any]]) -> bool:
    return not is_control_student(student)


def ai_requirement_met(student: Dict[str, Any]) -> bool:
    """Control students should not be forced to use AI before the post-test."""
    if is_control_student(student):
        return True
    return has_minimum_ai_interaction(student["id"])


def current_app_base_url() -> str:
    """Return the public URL used in password reset emails."""
    base = secret("APP_BASE_URL", "").strip().rstrip("/")
    if base:
        return base
    # Fallback is useful for local testing; set APP_BASE_URL in Streamlit Cloud for production.
    return "http://localhost:8501"


def smtp_is_configured() -> bool:
    return bool(secret("SMTP_HOST", "").strip() and secret("SMTP_USERNAME", "").strip() and secret("SMTP_PASSWORD", "").strip())


def send_password_reset_email(
    to_email: str,
    full_name: str,
    reset_link: str,
    expires_minutes: int = 30,
    language: str = "en",
) -> Tuple[bool, str]:
    """Send a one-time password reset link in the learner's preferred language."""
    host = secret("SMTP_HOST", "").strip()
    port = int(secret("SMTP_PORT", "587") or 587)
    username = secret("SMTP_USERNAME", "").strip()
    password = secret("SMTP_PASSWORD", "").strip()
    sender = secret("SMTP_FROM", username).strip() or username
    use_ssl = secret("SMTP_USE_SSL", "false").strip().lower() in {"1", "true", "yes"}

    if not (host and username and password and sender):
        return False, "SMTP email is not configured."

    lang = i18n.normalize_lang(language)
    subjects = {
        "ar": "إعادة تعيين كلمة مرور 3alimnIA",
        "fr": "Réinitialisation du mot de passe 3alimnIA",
        "en": "3alimnIA password reset",
    }
    bodies = {
        "ar": (
            f"مرحبًا {full_name}،\n\n"
            "تلقينا طلبًا لإعادة تعيين كلمة مرور حسابك في منصة 3alimnIA التعليمية.\n\n"
            f"استخدم الرابط الآتي لإنشاء كلمة مرور جديدة:\n{reset_link}\n\n"
            f"يبقى هذا الرابط صالحًا لمدة {expires_minutes} دقيقة، ويمكن استعماله مرة واحدة فقط.\n"
            "إن لم تطلب إعادة التعيين، يمكنك تجاهل هذه الرسالة.\n\n"
            "منصة 3alimnIA التعليمية"
        ),
        "fr": (
            f"Bonjour {full_name},\n\n"
            "Nous avons reçu une demande de réinitialisation du mot de passe de votre compte sur la plateforme 3alimnIA.\n\n"
            f"Utilisez ce lien pour créer un nouveau mot de passe :\n{reset_link}\n\n"
            f"Ce lien reste valide pendant {expires_minutes} minutes et ne peut être utilisé qu'une seule fois.\n"
            "Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer ce message.\n\n"
            "Plateforme d'apprentissage 3alimnIA"
        ),
        "en": (
            f"Hello {full_name},\n\n"
            "We received a request to reset your password for the 3alimnIA learning platform.\n\n"
            f"Reset your password using this link:\n{reset_link}\n\n"
            f"This link is valid for {expires_minutes} minutes and can be used only once.\n"
            "If you did not request this reset, you can ignore this email.\n\n"
            "3alimnIA Learning Platform"
        ),
    }

    msg = EmailMessage()
    msg["Subject"] = subjects[lang]
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(bodies[lang])

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
        "landing_track": "quantum",
        "selected_track": "quantum",
        "ui_language": "العربية",
        "ui_language_code": "ar",
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def render_language_selector(target=st, key: str = "global_language_selector", label_visibility: str = "visible") -> str:
    """Render a persistent language selector and save it to the learner account."""
    current = i18n.current_lang(st)
    labels = list(i18n.LANGUAGE_LABELS.values())
    current_label = i18n.LANGUAGE_LABELS.get(current, "العربية")
    selected = target.selectbox(
        i18n.tr("Language"),
        labels,
        index=labels.index(current_label) if current_label in labels else 0,
        key=key,
        label_visibility=label_visibility,
    )
    code = i18n.normalize_lang(selected)
    changed = code != current
    st.session_state.ui_language_code = code
    st.session_state.ui_language = i18n.LANGUAGE_LABELS[code]
    student = current_student()
    if student and str(student.get("preferred_language") or "") != code:
        try:
            db.set_student_preferred_language(int(student["id"]), code)
            student["preferred_language"] = code
        except Exception:
            pass
    if changed:
        request_scroll_top()
        st.rerun()
    return code


def localized_lessons() -> List[Dict[str, Any]]:
    return content.lessons_for(i18n.current_lang(st))


def localized_media(lesson_id: str) -> Dict[str, Any]:
    item = dict(LESSON_MEDIA.get(lesson_id, {}))
    code = i18n.current_lang(st)
    if code != "en":
        item.update(MEDIA_TRANSLATIONS.get(code, {}).get(lesson_id, {}))
    return item


def request_scroll_top() -> None:
    """Request a one-shot top-of-page reset after navigation or language changes."""
    st.session_state["_v4_scroll_top_requested"] = True


def perform_scroll_top_if_requested() -> None:
    """Reset the parent Streamlit page scroll position once, then clear the flag."""
    if not st.session_state.pop("_v4_scroll_top_requested", False):
        return
    components.html(
        """
        <script>
        try {
          window.parent.scrollTo({ top: 0, left: 0, behavior: 'instant' });
        } catch (e) {
          window.parent.scrollTo(0, 0);
        }
        </script>
        """,
        height=0,
        width=0,
    )


def switch_role(role: Optional[str] = None) -> None:
    request_scroll_top()
    st.session_state.role = role
    st.session_state.student_page = "Student Home"
    st.session_state.student_access_page = "Sign in"
    st.session_state.evaluator_page = "Evaluator Dashboard"
    st.session_state["_v411_history"] = []
    st.session_state["_v411_current_route"] = None
    if role == "student":
        router.queue(router.route_key("student", "Student Home"))
    elif role == "evaluator":
        router.queue(router.route_key("evaluator", "Evaluator Dashboard"))
    else:
        router.queue(router.route_key("public", "home"))
    st.rerun()


def set_student_page(page: str) -> None:
    st.session_state.student_page = page
    request_scroll_top()
    router.navigate(router.route_key("student", page))


def set_evaluator_page(page: str) -> None:
    st.session_state.evaluator_page = page
    request_scroll_top()
    router.navigate(router.route_key("evaluator", page))


def change_account_callback() -> None:
    """Reliable native callback used by the global account toolbar."""
    role = st.session_state.get("role")
    if role == "student":
        student = current_student()
        if student:
            try:
                db.log_event(student["id"], "student", "sign_out", "Student changed account from native toolbar")
            except Exception:
                pass
        st.session_state.student_id = None
        st.session_state.student_page = "Sign in"
        router.queue(router.route_key("student", "Sign in"))
    elif role == "evaluator":
        st.session_state.evaluator_logged_in = False
        st.session_state.evaluator_page = "Evaluator Dashboard"
        router.queue(router.route_key("evaluator", "Evaluator Dashboard"))
    request_scroll_top()


def switch_workspace_callback() -> None:
    """Return to the public workspace chooser without relying on a sidebar."""
    st.session_state.role = None
    st.session_state.student_page = "Student Home"
    st.session_state.evaluator_page = "Evaluator Dashboard"
    router.queue(router.route_key("public", "home"))
    request_scroll_top()


def logout_callback() -> None:
    """End the active workspace session and return to the public home page."""
    role = st.session_state.get("role")
    if role == "student":
        student = current_student()
        if student:
            try:
                db.log_event(student["id"], "student", "sign_out", "Student signed out from native toolbar")
            except Exception:
                pass
        st.session_state.student_id = None
    elif role == "evaluator":
        st.session_state.evaluator_logged_in = False
    st.session_state.role = None
    st.session_state.student_page = "Student Home"
    st.session_state.evaluator_page = "Evaluator Dashboard"
    router.queue(router.route_key("public", "home"))
    request_scroll_top()


def _v411_navigation_copy() -> Dict[str, str]:
    """Short, stable labels for the always-visible escape/navigation bar."""
    lang = i18n.current_lang(st)
    values = {
        "ar": {
            "page": "الانتقال إلى",
            "menu": "القائمة",
            "back": "رجوع",
            "home": "الرئيسية",
            "account": "تغيير الحساب",
            "logout": "خروج",
            "student": "فضاء المتعلم",
            "evaluator": "فضاء المقيّم",
        },
        "fr": {
            "page": "Aller à",
            "menu": "Menu",
            "back": "Retour",
            "home": "Accueil",
            "account": "Changer de compte",
            "logout": "Quitter",
            "student": "Espace apprenant",
            "evaluator": "Espace évaluateur",
        },
        "en": {
            "page": "Go to",
            "menu": "Menu",
            "back": "Back",
            "home": "Home",
            "account": "Change account",
            "logout": "Exit",
            "student": "Learner workspace",
            "evaluator": "Evaluator workspace",
        },
    }
    return values.get(lang, values["en"])


def _v411_current_route() -> Tuple[Optional[str], Optional[str]]:
    role = st.session_state.get("role")
    if role == "student":
        return role, st.session_state.get("student_page", "Student Home")
    if role == "evaluator":
        return role, st.session_state.get("evaluator_page", "Evaluator Dashboard")
    return None, None


def _v411_record_route() -> None:
    """Keep a lightweight in-app page history without using browser history."""
    role, page = _v411_current_route()
    token = (role, page)
    previous = st.session_state.get("_v411_current_route")
    suppress = bool(st.session_state.pop("_v411_suppress_history", False))
    if previous and previous != token and not suppress:
        history = list(st.session_state.get("_v411_history", []))
        if not history or history[-1] != previous:
            history.append(previous)
        st.session_state["_v411_history"] = history[-20:]
    st.session_state["_v411_current_route"] = token


def _v411_go_back() -> None:
    history = list(st.session_state.get("_v411_history", []))
    current_role = st.session_state.get("role")
    while history:
        role, page = history.pop()
        if role not in {"student", "evaluator"} or not page:
            continue
        # Keep role changes explicit; Back navigates inside the current workspace.
        if role != current_role:
            continue
        st.session_state["_v411_history"] = history
        st.session_state["_v411_suppress_history"] = True
        if role == "student":
            st.session_state.student_page = page
        else:
            st.session_state.evaluator_page = page
        request_scroll_top()
        st.rerun()
    # There is no earlier in-workspace page: return to the workspace home.
    if current_role == "student":
        st.session_state.student_page = "Student Home"
    elif current_role == "evaluator":
        st.session_state.evaluator_page = "Evaluator Dashboard"
    request_scroll_top()
    st.rerun()


def _v411_change_account() -> None:
    """Sign out of the active account while keeping the same workspace login."""
    role = st.session_state.get("role")
    if role == "student":
        student = current_student()
        if student:
            try:
                db.log_event(student["id"], "student", "sign_out", "Student changed account from global navigation")
            except Exception:
                pass
        st.session_state.student_id = None
        st.session_state.student_page = "Sign in"
    elif role == "evaluator":
        st.session_state.evaluator_logged_in = False
        st.session_state.evaluator_page = "Evaluator Dashboard"
    st.session_state["_v411_history"] = []
    st.session_state["_v411_current_route"] = None
    request_scroll_top()
    st.rerun()


def _v411_exit_platform() -> None:
    """Close the active session and return to the public landing page."""
    role = st.session_state.get("role")
    if role == "student":
        student = current_student()
        if student:
            try:
                db.log_event(student["id"], "student", "sign_out", "Student exited platform from global navigation")
            except Exception:
                pass
        st.session_state.student_id = None
    elif role == "evaluator":
        st.session_state.evaluator_logged_in = False
    st.session_state.role = None
    st.session_state.student_page = "Student Home"
    st.session_state.evaluator_page = "Evaluator Dashboard"
    st.session_state["_v411_history"] = []
    st.session_state["_v411_current_route"] = None
    request_scroll_top()
    st.rerun()


def _v411_open_sidebar() -> None:
    """Ask Streamlit's native collapsed-sidebar control to reopen the rail."""
    components.html(
        """
        <script>
        try {
          const doc = window.parent.document;
          const selectors = [
            '[data-testid="stSidebarCollapsedControl"] button',
            '[data-testid="collapsedControl"] button',
            'button[data-testid="stSidebarCollapsedControl"]'
          ];
          let button = null;
          for (const selector of selectors) {
            button = doc.querySelector(selector);
            if (button) break;
          }
          if (button) button.click();
        } catch (error) { console.debug('3alimnIA sidebar open fallback', error); }
        </script>
        """,
        height=0,
        width=0,
    )


def render_global_escape_navigation() -> None:
    """Always-visible navigation so no user can become trapped in a page.

    The native sidebar remains the full navigation rail. This compact bar is a
    safety layer that exposes page switching, back, home, account change and
    exit even when the sidebar is collapsed by the browser or Streamlit.
    """
    role, current_page = _v411_current_route()
    if role not in {"student", "evaluator"} or not current_page:
        return
    _v411_record_route()
    lang = i18n.current_lang(st)
    copy = _v411_navigation_copy()
    direction = i18n.direction(lang)

    if role == "student":
        student = current_student()
        pages = student_pages_allowed(student)
        if not student:
            pages = ["Sign in", "Create account"]
        home_page = "Student Home"
        workspace_label = copy["student"]
    else:
        pages = [
            "Evaluator Dashboard", "Study Protocol", "Students",
            "Registration Accounts", "Student Details", "AI Tutor Logs",
            "AI Response Evaluation", "AI Metrics", "Exports",
        ] if st.session_state.get("evaluator_logged_in") else ["Evaluator Dashboard"]
        home_page = "Evaluator Dashboard"
        workspace_label = copy["evaluator"]

    if current_page not in pages:
        pages = [current_page, *pages]
    # Deduplicate while preserving the intended order.
    pages = list(dict.fromkeys(pages))

    with st.container(border=True):
        st.markdown(
            f"<span class='v411-global-nav-marker' aria-hidden='true'></span>"
            f"<div class='v411-workspace-label' dir='{direction}'>{escape(workspace_label)}</div>",
            unsafe_allow_html=True,
        )
        nav_col, menu_col, back_col, home_col, account_col, exit_col = st.columns(
            [2.7, 1.0, .95, 1.05, 1.35, .9], gap="small"
        )
        with nav_col:
            selected_page = st.selectbox(
                copy["page"],
                pages,
                index=pages.index(current_page),
                format_func=lambda page: i18n.page_label(page, lang),
                key=f"v411_route_{role}_{current_page}",
                label_visibility="collapsed",
            )
            if selected_page != current_page:
                if role == "student":
                    st.session_state.student_page = selected_page
                else:
                    st.session_state.evaluator_page = selected_page
                request_scroll_top()
                st.rerun()
        with menu_col:
            if st.button(f"☰ {copy['menu']}", key=f"v411_menu_{role}_{current_page}", use_container_width=True):
                _v411_open_sidebar()
        with back_col:
            if st.button(f"↩ {copy['back']}", key=f"v411_back_{role}_{current_page}", use_container_width=True):
                _v411_go_back()
        with home_col:
            if st.button(f"⌂ {copy['home']}", key=f"v411_home_{role}_{current_page}", use_container_width=True):
                if role == "student":
                    st.session_state.student_page = home_page
                else:
                    st.session_state.evaluator_page = home_page
                request_scroll_top()
                st.rerun()
        with account_col:
            if st.button(f"⇄ {copy['account']}", key=f"v411_account_{role}_{current_page}", use_container_width=True):
                _v411_change_account()
        with exit_col:
            if st.button(f"⎋ {copy['logout']}", key=f"v411_exit_{role}_{current_page}", use_container_width=True):
                _v411_exit_platform()


def hero(title: str, subtitle: str, *, localized: bool = False, compact: Optional[bool] = None) -> None:
    """Render a language-aware premium page header used across the platform.

    Use ``localized=True`` when text was already selected from a locale-specific
    dictionary. This prevents phrase replacement from producing mixed-language
    titles such as Arabic text with a remaining English word.

    Evaluator pages use a compact header automatically so the operational
    controls remain visible on laptop screens. Callers may override this with
    ``compact=True`` or ``compact=False`` when a page needs a different density.
    """
    lang = i18n.current_lang(st)
    direction = i18n.direction(lang)
    safe_title = escape(title if localized else i18n.tr(title))
    safe_subtitle = escape(subtitle if localized else i18n.tr(subtitle))
    if compact is None:
        compact = st.session_state.get("role") == "evaluator"
    compact_class = " v47-page-hero-compact" if compact else ""
    st.markdown(
        f"""
        <section class="qai-hero v4-page-hero{compact_class}" dir="{direction}">
          <div class="v4-page-hero-glow"></div>
          <div class="v4-page-hero-kicker">3alimnIA · {escape(branding.BRAND_NAME_AR)}</div>
          <h1>{safe_title}</h1>
          <p>{safe_subtitle}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def card(title: str, body: str, pill: Optional[str] = None) -> None:
    lang = i18n.current_lang(st)
    direction = i18n.direction(lang)
    pill_html = f'<span class="qai-pill">{escape(i18n.tr(pill))}</span>' if pill else ""
    st.markdown(
        f"""
        <article class="qai-card v4-content-card" dir="{direction}">
          {pill_html}
          <h3>{escape(i18n.tr(title))}</h3>
          <p>{escape(i18n.tr(body))}</p>
        </article>
        """,
        unsafe_allow_html=True,
    )


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
    student = db.get_student(int(sid))
    if student and control_group_enabled():
        group = study_group_label(student)
        student["study_group"] = group
    return student


def student_profile(student: Dict[str, Any]) -> Dict[str, Any]:
    pre = db.get_test_attempt(student["id"], "pre")
    rec = db.get_recommendation(student["id"])
    progress = db.get_lesson_progress(student["id"])
    return {
        "participant_code": student.get("participant_code"),
        "academic_level": student.get("academic_level"),
        "prior_python_level": student.get("prior_python_level"),
        "prior_quantum_level": student.get("prior_quantum_level"),
        "preferred_language": i18n.response_language(student.get("preferred_language", i18n.current_lang(st))),
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
        ("4. AI support", ai_requirement_met(student), "Experimental group: use AI once. Control group: AI is intentionally hidden."),
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
    u = learning_ui_copy()
    lesson_count = lesson_completion_count(student["id"])
    required = required_lesson_count_for_posttest()
    learning_pct = int(round(100 * lesson_count / max(required, 1)))
    current_id = current_or_resume_lesson_id(student["id"]) if test_is_done(student["id"], "pre") else ""
    current_title = next((x.get("short_title", x["title"]) for x in localized_lessons() if x["id"] == current_id), "—")
    items = completion_items(student)
    study_pct = int(round(100 * sum(1 for _, ok, _ in items if ok) / max(len(items), 1)))
    st.markdown(f"""
    <section class='v43-topbar' dir='{u['dir']}'>
      <div><span>{escape(u['journey'])}</span><b>{escape(i18n.page_label(page, i18n.current_lang(st)))}</b></div>
      <div><span>{escape(u['current'])}</span><b>{escape(str(current_title))}</b></div>
      <div class='v43-topbar-meter'><div><b>{learning_pct}%</b><span>{escape(u['modules_done'])}: {lesson_count}/{required}</span></div><i><em style='width:{learning_pct}%'></em></i></div>
      <div class='v43-topbar-study'><b>{study_pct}%</b><span>{escape(u['overall'])}</span></div>
    </section>""", unsafe_allow_html=True)

def render_completion_requirements(student: Dict[str, Any], compact: bool = False) -> None:
    items = completion_items(student)
    done_count = sum(1 for _, ok, _ in items if ok)

    # Use a native container so the progress bar, next action, and workflow
    # cards are structurally grouped. Opening an HTML <div> before Streamlit
    # widgets does not wrap later widgets and previously produced a visually
    # fragmented roadmap.
    with st.container(border=True, key="v681_roadmap"):
        st.markdown("<div class='qai-roadmap-title'>Study roadmap</div>", unsafe_allow_html=True)
        st.progress(done_count / len(items), text=f"Required workflow progress: {done_count}/{len(items)}")
        st.markdown(f"<div class='qai-next-action'><b>{next_action_text(student)}</b></div>", unsafe_allow_html=True)
        if compact:
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




def record_lesson_entry(student_id: int, lesson_id: str) -> None:
    """Remember when a student first opened the current lesson during this session.

    This supports research analysis of whether learners request GenAI support
    immediately or after spending time with the concept activity.
    """
    key = f"lesson_entry_ts_{lesson_id}"
    if key not in st.session_state:
        st.session_state[key] = time.time()
        try:
            db.log_event(
                student_id,
                "student",
                "lesson_entry",
                json.dumps({"lesson_id": lesson_id}),
            )
        except Exception:
            pass


def log_ai_request_timing(student_id: int, lesson_id: str, source: str, task: str = "", step: str = "") -> None:
    """Log time spent in the lesson before a GenAI request is made."""
    key = f"lesson_entry_ts_{lesson_id}"
    start = st.session_state.get(key)
    seconds = round(time.time() - start, 1) if start else None
    detail = {
        "lesson_id": lesson_id,
        "source": source,
        "task": task,
        "step": step,
        "seconds_before_ai": seconds,
    }
    try:
        db.log_event(student_id, "student", "ai_request_timing", json.dumps(detail))
    except Exception:
        pass


def inline_ai_explain_button(student: Dict[str, Any], lesson: Dict[str, Any], focus: str, text: str, key: str) -> None:
    """Small contextual AI helper used inside concept and code panels.

    It is intentionally limited: it asks for a scaffolded explanation of the
    selected panel rather than a full answer. Timing is logged for research.
    """
    if not ai_features_available(student):
        return
    st.markdown("<div class='qai-inline-ai-box'>", unsafe_allow_html=True)
    st.caption("Use after reading this part: the AI should clarify the idea, not replace your reasoning.")
    if st.button("Ask AI to clarify this part", key=f"inline_ai_{key}", use_container_width=True):
        log_ai_request_timing(student["id"], lesson["id"], "inline_ai_explain", task=focus, step=focus)
        tutor = feedback_engine.generate_tutor_response(
            task=f"Clarify this {focus} panel with one short explanation and one check question. Do not give a full solution.",
            concept=", ".join(lesson.get("concepts", [])),
            student_input=text,
            student_profile=student_profile(student),
            lesson_context={
                **lesson,
                "pedagogical_mode": "inline concept clarification",
                "ai_use_policy": "Clarify, ask a check question, and avoid answer dumping.",
            },
        )
        interaction_id = log_tutor_interaction(
            student["id"],
            "inline_lesson_support",
            ", ".join(lesson.get("concepts", [])),
            f"clarify_{focus}",
            text,
            tutor,
            lesson_id=lesson["id"],
            activity_id="inline_ai_explain",
            selected_text=focus,
        )
        st.write(tutor.response)
        render_ai_usefulness_feedback(interaction_id, f"inline_ai_{key}")
    st.markdown("</div>", unsafe_allow_html=True)

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
        format_func=lambda x: i18n.tr({1: "1 - Not useful", 2: "2", 3: "3 - Acceptable", 4: "4", 5: "5 - Very useful"}[x]),
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


def learning_ui_copy() -> Dict[str, Any]:
    lang = i18n.current_lang(st)
    values = {
        "ar": {
            "dir": "rtl", "overview": "نظرة عامة", "learning": "التعلّم", "assessment": "التقييم", "research": "البحث والموافقة",
            "home": "لوحة المتعلّم", "plan": "الخطة التكيفية", "modules": "الوحدات التعليمية", "tutor": "مدرّب الذكاء الاصطناعي",
            "pre": "الاختبار القبلي", "post": "الاختبار البعدي", "survey": "الاستبيان الختامي", "notice": "إشعار البحث",
            "resume": "متابعة التعلّم", "journey": "رحلة التعلّم", "overall": "التقدّم العام", "modules_done": "الوحدات المكتملة",
            "ai_uses": "تفاعلات المدرّب", "pre_score": "نتيجة الاختبار القبلي", "post_score": "نتيجة الاختبار البعدي",
            "current": "الوحدة الحالية", "next_action": "الخطوة التالية", "continue": "متابعة الخطوة المقترحة",
            "open_path": "فتح المسار", "open_tutor": "فتح المدرّب الذكي", "dashboard_sub": "تابع تقدمك، استأنف وحدتك الحالية، وانتقل إلى الخطوة الصحيحة دون تشتّت.",
            "test_intro": "أجب بشكل فردي. يقيس هذا التقييم تقدّم الفهم ولا يمنح علامة دراسية.", "question": "السؤال", "of": "من",
            "choose": "اختر إجابة واحدة", "concept": "المفهوم", "submit_pre": "إرسال الاختبار القبلي", "submit_post": "إرسال الاختبار البعدي",
            "path_title": "مسار الكوانتوم الموجّه", "path_sub": "ست وحدات قصيرة تجمع الشرح البصري، التطبيق، Qiskit، الدعم الموجّه، والتحقق من الفهم.",
            "completed": "مكتملة", "recommended": "موصى بها", "available": "متاحة", "open": "فتح الوحدة", "opened": "مفتوحة",
            "quick": "بدايات سريعة", "hint": "أعطني تلميحًا", "simplify": "اشرح بطريقة أبسط", "qiskit": "أعطني مثال Qiskit", "quiz": "اختبر فهمي",
        },
        "fr": {
            "dir": "ltr", "overview": "Vue d’ensemble", "learning": "Apprentissage", "assessment": "Évaluation", "research": "Recherche et consentement",
            "home": "Tableau apprenant", "plan": "Plan adaptatif", "modules": "Modules", "tutor": "Coach IA", "pre": "Pré-test", "post": "Post-test",
            "survey": "Questionnaire final", "notice": "Notice de recherche", "resume": "Reprendre l’apprentissage", "journey": "Parcours d’apprentissage",
            "overall": "Progression globale", "modules_done": "Modules terminés", "ai_uses": "Interactions IA", "pre_score": "Score pré-test",
            "post_score": "Score post-test", "current": "Module actuel", "next_action": "Prochaine étape", "continue": "Continuer l’étape recommandée",
            "open_path": "Ouvrir le parcours", "open_tutor": "Ouvrir le Coach IA", "dashboard_sub": "Suivez votre progression, reprenez le module actuel et avancez sans vous disperser.",
            "test_intro": "Répondez individuellement. Cette évaluation mesure les progrès de compréhension et ne constitue pas une note académique.",
            "question": "Question", "of": "sur", "choose": "Choisissez une réponse", "concept": "Concept", "submit_pre": "Envoyer le pré-test", "submit_post": "Envoyer le post-test",
            "path_title": "Parcours Quantum guidé", "path_sub": "Six modules courts combinant explication visuelle, pratique, Qiskit, soutien guidé et vérification.",
            "completed": "Terminé", "recommended": "Recommandé", "available": "Disponible", "open": "Ouvrir", "opened": "Ouvert",
            "quick": "Démarrages rapides", "hint": "Donner un indice", "simplify": "Expliquer plus simplement", "qiskit": "Donner un exemple Qiskit", "quiz": "Tester ma compréhension",
        },
        "en": {
            "dir": "ltr", "overview": "Overview", "learning": "Learning", "assessment": "Assessment", "research": "Research & consent",
            "home": "Learner dashboard", "plan": "Adaptive plan", "modules": "Learning modules", "tutor": "AI Coach", "pre": "Pre-test", "post": "Post-test",
            "survey": "Final survey", "notice": "Research notice", "resume": "Resume learning", "journey": "Learning journey",
            "overall": "Overall progress", "modules_done": "Modules completed", "ai_uses": "AI interactions", "pre_score": "Pre-test score",
            "post_score": "Post-test score", "current": "Current module", "next_action": "Next action", "continue": "Continue recommended step",
            "open_path": "Open learning path", "open_tutor": "Open AI Coach", "dashboard_sub": "Track progress, resume the current module, and move to the right next step without distraction.",
            "test_intro": "Answer individually. This assessment measures learning progress and is not an academic grade.",
            "question": "Question", "of": "of", "choose": "Choose one answer", "concept": "Concept", "submit_pre": "Submit pre-test", "submit_post": "Submit post-test",
            "path_title": "Guided Quantum path", "path_sub": "Six compact modules combining visual explanation, practice, Qiskit, guided support, and understanding checks.",
            "completed": "Completed", "recommended": "Recommended", "available": "Available", "open": "Open module", "opened": "Opened",
            "quick": "Quick starts", "hint": "Give me a hint", "simplify": "Explain more simply", "qiskit": "Give a Qiskit example", "quiz": "Test my understanding",
        },
    }
    return values.get(lang, values["en"])



def render_sidebar(target=st) -> None:
    role = st.session_state.get("role")
    lang = i18n.current_lang(st)
    t = branding.TEXT[lang]
    u = learning_ui_copy()
    target.markdown("<span class='v4-sidebar-marker v43-sidebar-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
    if branding.OFFICIAL_LOGO_PATH.exists():
        target.image(str(branding.OFFICIAL_LOGO_PATH), use_container_width=True)
    else:
        target.markdown(branding.logo_lockup_html(compact=True, language=lang), unsafe_allow_html=True)
    target.markdown(f"<div class='v4-sidebar-tagline' dir='{u['dir']}'>{escape(t['nav_caption'])}</div>", unsafe_allow_html=True)
    render_language_selector(target, key="sidebar_language_selector")

    if role == "student":
        student = current_student()
        current_page = st.session_state.get("student_page", "Student Home")
        allowed = student_pages_allowed(student)
        if student:
            completed = lesson_completion_count(student["id"])
            required = required_lesson_count_for_posttest()
            pct = int(round(100 * completed / max(required, 1)))
            current_id = current_or_resume_lesson_id(student["id"]) if test_is_done(student["id"], "pre") else None
            current_title = next((x.get("short_title", x["title"]) for x in localized_lessons() if x["id"] == current_id), "—")
            initials = "".join(part[:1].upper() for part in str(student.get("full_name") or "3A").split()[:2]) or "3A"
            target.markdown(f"""
            <section class='v43-side-profile' dir='{u['dir']}'>
              <div class='v43-avatar'>{escape(initials)}</div>
              <div class='v43-profile-copy'><strong>{escape(str(student.get('full_name') or ''))}</strong><span>{escape(str(student['participant_code']))}</span></div>
              <div class='v43-progress-number'>{pct}%</div>
              <div class='v43-progress-track'><i style='width:{pct}%'></i></div>
              <div class='v43-current'><span>{escape(u['current'])}</span><b>{escape(str(current_title))}</b></div>
            </section>""", unsafe_allow_html=True)
            if target.button(f"▶ {u['resume']}", key="v43_resume", type="primary", use_container_width=True):
                st.session_state.student_page = next_student_page(student)
                st.rerun()
        else:
            target.markdown(f"<div class='v43-guest-card' dir='{u['dir']}'><b>{escape(i18n.tr('No student signed in'))}</b><span>{escape(i18n.tr('Create an account or sign in to start the study.'))}</span></div>", unsafe_allow_html=True)

        if not student:
            for page, icon in (("Sign in", "↪"), ("Create account", "+")):
                if target.button(f"{icon} {i18n.page_label(page, lang)}", key=f"student_nav_{page}", use_container_width=True, type="primary" if current_page == page else "secondary"):
                    st.session_state.student_page = page
                    st.rerun()
        else:
            groups = [
                (u["overview"], [("Student Home", "⌂", u["home"])]),
                (u["learning"], [("Adaptive Plan", "✦", u["plan"]), ("Learning Module", "▦", u["modules"]), ("AI Tutor Lab", "◈", u["tutor"])]),
                (u["assessment"], [("Pre-test", "01", u["pre"]), ("Post-test", "02", u["post"]), ("Satisfaction Survey", "✓", u["survey"])]),
                (u["research"], [("Research Notice", "◎", u["notice"])])
            ]
            for group_index, (title, pages) in enumerate(groups):
                active_group = any(page == current_page for page, _, _ in pages)
                # Keep the active section open and collapse the others. This
                # prevents the navigation from becoming taller than the laptop
                # viewport while preserving fast access to every destination.
                with target.expander(title, expanded=active_group):
                    for page, icon, label in pages:
                        if page in allowed:
                            if target.button(f"{icon}  {label}", key=f"student_nav_{page}", use_container_width=True, type="primary" if current_page == page else "secondary"):
                                st.session_state.student_page = page
                                st.rerun()
                        else:
                            target.markdown(f"<div class='v43-nav-lock' dir='{u['dir']}'><span>{escape(icon)}</span><b>{escape(label)}</b><i>🔒</i></div>", unsafe_allow_html=True)
        target.markdown("<div class='v43-side-separator'></div>", unsafe_allow_html=True)
        if student and target.button(i18n.tr("Sign out"), use_container_width=True):
            db.log_event(student["id"], "student", "sign_out", "Student signed out from sidebar")
            st.session_state.student_id = None
            st.session_state.student_page = "Student Home"
            st.rerun()
        if target.button(i18n.tr("Switch workspace"), use_container_width=True):
            switch_role(None)
        render_status_badge(target)
    elif role == "evaluator":
        eu = evaluator_ui()
        target.markdown(f"<div class='v45-eval-profile' dir='{eu['dir']}'><div class='v45-eval-avatar'>ER</div><div><b>{escape(eu['workspace'])}</b><span>{escape(eu['workspace_sub'])}</span></div></div>", unsafe_allow_html=True)
        if st.session_state.evaluator_logged_in:
            nav_hint = {
                "ar": "جميع أدوات المقيّم - ومنها التصدير - موجودة داخل الأقسام أدناه. مرّر هذه القائمة فقط للوصول إليها.",
                "fr": "Tous les outils d’évaluation, y compris l’export, se trouvent dans les sections ci-dessous. Faites défiler uniquement ce panneau.",
                "en": "All evaluator tools, including exports, are in the sections below. Scroll this panel independently.",
            }.get(lang, "")
            target.markdown(f"<div class='v481-navigation-note' dir='{eu['dir']}'>{escape(nav_hint)}</div>", unsafe_allow_html=True)
            groups = [
                (eu["overview_group"], [("Evaluator Dashboard", "⌂"), ("Study Protocol", "◎")]),
                (eu["participants_group"], [("Students", "◉"), ("Registration Accounts", "▤"), ("Student Details", "↗")]),
                (eu["ai_group"], [("AI Tutor Logs", "◈"), ("AI Response Evaluation", "★"), ("AI Metrics", "▥")]),
                (eu["data_group"], [("Exports", "⇩")]),
            ]
            current_eval_page = st.session_state.evaluator_page
            for group_index, (title, pages) in enumerate(groups):
                active_group = any(page == current_eval_page for page, _ in pages)
                with target.expander(title, expanded=active_group):
                    for page, icon in pages:
                        label = i18n.page_label(page, lang)
                        if target.button(f"{icon}  {label}", key=f"eval_nav_btn_{page}", use_container_width=True, type="primary" if current_eval_page == page else "secondary"):
                            st.session_state.evaluator_page = page
                            st.rerun()
            status = feedback_engine.provider_status()
            readiness = db.system_readiness(len(content.LESSONS))
            ai_state = eu["available"] if status.get("available") else eu["unavailable"]
            target.markdown(
                f"<div class='v45-eval-status' dir='{eu['dir']}'><span>{escape(eu['system_status'])}</span><b>{escape(str(readiness.get('database_dialect','—')))} · {escape(ai_state)}</b><small>{escape(str(readiness.get('app_version','—')))}</small></div>",
                unsafe_allow_html=True,
            )
            if target.button(i18n.tr("Sign out"), use_container_width=True):
                st.session_state.evaluator_logged_in = False
                st.rerun()
        if target.button(i18n.tr("Switch workspace"), use_container_width=True):
            switch_role(None)
    else:
        target.markdown(f"<div class='v4-sidebar-welcome' dir='{u['dir']}'><span>{escape(t['how_kicker'])}</span><strong>{escape(t['how_title'])}</strong><p>{escape(t['paths_body'])}</p></div>", unsafe_allow_html=True)


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
    pages += ["Adaptive Plan", "Learning Module"]
    if ai_features_available(student):
        pages.append("AI Tutor Lab")
    if learning_path_ready_for_posttest(student["id"]) and ai_requirement_met(student):
        pages.append("Post-test")
    if test_is_done(student["id"], "post"):
        pages.append("Satisfaction Survey")
    pages.append("Research Notice")
    return pages

# -----------------------------------------------------------------------------
# Landing and access
# -----------------------------------------------------------------------------

def render_role_selection() -> None:
    """Render the V4 premium multilingual startup landing page."""
    lang = i18n.current_lang(st)
    t = branding.TEXT[lang]
    direction = t["direction"]

    with st.container(border=True):
        st.markdown("<span class='v4-landing-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
        copy_col, visual_col = st.columns([1.15, 0.85], gap="large")
        with copy_col:
            if branding.OFFICIAL_LOGO_PATH.exists():
                st.image(str(branding.OFFICIAL_LOGO_PATH), use_column_width=True)
            st.markdown(branding.hero_copy_html(lang), unsafe_allow_html=True)
            cta1, cta2 = st.columns(2, gap="small")
            with cta1:
                if st.button(t["start_quantum"], key="v4_hero_start", type="primary", use_container_width=True):
                    st.session_state.landing_track = "quantum"
                    st.session_state.selected_track = "quantum"
                    switch_role("student")
            with cta2:
                if st.button(t["evaluator_button"], key="v4_hero_evaluator", use_container_width=True):
                    switch_role("evaluator")
        with visual_col:
            st.markdown(branding.hero_visual_html(lang), unsafe_allow_html=True)

    st.markdown(branding.section_heading_html(t["paths_kicker"], t["paths_title"], t["paths_body"], lang), unsafe_allow_html=True)

    selected = st.session_state.get("landing_track", "quantum")
    cols = st.columns(3, gap="large")
    track_order = ["quantum", "ml", "ai"]
    labels = {"quantum": t["start_quantum"], "ml": t["preview_ml"], "ai": t["preview_ai"]}
    for col, track_id in zip(cols, track_order):
        with col:
            st.markdown(branding.track_card_html(track_id, lang, selected == track_id), unsafe_allow_html=True)
            if st.button(labels[track_id], key=f"landing_track_{track_id}", type="primary" if track_id == "quantum" else "secondary", use_container_width=True):
                st.session_state.landing_track = track_id
                st.session_state.selected_track = track_id
                if track_id == "quantum":
                    switch_role("student")
                st.rerun()

    if selected in {"ml", "ai"}:
        track = branding.TRACKS[selected]
        st.markdown(branding.preview_panel_html(track, lang), unsafe_allow_html=True)

    st.markdown(branding.section_heading_html(t["how_kicker"], t["how_title"], "", lang, extra_class="brand-how-heading"), unsafe_allow_html=True)
    st.markdown(branding.how_grid_html(lang), unsafe_allow_html=True)
    st.markdown(branding.research_strip_html(lang), unsafe_allow_html=True)


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
    u = learning_ui_copy()
    lang = i18n.current_lang(st)
    if not student:
        hero("3alimnIA Quantum", branding.TEXT[lang]["subheadline"])
        st.markdown(f"<div class='v43-guest-intro' dir='{u['dir']}'><b>{escape(u['path_title'])}</b><span>{escape(u['path_sub'])}</span></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button(i18n.tr("Sign in"), type="primary", use_container_width=True):
                set_student_page("Sign in")
        with c2:
            if st.button(i18n.tr("Create account"), use_container_width=True):
                set_student_page("Create account")
        return
    if st.session_state.get("new_participant_code"):
        st.success(i18n.tr("Account created successfully. Save your participant code before continuing."))
        render_participant_code_box(st.session_state["new_participant_code"])
        if st.button(i18n.tr("I saved my participant code"), type="primary"):
            st.session_state.new_participant_code = None
            set_student_page(next_student_page(student))
        return
    summary = db.progress_summary_df(len(content.LESSONS))
    row = summary[summary["student_id"] == student["id"]] if not summary.empty and "student_id" in summary.columns else pd.DataFrame()
    progress_pct = float(row["progress_percent"].iloc[0]) if not row.empty and "progress_percent" in row.columns else 0.0
    modules_done = lesson_completion_count(student["id"])
    ai_count = db.ai_interaction_count(student["id"])
    pre = db.get_test_attempt(student["id"], "pre")
    post = db.get_test_attempt(student["id"], "post")
    current_id = current_or_resume_lesson_id(student["id"]) if test_is_done(student["id"], "pre") else content.LESSONS[0]["id"]
    lesson = content.lesson_by_id(current_id, lang)
    current_index = [x["id"] for x in content.LESSONS].index(current_id) + 1
    hero(u["home"], u["dashboard_sub"])
    st.markdown(f"""
    <section class='v43-metrics' dir='{u['dir']}'>
      <article><span>{escape(u['overall'])}</span><strong>{progress_pct:.0f}%</strong><i><em style='width:{progress_pct:.0f}%'></em></i></article>
      <article><span>{escape(u['modules_done'])}</span><strong>{modules_done}<small> / {len(content.LESSONS)}</small></strong><i><em style='width:{100*modules_done/max(len(content.LESSONS),1):.0f}%'></em></i></article>
      <article><span>{escape(u['pre_score'])}</span><strong>{f"{pre['score']:.0f}%" if pre else '—'}</strong><small>{escape(u['post_score'])}: {f"{post['score']:.0f}%" if post else '—'}</small></article>
      <article><span>{escape(u['ai_uses'])}</span><strong>{ai_count}</strong><small>{escape(study_group_label(student))}</small></article>
    </section>
    <section class='v43-resume-card' dir='{u['dir']}'>
      <div class='v43-resume-index'>{current_index:02d}</div>
      <div><span>{escape(u['current'])}</span><h2>{escape(lesson.get('short_title', lesson['title']))}</h2><p>{escape(lesson.get('objective',''))}</p></div>
      <div class='v43-next-action'><span>{escape(u['next_action'])}</span><b>{escape(i18n.tr(next_action_text(student)))}</b></div>
    </section>""", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.35, 1, 1])
    with c1:
        if st.button(f"▶ {u['continue']}", type="primary", use_container_width=True):
            set_student_page(next_student_page(student))
    with c2:
        if st.button(u["open_path"], use_container_width=True, disabled=not test_is_done(student["id"], "pre")):
            set_student_page("Learning Module")
    with c3:
        if st.button(u["open_tutor"], use_container_width=True, disabled=(not test_is_done(student["id"], "pre") or not ai_features_available(student))):
            set_student_page("AI Tutor Lab")
    render_completion_requirements(student)

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
    if not ai_requirement_met(student):
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
            set_student_page(next_student_page(student))
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
        set_student_page(next_student_page(student))


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
            ok, diagnostic = send_password_reset_email(student.get("email", email_clean), student.get("full_name", "student"), reset_link, language=student.get("preferred_language", i18n.current_lang(st)))
            db.log_event(student["id"], "student", "password_reset_requested", "Password reset requested")
            if not ok:
                st.warning("Password reset was created, but email delivery is not configured or failed. Please contact the instructor.")
                if secret("SHOW_RESET_LINK_FOR_DEBUG", "false").strip().lower() in {"1", "true", "yes"}:
                    st.code(reset_link)
                return
        st.success(generic_msg)


def render_password_reset_form(token: str) -> None:
    hero("Reset Password", "Create a new password for your 3alimnIA account.")
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
            st.info("You can now sign in using your email, participant code, or exact full name.")
            if st.button("Go to sign in", type="primary"):
                set_student_page("Sign in")
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
            preferred = i18n.normalize_lang(student.get("preferred_language"))
            st.session_state.ui_language_code = preferred
            st.session_state.ui_language = i18n.LANGUAGE_LABELS[preferred]
            st.session_state.student_id = student["id"]
            st.session_state.current_lesson_id = db.get_last_open_lesson(student["id"]) or first_incomplete_lesson_id(student["id"])
            st.success("Signed in successfully.")
            set_student_page(next_student_page(student))
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
            assigned_group = None
            if control_group_enabled():
                # Balanced assignment is finalized after the row is created.
                assigned_group = "pending"
            student = db.create_student(full_name, email, institution, academic_level, prior_python, prior_quantum, password, study_group=("" if assigned_group else "single_arm"), preferred_language=i18n.current_lang(st))
            if control_group_enabled():
                group = db.assign_study_group(student["id"])
                student = db.get_student(student["id"]) or student
                db.log_event(student["id"], "system", "study_group_assigned", json.dumps({"study_group": group, "method": "balanced_alternation"}))
            consent_text = "Participant confirmed that answers and AI interactions may be recorded for the pilot evaluation."
            db.save_consent(student["id"], consent_text, consent_version="v1")
            db.log_event(student["id"], "student", "account_created", "Student created account and confirmed consent notice")
            st.session_state.student_id = student["id"]
            st.session_state.current_lesson_id = content.LESSONS[0]["id"]
            st.session_state.new_participant_code = student["participant_code"]
            st.success(f"Account created. Your participant code is: {student['participant_code']}")
            set_student_page("Student Home")
        except Exception as exc:
            st.error(f"Could not create account: {exc}")

# -----------------------------------------------------------------------------
# Student study flow
# -----------------------------------------------------------------------------


def render_test_page(student: Dict[str, Any], kind: str) -> None:
    u = learning_ui_copy()
    title = u["pre"] if kind == "pre" else u["post"]
    hero(title, u["test_intro"])
    if kind == "post" and not has_minimum_lesson_activity(student["id"]):
        st.warning(i18n.tr("Please complete at least one learning section and save its reflection before the post-test.")); return
    if kind == "post" and not ai_requirement_met(student):
        st.warning(i18n.tr("Please complete at least one AI Tutor interaction before the post-test. This applies only to the experimental AI-supported group.")); return
    existing = db.get_test_attempt(student["id"], kind)
    if existing:
        st.markdown(f"<div class='v43-result-card' dir='{u['dir']}'><span>{escape(title)}</span><strong>{existing['score']:.1f}%</strong></div>", unsafe_allow_html=True)
        if st.button(i18n.tr("Continue"), type="primary", use_container_width=True):
            set_student_page("Adaptive Plan" if kind == "pre" else "Satisfaction Survey")
        return
    questions = content.questions_for(kind)
    with st.form(f"{kind}_test_form"):
        answers: Dict[str, int] = {}
        for i, q in enumerate(questions, start=1):
            pct = int(round(100*i/max(len(questions),1)))
            st.markdown(f"<section class='v43-question-head' dir='{u['dir']}'><div><span>{escape(u['question'])} {i} {escape(u['of'])} {len(questions)}</span><b>{escape(q.question)}</b></div><i>{pct}%</i></section>", unsafe_allow_html=True)
            answers[q.id] = st.radio(u["choose"], options=list(range(len(q.options))), format_func=lambda idx, opts=q.options: opts[idx], key=f"{kind}_{q.id}", label_visibility="collapsed")
            concept_label = getattr(q, 'display_concept', '') or i18n.concept_label(q.concept, i18n.current_lang(st))
            st.markdown(f"<div class='v43-concept-tag'>{escape(u['concept'])}: {escape(concept_label)}</div>", unsafe_allow_html=True)
        submitted = st.form_submit_button(u["submit_pre"] if kind == "pre" else u["submit_post"], type="primary", use_container_width=True)
    if submitted:
        result = db.save_test_attempt(student["id"], kind, answers, questions)
        if kind == "pre": db.compute_adaptive_recommendation(student["id"], content.CONCEPT_TO_LESSONS)
        db.log_event(student["id"], "student", f"{kind}_test_submitted", f"Score: {result['score']:.1f}%")
        st.success(f"{result['score']:.1f}%")
        st.rerun()

def render_adaptive_plan(student: Dict[str, Any]) -> None:
    lang = i18n.current_lang(st)
    direction = i18n.direction(lang)
    copy = {
        "ar": {
            "intro_title": "كيف تقرأ هذه الخطة؟",
            "steps": [
                "ابدأ بالمفاهيم التي ظهرت حاجتها إلى التعزيز أو التي أوصت بها المنصة.",
                "أكمل الوحدة التعليمية وحاول بنفسك قبل الاعتماد على المدرّب الذكي.",
                "استخدم المدرّب الذكي للتلميحات والتوضيح، لا لنسخ إجابات نهائية.",
            ],
            "input": "أنشئ خطة دراسية موجزة ومنظمة اعتمادًا على ملف المتعلم والمفاهيم التي تحتاج إلى تعزيز. استخدم العربية الفصحى في جميع العناوين والخطوات، وأبقِ أسماء Qiskit والكود فقط بصيغتها التقنية عند الحاجة.",
            "task": "إنشاء خطة تعلم شخصية منظمة",
            "concept": "التعلم التكيفي في البرمجة الكمية",
            "next": "الخطوة التفاعلية التالية: اضغط «بدء الوحدة التعليمية» وأكمل نشاطًا تعليميًا واحدًا على الأقل.",
        },
        "fr": {
            "intro_title": "Comment lire ce plan ?",
            "steps": [
                "Commencez par les concepts à renforcer ou recommandés par la plateforme.",
                "Terminez le module et effectuez votre propre tentative avant de vous appuyer sur le coach IA.",
                "Utilisez le coach IA pour obtenir des indices et des explications, et non pour copier des réponses finales.",
            ],
            "input": "Génère un plan d’étude concis et structuré à partir du profil de l’apprenant et des concepts à renforcer. Rédige tous les titres et toutes les étapes en français ; conserve uniquement les identifiants Qiskit et le code dans leur forme technique.",
            "task": "Générer un plan d’apprentissage personnalisé et structuré",
            "concept": "Apprentissage adaptatif de la programmation quantique",
            "next": "Étape interactive suivante : cliquez sur « Commencer le module » et terminez au moins une activité d’apprentissage.",
        },
        "en": {
            "intro_title": "How to read this plan",
            "steps": [
                "Start with the concepts listed as weak or recommended.",
                "Complete the learning module before relying on the AI tutor.",
                "Use the AI tutor for hints and explanations, not for copying final answers.",
            ],
            "input": "Generate a concise, structured study plan based on the learner profile and concepts to reinforce.",
            "task": "Generate a structured personalized study plan",
            "concept": "Adaptive quantum-programming learning",
            "next": "Next interactive step: click “Start learning module” and complete at least one learning activity.",
        },
    }[lang]

    hero("Adaptive Learning Plan", "The platform uses your pre-test results to recommend learning sections and AI-supported practice.")
    if not test_is_done(student["id"], "pre"):
        st.warning("Complete the pre-test first.")
        return

    rec = db.get_recommendation(student["id"]) or db.compute_adaptive_recommendation(student["id"], content.CONCEPT_TO_LESSONS)
    weak = rec.get("weak_concepts", [])
    recommended = rec.get("recommended_lessons", [])
    weak_localized = [i18n.concept_label(concept, lang) for concept in weak]
    lesson_map = {lesson["id"]: lesson["title"] for lesson in localized_lessons()}
    recommended_localized = [lesson_map.get(lesson_id, lesson_id) for lesson_id in recommended]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Concepts to reinforce")
        if weak_localized:
            for concept in weak_localized:
                st.markdown(f"- {concept}")
        else:
            st.markdown("No major weakness detected. Continue with the full learning sequence.")
    with c2:
        st.markdown("### Recommended lesson sequence")
        for title in recommended_localized:
            st.markdown(f"- {title}")

    st.divider()
    plan_language = st.selectbox(
        "AI response language",
        ["Auto-detect", "English", "Arabic", "French"],
        index={"en": 1, "ar": 2, "fr": 3}[lang],
        key="adaptive_plan_language",
        format_func=lambda value: i18n.tr(value),
    )
    target_lang = lang if plan_language == "Auto-detect" else {"English": "en", "Arabic": "ar", "French": "fr"}[plan_language]
    target_direction = i18n.direction(target_lang)

    if st.button("Generate AI personalized study plan", type="primary"):
        profile = student_profile(student)
        # Pass learner-visible labels rather than internal English identifiers.
        plan_profile = {
            "participant_code": profile.get("participant_code"),
            "academic_level": profile.get("academic_level"),
            "prior_python_level": profile.get("prior_python_level"),
            "prior_quantum_level": profile.get("prior_quantum_level"),
            "pre_test_score": profile.get("pre_test_score"),
            "concepts_to_reinforce": weak_localized,
            "recommended_sequence": recommended_localized,
            "completed_modules": len(profile.get("completed_lessons", [])),
        }
        target_copy = copy if target_lang == lang else {
            "ar": {
                "input": "أنشئ خطة دراسية موجزة ومنظمة اعتمادًا على ملف المتعلم والمفاهيم التي تحتاج إلى تعزيز. استخدم العربية الفصحى في جميع العناوين والخطوات، وأبقِ أسماء Qiskit والكود فقط بصيغتها التقنية عند الحاجة.",
                "task": "إنشاء خطة تعلم شخصية منظمة", "concept": "التعلم التكيفي في البرمجة الكمية",
            },
            "fr": {
                "input": "Génère un plan d’étude concis et structuré à partir du profil de l’apprenant et des concepts à renforcer. Rédige tous les titres et toutes les étapes en français.",
                "task": "Générer un plan d’apprentissage personnalisé et structuré", "concept": "Apprentissage adaptatif de la programmation quantique",
            },
            "en": {
                "input": "Generate a concise, structured study plan based on the learner profile and concepts to reinforce.",
                "task": "Generate a structured personalized study plan", "concept": "Adaptive quantum-programming learning",
            },
        }[target_lang]
        tutor = feedback_engine.generate_tutor_response(
            task=target_copy["task"],
            concept=target_copy["concept"],
            student_input=target_copy["input"],
            student_profile=plan_profile,
            lesson_context={
                "recommended_sequence": recommended_localized,
                "concepts_to_reinforce": weak_localized,
                "response_language": i18n.response_language(target_lang),
                "required_structure": ["diagnosis", "ordered learning steps", "practice guidance", "reflection question"],
                "language_contract": "All prose headings and steps must use the requested language. Keep only code identifiers and essential Qiskit tokens in English.",
            },
        )
        tutor.response = i18n.localize_generated_text(tutor.response, target_lang)
        log_tutor_interaction(
            student["id"], "adaptive_plan", "Adaptive learning", "Generate personalized study plan",
            target_copy["input"], tutor,
        )
        st.markdown("### 📋 AI-generated study plan")
        steps_html = "".join(f"<li>{escape(step)}</li>" for step in copy["steps"])
        st.markdown(
            f"<aside class='v44-plan-guide' dir='{direction}'><strong>{escape(copy['intro_title'])}</strong><ol>{steps_html}</ol></aside>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Personalized plan")
        safe_response = escape(tutor.response).replace("\n", "<br>")
        st.markdown(
            f"<section class='v44-generated-plan' dir='{target_direction}'>{safe_response}</section>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='qai-interactive' dir='{direction}'>{escape(copy['next'])}</div>",
            unsafe_allow_html=True,
        )
        if tutor.mode == "llm_error":
            st.info("The LLM service was unavailable, so a local fallback was shown and logged for the evaluator.")
    if st.button("Start learning module →", type="primary", use_container_width=True):
        set_student_page("Learning Module")



def lesson_diagram_html(lesson_id: str) -> str:
    """Return a compact localized text diagram while keeping code tokens unchanged."""
    diagrams = {
        "en": {
            "orientation": "Qiskit code\n  QuantumCircuit(1, 1)\n        ↓\nCircuit\n  q0 ── M ──\n        │\n  c0 ◄──0\n        ↓\nClassical output: {'0': shots}",
            "qubit_measurement": "Before measurement\n  qubit state: |0⟩ or α|0⟩ + β|1⟩\n        ↓ measurement\nAfter measurement\n  one classical result per shot: 0 or 1",
            "hadamard_superposition": "Start\n  |0⟩\n        ↓ H gate\nBefore measurement\n  (|0⟩ + |1⟩) / √2\n        ↓ many shots\nCounts\n  0 ≈ 50%   1 ≈ 50%",
            "shots_counts": "Run circuit once = one shot\n        ↓\nRun 10 shots → small noisy sample\n        ↓\nRun 1000 shots → clearer distribution\n        ↓\nCounts are frequencies, not certainty",
            "cnot_correlation": "q0: ── H ── ● ── M ──\n             │\nq1: ─────── ⊕ ── M ──\n\nRule: if control q0 = 1, target q1 flips\nBell-style output: mostly 00 and 11",
            "qiskit_debugging": "Common error\n  QuantumCircuit(1, 0)\n  qc.measure(0, 0)  ← no classical bit exists\n\nFix\n  QuantumCircuit(1, 1)\n  qc.measure(0, 0)",
        },
        "ar": {
            "orientation": "كود Qiskit\n  QuantumCircuit(1, 1)\n        ↓\nالدارة\n  q0 ── M ──\n        │\n  c0 ◄──0\n        ↓\nالخرج الكلاسيكي: {'0': shots}",
            "qubit_measurement": "قبل القياس\n  حالة qubit: |0⟩ أو α|0⟩ + β|1⟩\n        ↓ measurement\nبعد القياس\n  نتيجة كلاسيكية واحدة في كل shot: 0 أو 1",
            "hadamard_superposition": "البداية\n  |0⟩\n        ↓ بوابة H\nقبل القياس\n  (|0⟩ + |1⟩) / √2\n        ↓ shots كثيرة\nالعدّادات counts\n  0 ≈ 50%   1 ≈ 50%",
            "shots_counts": "تنفيذ الدارة مرة = shot واحدة\n        ↓\n10 shots → عينة صغيرة متذبذبة\n        ↓\n1000 shots → توزيع أوضح\n        ↓\ncounts تكرارات وليست يقينًا",
            "cnot_correlation": "q0: ── H ── ● ── M ──\n             │\nq1: ─────── ⊕ ── M ──\n\nالقاعدة: إذا كان control q0 = 1 تنقلب target q1\nخرج شبيه بحالة Bell: غالبًا 00 و11",
            "qiskit_debugging": "خطأ شائع\n  QuantumCircuit(1, 0)\n  qc.measure(0, 0)  ← لا يوجد classical bit\n\nالتصحيح\n  QuantumCircuit(1, 1)\n  qc.measure(0, 0)",
        },
        "fr": {
            "orientation": "Code Qiskit\n  QuantumCircuit(1, 1)\n        ↓\nCircuit\n  q0 ── M ──\n        │\n  c0 ◄──0\n        ↓\nSortie classique : {'0': shots}",
            "qubit_measurement": "Avant la mesure\n  état du qubit : |0⟩ ou α|0⟩ + β|1⟩\n        ↓ measurement\nAprès la mesure\n  un résultat classique par shot : 0 ou 1",
            "hadamard_superposition": "Départ\n  |0⟩\n        ↓ porte H\nAvant la mesure\n  (|0⟩ + |1⟩) / √2\n        ↓ plusieurs shots\nCounts\n  0 ≈ 50 %   1 ≈ 50 %",
            "shots_counts": "Exécuter une fois = un shot\n        ↓\n10 shots → petit échantillon fluctuant\n        ↓\n1000 shots → distribution plus claire\n        ↓\nLes counts sont des fréquences, pas une certitude",
            "cnot_correlation": "q0: ── H ── ● ── M ──\n             │\nq1: ─────── ⊕ ── M ──\n\nRègle : si le contrôle q0 = 1, la cible q1 bascule\nSortie de type Bell : surtout 00 et 11",
            "qiskit_debugging": "Erreur fréquente\n  QuantumCircuit(1, 0)\n  qc.measure(0, 0)  ← aucun bit classique\n\nCorrection\n  QuantumCircuit(1, 1)\n  qc.measure(0, 0)",
        },
    }
    lang = i18n.current_lang(st)
    fallback = {"ar": "يُحضّر المخطط لهذا الدرس.", "fr": "Le schéma de cette leçon est en préparation.", "en": "Diagram is being prepared for this lesson."}
    return diagrams.get(lang, diagrams["en"]).get(lesson_id, fallback[lang])


def lesson_sequence_frames(lesson_id: str) -> List[Dict[str, str]]:
    """Return a localized four-frame learning sequence."""
    lang = i18n.current_lang(st)
    copy = {
        "en": [
            ("1. Observe", "What is the phenomenon?", "Write one prediction before reading the code.", "Ask AI only for a question that helps you notice the key idea."),
            ("2. Model", "How does the circuit represent it?", "Point to the qubit line, gate or operation, measurement, and classical output.", "Ask AI to check whether you identified the circuit parts correctly."),
            ("3. Code", "Which Qiskit line creates the effect?", "Name the line that prepares, changes, measures, or stores information.", "Ask AI for a hint about one code line, not a full solution."),
            ("4. Interpret", "What does the result mean?", "Write a reasoning sentence using measurement, shots, or counts.", "Ask AI to check your reasoning sentence and improve one phrase."),
        ],
        "ar": [
            ("1. ألاحظ", "ما الظاهرة التي أدرسها؟", "اكتب توقعًا واحدًا قبل قراءة الكود.", "اطلب من الذكاء الاصطناعي سؤالًا فقط يساعدك على ملاحظة الفكرة الأساسية."),
            ("2. أمثّل", "كيف تمثل الدارة هذه الظاهرة؟", "حدد خط qubit والبوابة أو العملية والقياس والخرج الكلاسيكي.", "اطلب من الذكاء الاصطناعي التحقق من تحديدك لأجزاء الدارة."),
            ("3. أربط بالكود", "أي سطر في Qiskit ينشئ التأثير؟", "سمّ السطر الذي يهيئ المعلومات أو يغيّرها أو يقيسها أو يخزنها.", "اطلب تلميحًا حول سطر واحد من الكود، لا حلًا كاملًا."),
            ("4. أفسّر", "ماذا تعني النتيجة؟", "اكتب جملة استدلال تستعمل measurement أو shots أو counts.", "اطلب التحقق من جملة استدلالك وتحسين عبارة واحدة."),
        ],
        "fr": [
            ("1. Observer", "Quel est le phénomène étudié ?", "Écrivez une prédiction avant de lire le code.", "Demandez à l'IA une seule question qui vous aide à repérer l'idée essentielle."),
            ("2. Modéliser", "Comment le circuit le représente-t-il ?", "Repérez la ligne du qubit, la porte ou l'opération, la mesure et la sortie classique.", "Demandez à l'IA de vérifier votre identification des parties du circuit."),
            ("3. Relier au code", "Quelle ligne Qiskit produit l'effet ?", "Nommez la ligne qui prépare, transforme, mesure ou stocke l'information.", "Demandez un indice sur une ligne de code, pas la solution complète."),
            ("4. Interpréter", "Que signifie le résultat ?", "Rédigez une phrase de raisonnement avec measurement, shots ou counts.", "Demandez à l'IA de vérifier votre raisonnement et d'améliorer une formulation."),
        ],
    }[lang]
    keys = ["observe", "model", "code", "interpret"]
    return [
        {
            "key": key,
            "label": values[0],
            "title": values[1],
            "image": f"sequence/{lesson_id}_{index:02d}_{key}.png",
            "student_action": values[2],
            "ai_rule": values[3],
        }
        for index, (key, values) in enumerate(zip(keys, copy), start=1)
    ]


def concept_flow_for_lesson(lesson: Dict[str, Any]) -> List[Dict[str, str]]:
    """Pedagogical route used by the concept studio and AI coach."""
    frames = lesson_sequence_frames(lesson["id"])
    visual_steps = lesson.get("visual_steps", []) or []
    code_focus = lesson.get("code_focus", []) or []
    lang = i18n.current_lang(st)
    before_label = {"ar": "قبل", "fr": "Avant", "en": "Before"}[lang]
    after_label = {"ar": "بعد", "fr": "Après", "en": "After"}[lang]
    body = [
        lesson.get("big_idea", lesson.get("concept", "")),
        " → ".join(visual_steps) if visual_steps else lesson.get("objective", ""),
        " ".join(code_focus[:2]) if code_focus else lesson.get("qiskit_code", ""),
        f"{before_label}: {lesson.get('before_measurement','')} {after_label}: {lesson.get('after_measurement','')}",
    ]
    for item, text in zip(frames, body):
        item["body"] = text
    return frames


def render_learning_route_overview(lesson: Dict[str, Any]) -> None:
    """A clear student-facing route: what to do, in what order, and why."""
    st.markdown("### Your learning route for this concept")
    st.caption("Follow the four steps in order. The AI coach is used after your first attempt, not before it.")
    steps = lesson_sequence_frames(lesson["id"])
    st.markdown("<div class='qai-route-strip'>", unsafe_allow_html=True)
    cols = st.columns(4)
    for col, step in zip(cols, steps):
        with col:
            st.markdown(
                f"""
                <div class='qai-route-step'>
                  <div class='qai-route-label'>{step['label']}</div>
                  <div class='qai-route-title'>{step['title']}</div>
                  <div class='qai-route-action'>{step['student_action']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


def render_concept_learning_studio(student: Dict[str, Any], lesson: Dict[str, Any]) -> None:
    """Render the organizing map for the lesson: one question, one route, one rule."""
    st.markdown("### Learning map")
    steps = concept_flow_for_lesson(lesson)
    st.markdown(
        f"""
        <div class='qai-v101-map-hero'>
          <div class='qai-v101-kicker'>Structured concept journey</div>
          <div class='qai-v101-title'>{lesson.get('title','')}</div>
          <div class='qai-v101-subtitle'>{lesson.get('objective','')}</div>
          <div class='qai-v101-focus'><b>Big idea:</b> {lesson.get('big_idea', lesson.get('concept', ''))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### What the student does")
    st.markdown("<div class='qai-v101-roadmap'>", unsafe_allow_html=True)
    cols = st.columns(4)
    for col, item in zip(cols, steps):
        with col:
            st.markdown(
                f"""
                <div class='qai-v101-road-card'>
                  <div class='qai-v101-road-num'>{item['label']}</div>
                  <div class='qai-v101-road-title'>{item['title']}</div>
                  <div class='qai-v101-road-body'>{item['student_action']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class='qai-v101-principle-grid'>
          <div><b>Visual first</b><br><span>The learner sees the circuit/state before reading long explanations.</span></div>
          <div><b>One change at a time</b><br><span>Each stage highlights only one conceptual change.</span></div>
          <div><b>Code bridge</b><br><span>The learner matches the visual event with the Qiskit line.</span></div>
          <div><b>AI after attempt</b><br><span>The AI coach checks or scaffolds, not replaces reasoning.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_genai_concept_coach(student: Dict[str, Any], lesson: Dict[str, Any]) -> None:
    """A step-aware GenAI coach that supports the concept sequence."""
    st.markdown("### GenAI learning coach")
    st.caption("Choose the step you are working on, write your attempt, then ask the AI for a limited type of support.")
    render_learning_route_overview(lesson)
    steps = concept_flow_for_lesson(lesson)
    step_labels = [s["label"] for s in steps]
    selected_label = st.selectbox("Which step are you working on?", step_labels, key=f"coach_step_{lesson['id']}")
    selected_step = next(s for s in steps if s["label"] == selected_label)
    st.markdown(
        f"""
        <div class='qai-ai-protocol'>
          <b>{selected_step['label']}:</b> {selected_step['title']}<br>
          <b>Your task:</b> {selected_step['student_action']}<br>
          <b>AI boundary:</b> {selected_step['ai_rule']}
        </div>
        """,
        unsafe_allow_html=True,
    )
    lang = st.selectbox(
        "Coach response language",
        ["Auto-detect", "English", "Arabic", "French"],
        index={"en": 1, "ar": 2, "fr": 3}[i18n.current_lang(st)],
        key=f"genai_coach_lang_{lesson['id']}",
        format_func=lambda value: i18n.tr(value),
    )
    attempt = st.text_area(
        "Your attempt first",
        placeholder="Write a prediction, explanation, code reading, or result interpretation before asking the AI coach...",
        height=120,
        key=f"genai_attempt_{lesson['id']}",
    )
    support_modes = [
        ("Ask me one question", "Ask one Socratic diagnostic question for this exact step. Do not give the answer."),
        ("Give one hint", "Give one concise hint for this step only, without solving it."),
        ("Check my explanation", "Evaluate my attempt: what is correct, what is missing, and one precise improvement."),
        ("Explain this step", "Give a layered explanation of this step only: intuition, visual, Qiskit, result."),
        ("Create practice", "Create one tiny practice item for this step and ask me to answer before showing a solution."),
    ]
    cols = st.columns(len(support_modes))
    selected_mode = None
    selected_instruction = None
    for col, (label, instruction) in zip(cols, support_modes):
        if col.button(i18n.tr(label), key=f"coach_{lesson['id']}_{selected_step['key']}_{label}", use_container_width=True):
            selected_mode = label
            selected_instruction = instruction
    if selected_mode:
        if len((attempt or "").strip()) < 8 and selected_mode in {"Ask me one question", "Give one hint", "Check my explanation"}:
            st.warning("Write a short attempt first. This keeps the AI tutor formative rather than answer-giving.")
            return
        log_ai_request_timing(
            student["id"],
            lesson["id"],
            "genai_learning_coach",
            task=selected_mode,
            step=selected_step.get("label", ""),
        )
        tutor = feedback_engine.generate_tutor_response(
            task=f"{selected_mode}: {selected_instruction}",
            concept=", ".join(lesson.get("concepts", [])),
            student_input=attempt or f"Support me on {selected_step['label']} for {lesson.get('title','this lesson')}.",
            student_profile=student_profile(student),
            lesson_context={
                **lesson,
                "response_language": lang,
                "selected_learning_step": selected_step,
                "pedagogical_mode": "step-aware concept coaching",
                "ai_use_policy": "Do not replace learner reasoning; scaffold with questions, hints, diagnosis, or limited explanation.",
            },
        )
        interaction_id = log_tutor_interaction(
            student["id"],
            "genai_learning_coach",
            ", ".join(lesson.get("concepts", [])),
            selected_mode,
            attempt or selected_instruction,
            tutor,
            lesson_id=lesson["id"],
            activity_id="genai_learning_coach",
            selected_text=f"{selected_step['label']} | {selected_instruction}",
        )
        st.markdown("#### AI coach response")
        st.write(tutor.response)
        render_ai_usefulness_feedback(interaction_id, f"genai_coach_{lesson['id']}_{interaction_id}")



def concept_builder_profile(lesson: Dict[str, Any]) -> Dict[str, Any]:
    """Curated pedagogical content for professional Concept Builder outputs."""
    lid = lesson.get("id", "orientation")
    profiles = {
        "orientation": {
            "phenomenon": "A Qiskit program becomes a circuit with quantum resources, operations, measurement, and classical output.",
            "key_line": "qc = QuantumCircuit(1, 1)",
            "qiskit_meaning": "The first number allocates one qubit; the second allocates one classical bit for measurement output.",
            "analogy": "Think of the circuit as a laboratory protocol: q0 is the object being tested, the measurement is the instrument, and c0 is the notebook where the observed value is recorded.",
            "analogy_limit": "Unlike a normal protocol, the quantum state before measurement is not just a hidden classical value waiting to be revealed.",
            "misconception_test": "If a learner says 'print(qc) gives the quantum result', they are confusing the circuit diagram with execution output.",
            "takeaway": "A circuit is a structured map of quantum and classical resources, read left to right.",
            "visual_label": "q0 wire -> measurement -> c0 output",
        },
        "qubit_measurement": {
            "phenomenon": "Measurement creates one classical outcome from a quantum state in each run.",
            "key_line": "qc.measure(0, 0)",
            "qiskit_meaning": "Measure qubit 0 and store the observed classical value in classical bit 0.",
            "analogy": "Measurement is like taking one photograph of a system: you get one recorded observation, not the entire underlying description.",
            "analogy_limit": "A qubit is not a hidden coin with a fixed face already chosen before you look.",
            "misconception_test": "If a learner says measurement displays the full quantum state, they are confusing state description with classical sample.",
            "takeaway": "Before measurement we discuss state; after measurement we discuss classical outcomes.",
            "visual_label": "state before -> measurement boundary -> classical value",
        },
        "hadamard_superposition": {
            "phenomenon": "H changes the qubit state before measurement; repeated measurement then reveals a balanced pattern.",
            "key_line": "qc.h(0)",
            "qiskit_meaning": "Apply a Hadamard gate to qubit 0, preparing a state that can later produce 0 or 1 with roughly equal frequency.",
            "analogy": "H is like changing the setup of an experiment before taking samples: it changes the conditions that determine the later pattern of observations.",
            "analogy_limit": "It is not accurate to say the qubit becomes two ordinary classical bits at once.",
            "misconception_test": "If a learner says 'H directly gives 0 and 1', they are mixing up state preparation with measurement outcomes.",
            "takeaway": "H is a state-changing operation; counts appear only after measurement and repeated shots.",
            "visual_label": "|0> -- H -- measure -> counts about 50/50",
        },
        "shots_counts": {
            "phenomenon": "Counts summarize repeated measurement outcomes; small samples fluctuate and larger samples stabilize.",
            "key_line": "counts = result.get_counts()",
            "qiskit_meaning": "Collect the observed bitstring frequencies after executing the circuit many times.",
            "analogy": "Shots are like repeated trials in a science experiment: one trial is not enough to see the pattern clearly.",
            "analogy_limit": "Counts are samples, not a direct printout of the quantum state itself.",
            "misconception_test": "If a learner treats {'0': 6, '1': 4} from 10 shots as a permanent law, they are ignoring sampling variation.",
            "takeaway": "Use proportions and repeated shots to interpret probabilistic output.",
            "visual_label": "10 shots fluctuate -> 1000 shots approximates the pattern",
        },
        "cnot_correlation": {
            "phenomenon": "CNOT links a control qubit and target qubit; with H before CNOT, outcomes can become correlated.",
            "key_line": "qc.cx(0, 1)",
            "qiskit_meaning": "Use qubit 0 as the control and qubit 1 as the target. The target flips when the control is 1.",
            "analogy": "CNOT is like a conditional rule: if the control condition is active, apply the change to the target.",
            "analogy_limit": "It is not a universal copying machine for arbitrary quantum states.",
            "misconception_test": "If a learner says CNOT simply copies q0 into q1 in all cases, they are missing the conditional control-target rule.",
            "takeaway": "Read CNOT as a two-qubit relationship: control first, target second.",
            "visual_label": "H on q0 -> CNOT(q0,q1) -> 00 and 11 dominate",
        },
        "qiskit_debugging": {
            "phenomenon": "Many Qiskit errors reveal mismatches between intended circuit resources and allocated resources.",
            "key_line": "qc = QuantumCircuit(1, 1)",
            "qiskit_meaning": "Allocate one qubit and one classical bit before measuring qubit 0 into classical bit 0.",
            "analogy": "Debugging is like checking a lab checklist: do you have the object, the instrument, and a place to record the result?",
            "analogy_limit": "Fixing syntax is not enough; the correction must also match the intended circuit meaning.",
            "misconception_test": "If a learner thinks the second argument of measure(0, 0) is another qubit, they are confusing qubit indices with classical-bit indices.",
            "takeaway": "Check qubits, classical bits, indices, and measurement mapping before interpreting output.",
            "visual_label": "wrong resource count -> error -> corrected circuit",
        },
    }
    profile = profiles.get(lid, profiles["orientation"]).copy()
    profile["title"] = lesson.get("title", "Concept")
    profile["big_idea"] = lesson.get("big_idea", lesson.get("concept", ""))
    profile["misconception"] = lesson.get("misconception", profile["misconception_test"])
    profile["takeaway"] = lesson.get("big_idea", profile["takeaway"])
    if lesson.get("code_focus"):
        profile["qiskit_meaning"] = " ".join(lesson.get("code_focus", [])[:2])
    profile["qiskit_code"] = lesson.get("qiskit_code", "")
    profile["check_question"] = lesson.get("check_question", "Explain the result in your own words.")
    lang = i18n.current_lang(st)
    localized_builder = {
        "ar": {
            "orientation": ("تخيّل الدارة بروتوكول مختبر: q0 هو النظام، وmeasurement أداة الملاحظة، وc0 دفتر تسجيل النتيجة.", "التشبيه يساعد على تمييز الموارد، لكنه لا يعني أن الحالة الكمية قيمة كلاسيكية مخفية.", "خط q0 ← measurement ← خرج c0"),
            "qubit_measurement": ("القياس يشبه التقاط صورة واحدة: نحصل على ملاحظة مسجلة، لا على الوصف الكامل للحالة.", "ليس qubit قطعة نقدية ذات وجه ثابت قبل النظر إليها.", "حالة كمية ← measurement ← قيمة كلاسيكية"),
            "hadamard_superposition": ("بوابة H تغيّر إعداد التجربة قبل أخذ العينات، فتغيّر نمط النتائج اللاحقة.", "لا يعني ذلك أن qubit أصبح بتّين كلاسيكيين في الوقت نفسه.", "|0⟩ ← H ← measurement ← counts تقارب 50/50"),
            "shots_counts": ("shots مثل تكرار التجربة العلمية: تجربة واحدة لا تكشف النمط بوضوح.", "counts عينات من النتائج وليست طباعة مباشرة للحالة الكمية.", "10 shots متذبذبة ← 1000 shots أوضح"),
            "cnot_correlation": ("CNOT قاعدة شرطية: عندما يكون control فعّالًا، يتغير target.", "CNOT ليست آلة نسخ عامة لأي حالة كمية.", "H على q0 ← CNOT(q0,q1) ← غالبًا 00 و11"),
            "qiskit_debugging": ("تصحيح الخطأ يشبه قائمة فحص مختبر: هل خصصت النظام وأداة القياس ومكان تسجيل النتيجة؟", "تصحيح الصياغة وحده لا يكفي؛ يجب أن يطابق التصحيح معنى الدارة المقصود.", "موارد ناقصة ← خطأ ← دارة مصححة"),
        },
        "fr": {
            "orientation": ("Pensez au circuit comme à un protocole de laboratoire : q0 est le système, measurement l'instrument et c0 le carnet de résultat.", "Cette analogie distingue les ressources, mais l'état quantique n'est pas une valeur classique cachée.", "ligne q0 → measurement → sortie c0"),
            "qubit_measurement": ("La mesure ressemble à une photographie unique : elle produit une observation enregistrée, pas la description complète de l'état.", "Un qubit n'est pas une pièce possédant déjà une face classique fixe.", "état quantique → measurement → valeur classique"),
            "hadamard_superposition": ("La porte H modifie la préparation de l'expérience avant l'échantillonnage et change donc le motif des résultats.", "Cela ne signifie pas que le qubit devient deux bits classiques simultanément.", "|0⟩ → H → measurement → counts proches de 50/50"),
            "shots_counts": ("Les shots ressemblent à des répétitions expérimentales : un seul essai ne suffit pas pour voir clairement le motif.", "Les counts sont des échantillons, pas une impression directe de l'état quantique.", "10 shots fluctuent → 1000 shots stabilisent"),
            "cnot_correlation": ("CNOT agit comme une règle conditionnelle : si le contrôle est actif, la cible bascule.", "CNOT n'est pas une machine universelle de copie d'états quantiques.", "H sur q0 → CNOT(q0,q1) → surtout 00 et 11"),
            "qiskit_debugging": ("Déboguer ressemble à vérifier une liste de laboratoire : système, instrument et emplacement d'enregistrement sont-ils disponibles ?", "Corriger la syntaxe ne suffit pas ; la correction doit respecter le sens du circuit visé.", "ressources insuffisantes → erreur → circuit corrigé"),
        },
    }
    if lang in localized_builder:
        analogy, analogy_limit, visual_label = localized_builder[lang].get(lid, localized_builder[lang]["orientation"])
        profile["phenomenon"] = lesson.get("concept", profile["phenomenon"])
        profile["analogy"] = analogy
        profile["analogy_limit"] = analogy_limit
        profile["misconception_test"] = lesson.get("misconception", profile["misconception_test"])
        profile["visual_label"] = visual_label
    return profile


def concept_builder_svg_card(lesson: Dict[str, Any]) -> str:
    """Return a localized safe visual card using approved templates."""
    profile = concept_builder_profile(lesson)
    title = profile["title"]
    focus = profile["takeaway"]
    label = profile["visual_label"]
    key_line = profile["key_line"]
    lang = i18n.current_lang(st)
    labels = {
        "ar": {"kicker": "دعامة بصرية مولدة من قالب", "chip": "SVG آمن", "observe": "ألاحظ", "model": "أمثّل", "interpret": "أقيس وأفسّر", "key": "سطر Qiskit الأساسي:", "footer": "تُولد هذه البطاقة من قالب درس تربوي معتمد، لا من كود تنفيذي عشوائي."},
        "fr": {"kicker": "Support visuel généré par modèle", "chip": "SVG sécurisé", "observe": "Observer", "model": "Modéliser", "interpret": "Mesurer / interpréter", "key": "Ligne Qiskit clé :", "footer": "Cette carte provient d'un modèle pédagogique validé, et non d'un code exécutable arbitraire."},
        "en": {"kicker": "Template-generated visual support", "chip": "safe SVG", "observe": "Observe", "model": "Model", "interpret": "Measure / interpret", "key": "Key Qiskit line:", "footer": "This card is generated from an approved lesson template, not arbitrary executable AI code."},
    }[lang]
    return f"""
    <div class='qai-builder-pro-card'>
      <div class='qai-builder-pro-head'>
        <div>
          <div class='qai-builder-kicker'>{labels['kicker']}</div>
          <div class='qai-builder-title'>{title}</div>
          <div class='qai-builder-sub'>{focus}</div>
        </div>
        <div class='qai-builder-chip'>{labels['chip']}</div>
      </div>
      <div class='qai-builder-diagram'>
        <div class='qai-node qai-node-blue'>{labels['observe']}</div>
        <div class='qai-arrow'>→</div>
        <div class='qai-node qai-node-indigo'>{labels['model']}</div>
        <div class='qai-arrow'>→</div>
        <div class='qai-node qai-node-teal'>{labels['interpret']}</div>
      </div>
      <div class='qai-builder-visual-line'>{label}</div>
      <div class='qai-builder-code-line'><b>{labels['key']}</b> <code>{key_line}</code></div>
      <div class='qai-builder-footer'>{labels['footer']}</div>
    </div>
    """


def professional_concept_builder_output(lesson: Dict[str, Any], mode: str, attempt: str, language: str = "English") -> str:
    """Curated professional outputs for the Concept Builder.

    This avoids weak generic LLM answers and ensures every generated support
    follows a stable pedagogical structure: concept, visual meaning, code bridge,
    misconception warning, and learner action.
    """
    p = concept_builder_profile(lesson)
    arabic = language == "Arabic"
    if arabic:
        # Keep code terms in English for Qiskit clarity.
        if mode == "simpler_explanation":
            return f"""### شرح مبسّط ومنظّم

**الفكرة الأساسية:** {p['phenomenon']}

**ما يجب أن يلاحظه الطالب بصريًا:**  
{p['takeaway']}

**الربط مع Qiskit:**  
`{p['key_line']}`  
{p['qiskit_meaning']}

**تنبيه ضد سوء الفهم:**  
{p['misconception']}

**مهمة قصيرة:** اكتب بجملة واحدة: ما الذي يحدث قبل القياس؟ وما الذي لا يظهر إلا بعد القياس؟"""
        if mode == "analogy":
            return f"""### تشبيه تعليمي مضبوط

**التشبيه:**  
{p['analogy']}

**حدود التشبيه:**  
{p['analogy_limit']}

**كيف تستعمله في الفهم؟**  
استعمل التشبيه فقط لتذكّر البنية العامة، ثم ارجع دائمًا إلى الدارة والكود.

**سؤال للطالب:** أين يظهر هذا المعنى في السطر `{p['key_line']}`؟"""
        if mode == "misconception_check":
            return f"""### فحص سوء فهم

**تصريح محتمل من الطالب:**  
{p['misconception_test']}

**لماذا هذا مهم؟**  
لأنه يكشف هل الطالب يخلط بين الحالة قبل القياس، والكود، والنتيجة الكلاسيكية بعد القياس.

**سؤال تشخيصي:**  
{p['check_question']}

**إجابة جيدة يجب أن تذكر:**  
- ما الذي يتغير داخل الدارة.  
- أين يظهر ذلك في Qiskit.  
- ماذا تعني النتيجة بعد measurement/counts."""
        if mode == "mini_quiz":
            return f"""### اختبار تكويني قصير

1. **Concept:** {p['check_question']}  
2. **Code reading:** ماذا يفعل السطر `{p['key_line']}`؟  
3. **Interpretation:** كيف تربط النتيجة المرئية بفكرة: {p['takeaway']}؟

**قاعدة التصحيح:** الإجابة الجيدة يجب أن تميز بين ما يحدث قبل measurement وما يظهر بعد measurement/counts."""
        if mode == "qiskit_bridge":
            return f"""### الربط مع Qiskit

**السطر المفتاحي:**  
`{p['key_line']}`

**معناه:**  
{p['qiskit_meaning']}

**كيف تقرأ الكود؟**
```python
{p['qiskit_code']}
```

**ما الذي يجب شرحه:**  
{p['takeaway']}

**سؤال متابعة:** اشرح لماذا لا يكفي النظر إلى الكود دون تفسير القياس أو counts."""
    if language == "French":
        if mode == "simpler_explanation":
            return f"""### Explication structurée

**Idée essentielle.**  
{p['big_idea'] or p['phenomenon']}

**Ce que la représentation visuelle met en évidence.**  
{p['takeaway']}

**Lien avec Qiskit.**  
`{p['key_line']}`  
{p['qiskit_meaning']}

**Attention à la confusion fréquente.**  
{p['misconception']}

**Action de l'apprenant.**  
Rédigez une phrase qui distingue ce qui change avant la mesure de ce qui est observé après measurement/counts."""
        if mode == "analogy":
            return f"""### Analogie guidée

**Analogie.**  
{p['analogy']}

**Limite de l'analogie.**  
{p['analogy_limit']}

**Usage pédagogique.**  
Utilisez l'analogie pour organiser l'idée, puis revenez au circuit et à la ligne Qiskit mise en évidence.

**Auto-vérification.**  
Où la ligne `{p['key_line']}` intervient-elle exactement dans le processus ?"""
        if mode == "misconception_check":
            return f"""### Diagnostic d'une conception erronée

**Confusion possible.**  
{p['misconception']}

**Question diagnostique.**  
{p['check_question']}

**Une réponse solide doit mentionner :**
- l'opération ou la ressource du circuit ;
- la ligne Qiskit correspondante ;
- le sens du résultat après measurement ou après plusieurs shots."""
        if mode == "mini_quiz":
            return f"""### Mini-quiz formatif

1. **Concept :** {p['check_question']}  
2. **Lecture du code :** Que fait `{p['key_line']}` dans cette leçon ?  
3. **Interprétation :** Comment la représentation visuelle soutient-elle l'idée suivante : {p['takeaway']} ?

**Critère de réussite.**  
La réponse distingue l'opération du circuit du résultat de mesure observé et emploie au moins un terme Qiskit correct."""
        if mode == "qiskit_bridge":
            return f"""### Du code au concept

**Ligne clé.**  
`{p['key_line']}`

**Signification.**  
{p['qiskit_meaning']}

**Contexte minimal.**
```python
{p['qiskit_code']}
```

**Lien visuel à expliquer.**  
{p['takeaway']}

**Question de suivi.**  
Pourquoi la lecture du code ne suffit-elle pas sans interpréter measurement et counts ?"""
    # English professional outputs.
    if mode == "simpler_explanation":
        return f"""### Structured explanation

**Core idea.**  
{p['phenomenon']}

**What the visual is trying to show.**  
{p['takeaway']}

**Qiskit bridge.**  
`{p['key_line']}`  
{p['qiskit_meaning']}

**Misconception warning.**  
{p['misconception']}

**Learner action.**  
Write one sentence that separates *what changes before measurement* from *what is observed after measurement/counts*."""
    if mode == "analogy":
        return f"""### Careful analogy

**Analogy.**  
{p['analogy']}

**Where the analogy breaks down.**  
{p['analogy_limit']}

**How to use it productively.**  
Use the analogy only to organize the idea, then return to the circuit and the highlighted Qiskit line.

**Check yourself.**  
Where exactly does `{p['key_line']}` appear in the visual process?"""
    if mode == "misconception_check":
        return f"""### Misconception diagnosis

**Possible misconception.**  
{p['misconception_test']}

**What this misconception reveals.**  
The learner may be confusing the state before measurement, the code operation, and the classical result after measurement.

**Diagnostic question.**  
{p['check_question']}

**A strong answer should mention:**
- the circuit operation or resource being used;
- the exact Qiskit line connected to it;
- the interpretation of the result after measurement or repeated shots."""
    if mode == "mini_quiz":
        return f"""### Mini formative quiz

1. **Concept question:** {p['check_question']}  
2. **Code-reading question:** What does `{p['key_line']}` do in this lesson?  
3. **Interpretation question:** How does the visual support the idea that {p['takeaway'].lower()}?

**Scoring guide.**  
A strong response distinguishes the circuit operation from the observed measurement result and uses at least one correct Qiskit term."""
    if mode == "qiskit_bridge":
        return f"""### Code-to-concept bridge

**Key line.**  
`{p['key_line']}`

**Meaning.**  
{p['qiskit_meaning']}

**Minimal context.**
```python
{p['qiskit_code']}
```

**What to connect visually.**  
{p['takeaway']}

**Follow-up prompt.**  
Explain why reading the code is not enough unless you also interpret measurement and counts."""
    return professional_concept_builder_output(lesson, "simpler_explanation", attempt, language)


def render_concept_builder(student: Dict[str, Any], lesson: Dict[str, Any]) -> None:
    """Generate controlled, professional learning supports from approved pedagogical templates."""
    st.markdown("### Concept Builder")
    st.caption("Generate polished learning supports after writing your own attempt. Outputs are curated around the current lesson, not open-ended free generation.")
    st.markdown(
        """
        <div class='qai-builder-rule'>
          <b>Research rule:</b> write your own attempt first. The builder produces structured explanations, analogies, checks, Qiskit bridges, and safe visual cards from approved pedagogical templates.
        </div>
        """,
        unsafe_allow_html=True,
    )
    attempt = st.text_area(
        "Your attempt before generation",
        placeholder="Write what you think the concept means, what the circuit does, or what confuses you...",
        height=115,
        key=f"concept_builder_attempt_{lesson['id']}",
    )
    builder_languages = ["English", "Arabic", "French"]
    builder_default = {"en": 0, "ar": 1, "fr": 2}[i18n.current_lang(st)]
    language = st.selectbox(
        "Output language",
        builder_languages,
        index=builder_default,
        key=f"concept_builder_language_{lesson['id']}",
        format_func=lambda value: i18n.tr(value),
    )
    mode_specs = [
        ("simpler_explanation", "Generate structured explanation"),
        ("analogy", "Generate careful analogy"),
        ("misconception_check", "Generate misconception diagnosis"),
        ("mini_quiz", "Generate mini formative quiz"),
        ("qiskit_bridge", "Connect to Qiskit professionally"),
        ("svg_card", "Generate polished visual card"),
    ]
    cols = st.columns(3)
    selected = None
    for idx, (key, label) in enumerate(mode_specs):
        with cols[idx % 3]:
            if st.button(label, key=f"concept_builder_{lesson['id']}_{key}", use_container_width=True):
                selected = (key, label)
    if not selected:
        return
    key, label = selected
    if len((attempt or "").strip()) < 8:
        st.warning("Write a short attempt first. This preserves the research value of measuring AI-supported learning after learner effort.")
        return
    try:
        db.log_event(student["id"], "student", "concept_builder_request", json.dumps({
            "lesson_id": lesson["id"],
            "mode": key,
            "attempt_chars": len(attempt or ""),
            "output_type": "curated_template",
        }))
    except Exception:
        pass
    log_ai_request_timing(student["id"], lesson["id"], "concept_builder", task=key, step="builder")
    if key == "svg_card":
        st.markdown("#### Generated visual card")
        st.markdown(concept_builder_svg_card(lesson), unsafe_allow_html=True)
        try:
            db.log_event(student["id"], "student", "generated_visual_card", json.dumps({"lesson_id": lesson["id"], "mode": key, "quality": "curated_template"}))
        except Exception:
            pass
        return

    response = professional_concept_builder_output(lesson, key, attempt, language)
    tutor = feedback_engine.TutorResult(
        response=response,
        mode="curated_template",
        provider="platform",
        model="concept-builder-v12.4",
        diagnostic="curated professional concept-builder output",
        latency_ms=0,
        response_word_count=len(response.split()),
        student_input_language=feedback_engine.detect_input_language(attempt),
        response_language=language,
        is_fallback_used=0,
    )
    interaction_id = log_tutor_interaction(
        student["id"],
        "concept_builder",
        ", ".join(lesson.get("concepts", [])),
        key,
        attempt,
        tutor,
        lesson_id=lesson["id"],
        activity_id="concept_builder",
        selected_text=label,
    )
    st.markdown(f"#### {label}")
    st.markdown(response)
    try:
        db.log_event(student["id"], "student", f"concept_builder_{key}", json.dumps({"lesson_id": lesson["id"], "interaction_id": interaction_id, "quality": "curated_template"}))
    except Exception:
        pass
    render_ai_usefulness_feedback(interaction_id, f"concept_builder_{lesson['id']}_{key}_{interaction_id}")


def render_lesson_media(lesson_id: str, student: Optional[Dict[str, Any]] = None) -> None:
    """V11 visual learning flow: animation, simulator, code bridge, quick checks."""
    media = localized_media(lesson_id)
    lesson = content.lesson_by_id(lesson_id, i18n.current_lang(st))
    sid = student.get("id") if student else None

    st.markdown(
        f"""
        <div class='qai-v11-preview'>
          <div class='qai-v11-kicker'>V11 structured visual learning</div>
          <div class='qai-v11-title'>{lesson.get('title','')}</div>
          <div class='qai-v11-goal'><b>Goal:</b> {lesson.get('objective', media.get('caption',''))}</div>
          <div class='qai-v11-goal'><b>Focus question:</b> {lesson.get('mini_task', lesson.get('check_question', 'What changes, and what is merely observed?'))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    step_html = "".join([
        f"<div class='qai-v11-step'><span>{i}</span><b>{label}</b><br><small>{desc}</small></div>"
        for i, (label, desc) in enumerate([
            ("Watch", "See the core idea in motion."),
            ("Simulate", "Step through the visual model."),
            ("Connect", "Map the visual to Qiskit."),
            ("Check", "Explain what the result means."),
        ], start=1)
    ])
    st.markdown(f"<div class='qai-v11-steps'>{step_html}</div>", unsafe_allow_html=True)

    st.markdown("<div class='qai-v11-section'><div class='qai-v11-section-title'>1. Watch the idea</div>", unsafe_allow_html=True)
    if render_micro_animation(lesson_id, ANIMATION_MEDIA_DIR):
        if sid:
            try: db.log_event(sid, "student", "animation_viewed", lesson_id)
            except Exception: pass
    else:
        st.info("Concept animation will appear here once the MP4 is available.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='qai-v11-section'><div class='qai-v11-section-title'>2. Use the simulator</div>", unsafe_allow_html=True)
    if render_simulator(lesson_id, INTERACTIVE_MEDIA_DIR):
        if sid:
            try: db.log_event(sid, "student", "simulator_opened", lesson_id)
            except Exception: pass
    else:
        st.warning("Interactive simulator missing. This module should not be used in a study until it is restored.")
    sim_key = f"v11_sim_completed_{sid}_{lesson_id}"
    sim_log_key = f"v11_sim_completed_logged_{sid}_{lesson_id}"
    if st.checkbox("I completed the simulator steps", key=sim_key):
        if sid and not st.session_state.get(sim_log_key):
            try:
                db.log_event(sid, "student", "simulator_completed", json.dumps({"lesson_id": lesson_id, "self_report": True}))
                st.session_state[sim_log_key] = True
            except Exception: pass
        st.success("Simulator completion recorded.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='qai-v11-section'><div class='qai-v11-section-title'>3. Connect to Qiskit</div>", unsafe_allow_html=True)
    left, right = st.columns([0.58, 0.42], gap="large")
    with left:
        st.code(lesson.get("qiskit_code", ""), language="python")
    with right:
        st.markdown(
            f"""
            <div class='qai-v11-side'>
              <h4>What to connect</h4>
              <p><b>Before measurement:</b><br>{lesson.get('before_measurement', '')}</p>
              <p><b>After measurement / output:</b><br>{lesson.get('after_measurement', '')}</p>
              <p><b>Avoid this misconception:</b><br>{lesson.get('misconception', '')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='qai-v11-section'><div class='qai-v11-section-title'>4. Check your understanding</div>", unsafe_allow_html=True)
    if lesson.get("check_question"):
        st.markdown(f"<div class='qai-v11-check'><b>Question:</b> {lesson.get('check_question')}</div>", unsafe_allow_html=True)
    response_key = f"v11_check_{sid}_{lesson_id}"
    answer = st.text_area("Write one short explanation before using AI", key=response_key, height=90)
    if st.button("Save my explanation", key=f"save_v11_check_{sid}_{lesson_id}"):
        if sid:
            try: db.log_event(sid, "student", "check_answered", json.dumps({"lesson_id": lesson_id, "answer": answer[:800]}))
            except Exception: pass
        st.success("Saved.")
    st.markdown("</div>", unsafe_allow_html=True)
    guardrail_copy = {
        "ar": ("ملاحظة تربوية", "أُخفيت الصور الثابتة القديمة والمقاطع المصغرة السابقة من مسار المتعلم. وتعتمد الوحدة الآن على الحركة المصغرة والمحاكي وجسر الكود وفحص الفهم."),
        "fr": ("Note pédagogique", "Les anciennes images statiques et micro-vidéos ont été retirées du parcours. Le module s’appuie désormais sur la micro-animation, le simulateur, le pont vers le code et la vérification de compréhension."),
        "en": ("Pedagogical note", "Old static images and legacy micro-videos are hidden from the learner path. Active materials are the micro-animation, simulator, code bridge, and understanding check."),
    }[i18n.current_lang(st)]
    st.markdown(
        f"<div class='qai-v11-no-legacy' dir='{i18n.direction(i18n.current_lang(st))}'><b>{escape(guardrail_copy[0])}:</b> {escape(guardrail_copy[1])}</div>",
        unsafe_allow_html=True,
    )
    resource_url = media.get("resource_url")
    resource_label = media.get("resource_label", "Optional external resource")
    if resource_url:
        st.markdown(f"Optional enrichment: [{resource_label}]({resource_url})")


def render_learning_path_cards(student: Dict[str, Any], selected_id: str, recommended_set: set, completed: set) -> None:
    u = learning_ui_copy()
    lessons = localized_lessons()
    st.markdown(f"<div class='v43-section-title' dir='{u['dir']}'><span>{escape(u['journey'])}</span><h3>{escape(u['path_title'])}</h3><p>{escape(u['path_sub'])}</p></div>", unsafe_allow_html=True)
    for start in range(0, len(lessons), 3):
        row = lessons[start:start+3]
        cols = st.columns(len(row), gap="medium")
        for col, lesson in zip(cols, row):
            selected = lesson["id"] == selected_id
            done = lesson["id"] in completed
            recommended = lesson["id"] in recommended_set
            status = u["completed"] if done else (u["recommended"] if recommended else u["available"])
            idx = lessons.index(lesson) + 1
            tags = "".join(f"<span>{escape(i18n.concept_label(c, i18n.current_lang(st)))}</span>" for c in lesson.get("concepts", [])[:2])
            with col:
                st.markdown(f"""
                <article class='v43-lesson-card {'is-active' if selected else ''} {'is-done' if done else ''}' dir='{u['dir']}'>
                  <div class='v43-lesson-top'><i>{idx:02d}</i><span>{escape(status)}</span></div>
                  <h4>{escape(lesson.get('short_title', lesson['title']))}</h4>
                  <p>{escape(lesson.get('objective',''))}</p>
                  <div class='v43-lesson-tags'>{tags}</div><small>{escape(lesson.get('duration',''))}</small>
                </article>""", unsafe_allow_html=True)
                if st.button(u["opened"] if selected else u["open"], key=f"open_lesson_{lesson['id']}", disabled=selected, use_container_width=True):
                    set_current_lesson(student["id"], lesson["id"]); st.rerun()

def student_workspace_copy() -> Dict[str, str]:
    lang = i18n.current_lang(st)
    return {
        "ar": {
            "workspace": "بيئة تعلّم الطالب",
            "subtitle": "مسار واضح يجمع الفهم البصري، التجربة، Qiskit، والمدرّب التوليدي بعد محاولة المتعلّم.",
            "stage": "المرحلة الحالية",
            "module": "الوحدة",
            "of": "من",
            "path_progress": "تقدم المسار",
            "course_map": "خريطة الوحدات",
            "course_map_help": "افتح الخريطة للانتقال بين الوحدات دون إطالة الصفحة.",
            "learn_panel": "الدرس والتجربة",
            "coach_panel": "المدرّب الذكي",
            "coach_help": "اكتب محاولة قصيرة أولًا، ثم اختر نوع المساعدة المطلوب.",
            "understand": "افهم",
            "visual": "شاهد وجرّب",
            "qiskit": "جسر Qiskit",
            "check": "تحقق من فهمك",
            "goal": "هدف الوحدة",
            "big_idea": "الفكرة الكبرى",
            "why": "لماذا يهم هذا المفهوم؟",
            "can_do": "بعد هذه الوحدة ستتمكن من",
            "misconception": "تصور خاطئ يجب تجنبه",
            "code_focus": "كيف تقرأ الكود؟",
            "attempt": "محاولتك قبل طلب المساعدة",
            "attempt_ph": "اكتب توقعك، تفسيرك، أو ما فهمته من الكود في سطرين على الأقل…",
            "quick_support": "مساعدة سريعة",
            "hint": "تلميح واحد",
            "simplify": "اشرح ببساطة",
            "qiskit_example": "اربطه بـ Qiskit",
            "quiz": "اختبر فهمي",
            "send": "اطلب المساعدة",
            "full_tutor": "فتح المحادثة الكاملة",
            "ai_policy": "المدرّب يوجّه التفكير ولا يستبدل محاولة المتعلّم.",
            "no_ai": "هذا المسار لا يعرض أدوات الذكاء الاصطناعي وفق تصميم مجموعة الدراسة.",
            "reflection": "تأمل الوحدة وإكمالها",
            "reflection_ph": "ما الذي أصبح واضحًا؟ وما الفكرة التي ما زالت تحتاج مراجعة؟",
            "save_complete": "حفظ التأمل وإكمال الوحدة",
            "previous": "الوحدة السابقة",
            "next": "الوحدة التالية",
            "review": "مراجعة المسار",
            "completed": "مكتملة",
            "recommended": "موصى بها",
            "available": "متاحة",
            "status": "حالة الوحدة",
            "route_rule": "حاول ← شاهد وجرّب ← اطلب تلميحًا ← أثبت الفهم",
            "response": "استجابة المدرّب",
            "need_attempt": "اكتب محاولة قصيرة أولًا حتى تبقى المساعدة تكوينية.",
            "saved": "تم حفظ التأمل وإكمال الوحدة.",
            "min_reflection": "اكتب تأملًا قصيرًا من 20 حرفًا على الأقل.",
        },
        "fr": {
            "workspace": "Espace d’apprentissage",
            "subtitle": "Un parcours clair qui combine compréhension visuelle, expérimentation, Qiskit et coaching génératif après une première tentative.",
            "stage": "Étape actuelle", "module": "Module", "of": "sur", "path_progress": "Progression du parcours",
            "course_map": "Carte des modules", "course_map_help": "Ouvrez la carte pour changer de module sans allonger la page.",
            "learn_panel": "Leçon et expérimentation", "coach_panel": "Coach intelligent", "coach_help": "Rédigez d’abord une courte tentative, puis choisissez le type d’aide.",
            "understand": "Comprendre", "visual": "Voir et expérimenter", "qiskit": "Pont Qiskit", "check": "Vérifier la compréhension",
            "goal": "Objectif", "big_idea": "Idée centrale", "why": "Pourquoi ce concept est important", "can_do": "À la fin, vous pourrez",
            "misconception": "Erreur conceptuelle à éviter", "code_focus": "Comment lire le code", "attempt": "Votre tentative avant l’aide",
            "attempt_ph": "Écrivez votre prédiction, votre explication ou votre lecture du code en au moins deux lignes…",
            "quick_support": "Aide rapide", "hint": "Un indice", "simplify": "Expliquer simplement", "qiskit_example": "Relier à Qiskit", "quiz": "Tester ma compréhension",
            "send": "Demander de l’aide", "full_tutor": "Ouvrir la conversation complète", "ai_policy": "Le coach guide le raisonnement sans remplacer la tentative de l’apprenant.",
            "no_ai": "Les outils d’IA sont masqués pour ce parcours selon le protocole de l’étude.", "reflection": "Réflexion et validation du module",
            "reflection_ph": "Qu’est-ce qui est devenu clair ? Quel point doit encore être revu ?", "save_complete": "Enregistrer et terminer le module",
            "previous": "Module précédent", "next": "Module suivant", "review": "Revoir le parcours", "completed": "Terminé", "recommended": "Recommandé", "available": "Disponible",
            "status": "État du module", "route_rule": "Essayer ← Observer et pratiquer ← Demander un indice ← Prouver sa compréhension",
            "response": "Réponse du coach", "need_attempt": "Écrivez d’abord une courte tentative afin de préserver une aide formative.",
            "saved": "Réflexion enregistrée et module terminé.", "min_reflection": "Rédigez une réflexion d’au moins 20 caractères.",
        },
        "en": {
            "workspace": "Student learning workspace",
            "subtitle": "A clear flow combining visual understanding, experimentation, Qiskit, and generative coaching after the learner's first attempt.",
            "stage": "Current stage", "module": "Module", "of": "of", "path_progress": "Path progress",
            "course_map": "Module map", "course_map_help": "Open the map to change modules without making the page unnecessarily long.",
            "learn_panel": "Lesson and experiment", "coach_panel": "AI learning coach", "coach_help": "Write a short attempt first, then choose the kind of support you need.",
            "understand": "Understand", "visual": "See and experiment", "qiskit": "Qiskit bridge", "check": "Check understanding",
            "goal": "Module goal", "big_idea": "Big idea", "why": "Why this concept matters", "can_do": "By the end you can",
            "misconception": "Misconception to avoid", "code_focus": "How to read the code", "attempt": "Your attempt before support",
            "attempt_ph": "Write your prediction, explanation, or code reading in at least two lines…",
            "quick_support": "Quick support", "hint": "One hint", "simplify": "Explain simply", "qiskit_example": "Connect to Qiskit", "quiz": "Test my understanding",
            "send": "Ask for support", "full_tutor": "Open full conversation", "ai_policy": "The coach guides reasoning; it does not replace the learner's attempt.",
            "no_ai": "AI tools are hidden for this pathway under the study design.", "reflection": "Reflect and complete the module",
            "reflection_ph": "What became clear, and what still needs review?", "save_complete": "Save reflection and complete module",
            "previous": "Previous module", "next": "Next module", "review": "Review path", "completed": "Completed", "recommended": "Recommended", "available": "Available",
            "status": "Module status", "route_rule": "Attempt ← See and experiment ← Ask for a hint ← Prove understanding",
            "response": "Coach response", "need_attempt": "Write a short attempt first so the support remains formative.",
            "saved": "Reflection saved and module completed.", "min_reflection": "Write a reflection of at least 20 characters.",
        },
    }[lang]


def render_v66_stage_header(student: Dict[str, Any], lesson: Dict[str, Any], completed: set) -> None:
    copy = student_workspace_copy()
    lang = i18n.current_lang(st)
    direction = i18n.direction(lang)
    ids = [item["id"] for item in content.LESSONS]
    index = ids.index(lesson["id"]) + 1
    pct = int(round(100 * len(completed) / max(len(ids), 1)))
    status = copy["completed"] if lesson["id"] in completed else copy["available"]
    st.markdown(
        f"""
        <section class='v66-stage-header v68-stage-header' dir='{direction}'>
          <div class='v66-stage-copy v68-stage-copy'>
            <span>{escape(copy['workspace'])}</span>
            <h1>{escape(lesson.get('short_title', lesson['title']))}</h1>
            <p>{escape(copy['subtitle'])}</p>
          </div>
          <div class='v66-stage-meta v68-stage-meta'>
            <div><small>{escape(copy['stage'])}</small><strong>{escape(copy['module'])} {index} {escape(copy['of'])} {len(ids)}</strong></div>
            <div><small>{escape(copy['status'])}</small><strong>{escape(status)}</strong></div>
            <div class='v66-stage-progress'><small>{escape(copy['path_progress'])}</small><strong>{pct}%</strong><i><em style='width:{pct}%'></em></i></div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_v66_ai_coach(student: Dict[str, Any], lesson: Dict[str, Any]) -> None:
    copy = student_workspace_copy()
    lang = i18n.current_lang(st)
    direction = i18n.direction(lang)
    st.markdown(
        f"""
        <div class='v66-panel-heading' dir='{direction}'>
          <span>AI</span><div><h3>{escape(copy['coach_panel'])}</h3><p>{escape(copy['coach_help'])}</p></div>
        </div>
        <div class='v66-ai-policy' dir='{direction}'>{escape(copy['ai_policy'])}</div>
        """,
        unsafe_allow_html=True,
    )
    if not ai_features_available(student):
        st.info(copy["no_ai"])
        return

    attempt_key = f"v66_attempt_{lesson['id']}"
    attempt = st.text_area(
        copy["attempt"],
        placeholder=copy["attempt_ph"],
        height=138,
        key=attempt_key,
    )
    st.markdown(f"<div class='v66-quick-label' dir='{direction}'>{escape(copy['quick_support'])}</div>", unsafe_allow_html=True)
    modes = [
        ("hint", copy["hint"], "Give one concise hint and one check question. Do not reveal a full answer."),
        ("simplify", copy["simplify"], "Explain the current concept simply using one analogy, then ask one diagnostic question."),
        ("qiskit", copy["qiskit_example"], "Connect the learner's attempt to the smallest relevant Qiskit code idea. Do not solve the whole task."),
        ("quiz", copy["quiz"], "Create one short formative question about this module and wait for the learner's answer."),
    ]
    selected = st.session_state.get(f"v66_mode_{lesson['id']}", "hint")
    with st.container(key=f"v68_quick_support_{lesson['id']}"):
        st.markdown("<span class='v68-quick-grid-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
        button_cols = st.columns(2, gap="small")
        for idx, (mode_key, label, instruction) in enumerate(modes):
            with button_cols[idx % 2]:
                if st.button(
                    label,
                    key=f"v66_mode_btn_{lesson['id']}_{mode_key}",
                    use_container_width=True,
                    type="primary" if selected == mode_key else "secondary",
                ):
                    st.session_state[f"v66_mode_{lesson['id']}"] = mode_key
                    selected = mode_key
                    st.rerun()

    selected_mode = next(item for item in modes if item[0] == selected)
    if st.button(copy["send"], key=f"v66_send_{lesson['id']}", type="primary", use_container_width=True):
        if len((attempt or "").strip()) < 8:
            st.warning(copy["need_attempt"])
        else:
            log_ai_request_timing(student["id"], lesson["id"], "v66_student_workspace", task=selected_mode[1], step="workspace")
            with st.spinner("…"):
                tutor = feedback_engine.generate_tutor_response(
                    task=f"{selected_mode[1]}: {selected_mode[2]}",
                    concept=", ".join(lesson.get("concepts", [])),
                    student_input=attempt,
                    student_profile=student_profile(student),
                    lesson_context={
                        **lesson,
                        "response_language": {"ar": "Arabic", "fr": "French", "en": "English"}[lang],
                        "pedagogical_mode": "student workspace compact coach",
                        "ai_use_policy": "Support after learner attempt. Scaffold, diagnose, and ask questions. Avoid answer dumping.",
                    },
                )
            interaction_id = log_tutor_interaction(
                student["id"], "student_workspace", ", ".join(lesson.get("concepts", [])), selected_mode[1], attempt, tutor,
                lesson_id=lesson["id"], activity_id="v66_compact_coach", selected_text=selected_mode[2],
            )
            st.session_state[f"v66_response_{lesson['id']}"] = {"text": tutor.response, "id": interaction_id}

    response = st.session_state.get(f"v66_response_{lesson['id']}")
    if response:
        st.markdown(f"<div class='v66-response-title' dir='{direction}'>{escape(copy['response'])}</div>", unsafe_allow_html=True)
        with st.chat_message("assistant"):
            st.write(response["text"])
            if response.get("id"):
                render_ai_usefulness_feedback(response["id"], f"v66_{lesson['id']}_{response['id']}")

    if st.button(copy["full_tutor"], key=f"v66_full_tutor_{lesson['id']}", use_container_width=True):
        st.session_state.current_lesson_id = lesson["id"]
        set_student_page("AI Tutor Lab")


def render_v66_lesson_content(student: Dict[str, Any], lesson: Dict[str, Any]) -> None:
    copy = student_workspace_copy()
    direction = i18n.direction(i18n.current_lang(st))
    understand_tab, visual_tab, code_tab, check_tab = st.tabs([
        copy["understand"], copy["visual"], copy["qiskit"], copy["check"],
    ])
    with understand_tab:
        st.markdown(
            f"""
            <div class='v66-concept-hero' dir='{direction}'>
              <span>{escape(copy['goal'])}</span><h2>{escape(lesson.get('objective',''))}</h2>
              <div><b>{escape(copy['big_idea'])}</b><p>{escape(lesson.get('big_idea', lesson.get('concept','')))}</p></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns([1.08, .92], gap="large")
        with col1:
            st.markdown(f"#### {copy['understand']}")
            st.write(lesson.get("concept", ""))
            st.markdown(f"#### {copy['why']}")
            st.write(lesson.get("why_it_matters", ""))
        with col2:
            if lesson.get("can_do"):
                st.markdown(f"#### {copy['can_do']}")
                st.markdown("<ul class='v66-outcomes'>" + "".join(f"<li>{escape(str(item))}</li>" for item in lesson.get("can_do", [])) + "</ul>", unsafe_allow_html=True)
            st.markdown(f"#### {copy['misconception']}")
            st.warning(lesson.get("misconception", ""))

    with visual_tab:
        st.markdown(f"<div class='v66-route-rule' dir='{direction}'>{escape(copy['route_rule'])}</div>", unsafe_allow_html=True)
        render_lesson_media(lesson["id"], student)

    with code_tab:
        left, right = st.columns([1.08, .92], gap="large")
        with left:
            st.markdown("#### Qiskit")
            st.code(lesson.get("qiskit_code", ""), language="python")
        with right:
            st.markdown(f"#### {copy['code_focus']}")
            for point in lesson.get("code_focus", []):
                st.markdown(f"- {point}")
            if lesson.get("before_measurement") or lesson.get("after_measurement"):
                st.markdown(
                    f"<div class='v66-before-after'><div><b>Before</b><span>{escape(lesson.get('before_measurement',''))}</span></div><div><b>After</b><span>{escape(lesson.get('after_measurement',''))}</span></div></div>",
                    unsafe_allow_html=True,
                )

    with check_tab:
        st.markdown(f"<div class='v66-check-card' dir='{direction}'><b>{escape(copy['check'])}</b><p>{escape(lesson.get('mini_task',''))}</p></div>", unsafe_allow_html=True)
        if lesson.get("check_question"):
            st.info(lesson.get("check_question"))
        st.markdown("#### Reflection prompt")
        st.write(lesson.get("reflective_prompt", ""))


def render_learning_module(student: Dict[str, Any]) -> None:
    copy = student_workspace_copy()
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
    valid_ids = {item["id"] for item in content.LESSONS}
    if selected_id not in valid_ids:
        selected_id = first_incomplete_lesson_id(student["id"])
    lesson = content.lesson_by_id(selected_id, i18n.current_lang(st))
    record_lesson_entry(student["id"], selected_id)
    db.log_event(student["id"], "student", "open_module", selected_id)

    render_v66_stage_header(student, lesson, completed)

    open_map = bool(st.session_state.pop("v66_open_map", False))
    with st.expander(f"{copy['course_map']} · {copy['course_map_help']}", expanded=open_map):
        render_learning_path_cards(student, selected_id, recommended_set, completed)

    learning_col, coach_col = st.columns([3, 2], gap="large")
    with learning_col:
        st.markdown("<span class='v66-learning-marker v68-learning-marker'></span>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(
                f"<div class='v66-panel-heading' dir='{i18n.direction(i18n.current_lang(st))}'><span>01</span><div><h3>{escape(copy['learn_panel'])}</h3><p>{escape(lesson.get('objective',''))}</p></div></div>",
                unsafe_allow_html=True,
            )
            render_v66_lesson_content(student, lesson)

    with coach_col:
        st.markdown("<span class='v66-coach-marker v68-coach-marker'></span>", unsafe_allow_html=True)
        with st.container(border=True):
            render_v66_ai_coach(student, lesson)

    st.markdown("<span class='v66-reflection-marker v68-reflection-marker'></span>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(f"### {copy['reflection']}")
        st.info(lesson.get("reflective_prompt", ""))
        reflection_default = ""
        if not progress.empty:
            row = progress[progress["lesson_id"] == lesson["id"]]
            if not row.empty:
                reflection_default = str(row["reflection_text"].iloc[0] or "")
        with st.form(f"v66_reflection_{lesson['id']}"):
            reflection = st.text_area(copy["reflection_ph"], value=reflection_default, height=120)
            submitted = st.form_submit_button(copy["save_complete"], type="primary", use_container_width=True)
        if submitted:
            if len(reflection.strip()) < 20:
                st.error(copy["min_reflection"])
            else:
                db.save_lesson_progress(student["id"], lesson["id"], reflection, completed=True)
                db.log_event(student["id"], "student", "lesson_completed", lesson["id"])
                ids = [item["id"] for item in content.LESSONS]
                idx = ids.index(lesson["id"])
                if idx + 1 < len(ids):
                    st.session_state.current_lesson_id = ids[idx + 1]
                st.success(copy["saved"])
                st.rerun()

    ids = [item["id"] for item in content.LESSONS]
    idx = ids.index(lesson["id"])
    previous_col, map_col, next_col = st.columns(3)
    if previous_col.button(f"← {copy['previous']}", use_container_width=True, disabled=idx == 0):
        set_current_lesson(student["id"], ids[idx - 1]); st.rerun()
    if map_col.button(copy["review"], use_container_width=True):
        st.session_state["v66_open_map"] = True
        st.rerun()
    if next_col.button(f"{copy['next']} →", type="primary", use_container_width=True, disabled=idx >= len(ids) - 1):
        set_current_lesson(student["id"], ids[idx + 1]); st.rerun()

    if learning_path_ready_for_posttest(student["id"]) and ai_requirement_met(student):
        st.success("Learning path requirements are complete. You may continue to the post-test when ready.")
        if st.button("Go to post-test", type="primary", use_container_width=True):
            set_student_page("Post-test")

def render_ai_tutor_lab(student: Dict[str, Any]) -> None:
    if not ai_features_available(student):
        hero("AI Tutor Lab", "This area is intentionally hidden for the control group.")
        st.info("You are in the control learning path. Continue with lessons, simulators, reflections, and the post-test without AI support.")
        if st.button("Return to learning module", type="primary"):
            set_student_page("Learning Module")
        return
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
    current_lesson = content.lesson_by_id(current_lesson_id, i18n.current_lang(st))
    concepts = sorted({c for lesson in content.LESSONS for c in lesson["concepts"]})
    default_concept = current_lesson["concepts"][0] if current_lesson.get("concepts") else concepts[0]
    default_index = concepts.index(default_concept) if default_concept in concepts else 0

    c1, c2, c3 = st.columns([1.15, 1, 1])
    with c1:
        task = st.selectbox(
            "Tutor task",
            ["Explain a concept", "Generate a practice exercise", "Check my explanation", "Debug or interpret Qiskit code"],
            format_func=lambda value: i18n.tr(value),
        )
    with c2:
        concept = st.selectbox("Concept focus", concepts, index=default_index, format_func=lambda value: i18n.concept_label(value, i18n.current_lang(st)))
    with c3:
        tutor_language = st.selectbox(
            "Response language",
            ["Auto-detect", "English", "Arabic", "French"],
            index={"en": 1, "ar": 2, "fr": 3}[i18n.current_lang(st)],
            format_func=lambda value: i18n.tr(value),
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
        set_student_page("Learning Module")

    chat_key = f"ai_chat_history_{student['id']}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    quick_prompts = {
        learning_ui_copy()["simplify"]: f"I am confused about {concept}. Explain it simply, then ask me one question to check my understanding.",
        learning_ui_copy()["hint"]: f"Give me one short beginner exercise about {concept}. Do not give the full solution first.",
        learning_ui_copy()["quiz"]: f"Here is my explanation of {concept}: ... Please tell me what is correct and what I should improve.",
        learning_ui_copy()["qiskit"]: "Here is my Qiskit code:\n\n# paste code here\n\nPlease help me interpret it or find the mistake without giving a long answer.",
    }

    st.markdown(f"#### {learning_ui_copy()['quick']}")
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

    # Keep the composer inline with the conversation. A root-level st.chat_input
    # is pinned to the viewport by Streamlit and can cover the page hero or tools
    # while the learner scrolls. The bordered form below is stable on desktop,
    # tablet, and mobile, and preserves a clear send action.
    manual_prompt = ""
    send_manual = False
    with st.container(border=True, key="v681_chat_composer"):
        st.markdown("#### Ask the AI Coach")
        st.caption("Write your own attempt, question, or small Qiskit snippet. The coach will guide your reasoning rather than replace it.")
        with st.form("v681_chat_composer_form", clear_on_submit=True):
            manual_prompt = st.text_area(
                "Message to the AI Coach",
                placeholder="Ask about the current module, a concept, or a Qiskit code snippet...",
                height=112,
                label_visibility="collapsed",
            )
            send_manual = st.form_submit_button("Send to AI Coach", type="primary", use_container_width=True)

    prompt = None
    if send_draft:
        prompt = st.session_state.get("pending_chat_prompt", "")
        st.session_state.pending_chat_prompt = ""
    elif send_manual:
        prompt = manual_prompt

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
        for key, label in content.survey_items_for(i18n.current_lang(st)):
            responses[key] = st.slider(label, 1, 5, 3, key=f"survey_{key}")
        open_feedback: Dict[str, str] = {}
        st.markdown("### Open-ended feedback")
        for key, label in content.open_ended_items_for(i18n.current_lang(st)):
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


def evaluator_ui() -> Dict[str, Any]:
    """Localized copy for the evaluator/research workspace.

    Internal route names remain stable in English while all visible copy follows
    the selected UI language. This avoids route/database changes and makes the
    research workspace consistent with the learner experience.
    """
    lang = i18n.current_lang(st)
    common = {
        "ar": {
            "dir": "rtl", "workspace": "فضاء المقيّم والباحث", "workspace_sub": "مراقبة التقدم، جودة دعم الذكاء الاصطناعي، والبيانات البحثية.",
            "overview_group": "نظرة عامة", "participants_group": "المشاركون", "ai_group": "الذكاء الاصطناعي والجودة", "data_group": "البيانات والتصدير",
            "dashboard_title": "لوحة المقيّم والباحث", "dashboard_sub": "نظرة موحدة على تقدم المتعلمين، نتائج التعلم، استخدام الذكاء الاصطناعي وجودة استجاباته.",
            "filters": "مرشحات التحليل", "group": "مجموعة الدراسة", "level": "المستوى الأكاديمي", "language": "لغة الواجهة", "completion": "حالة الاكتمال",
            "all": "الكل", "complete": "حالة مكتملة", "incomplete": "غير مكتملة", "reset": "إعادة ضبط المرشحات",
            "students": "المتعلمون", "complete_cases": "الحالات المكتملة", "paired_tests": "اختبارات مزدوجة", "mean_gain": "متوسط التحسن", "ai_logs": "تفاعلات الذكاء الاصطناعي", "lpqs": "متوسط LPQS",
            "registered_note": "الحسابات المسجلة ضمن المرشحات الحالية", "complete_note": "موافقة + قبلي + تعلم + AI + بعدي + استبيان", "paired_note": "متعلمين لديهم اختبار قبلي وبعدي", "gain_note": "فرق الدرجة البعدية عن القبلية", "ai_note": "إجمالي التفاعلات المسجلة", "lpqs_note": "متوسط التقييم التربوي للاستجابات",
            "overview": "نظرة عامة", "learning": "نتائج التعلم", "ai_usage": "استخدام الذكاء الاصطناعي", "quality_system": "الجودة وجاهزية النظام",
            "workflow": "مسار إكمال الدراسة", "workflow_sub": "عدد المشاركين الذين وصلوا إلى كل مرحلة من البروتوكول.",
            "stage": "المرحلة", "count": "العدد", "percent": "النسبة", "consent": "الموافقة", "pre": "الاختبار القبلي", "lesson": "نشاط تعليمي", "ai": "تفاعل AI", "post": "الاختبار البعدي", "survey": "الاستبيان",
            "recent": "أحدث المشاركين", "recent_sub": "عرض تشغيلي سريع مع إبقاء التصدير الكامل في صفحة التصدير.", "no_data": "لا توجد بيانات مطابقة للمرشحات الحالية.",
            "quick_actions": "مركز الإجراءات", "quick_actions_sub": "الوصول المباشر إلى أكثر أدوات المقيّم استخدامًا دون النزول أسفل الصفحة.", "open_students": "إدارة المتعلمين", "quick_students_sub": "البحث في الحسابات، إنشاء مشاركين ومراجعة حالة التسجيل.", "open_ai_logs": "مراجعة سجلات AI", "quick_ai_sub": "فحص المطالبات والاستجابات والأخطاء وزمن التنفيذ.", "open_quality": "تقييم الاستجابات", "quick_quality_sub": "تطبيق معايير LPQS السبعة على استجابات المدرّب الذكي.", "open_exports": "فتح التصدير", "quick_exports_sub": "تحضير بيانات مجهولة الهوية أو نسخة إدارية مؤمّنة.",
            "score_summary": "ملخص الدرجات", "mean_pre": "متوسط القبلي", "mean_post": "متوسط البعدي", "normalized": "الحالات المستخدمة", "concepts": "الأداء حسب المفهوم",
            "usage_provider": "الاستخدام حسب النمط والمزوّد", "usage_task": "الاستخدام حسب نوع الدعم", "interaction_health": "صحة التفاعلات", "fallback_rate": "نسبة الاستجابات الاحتياطية", "latency": "متوسط زمن الاستجابة", "usefulness": "متوسط فائدة الاستجابة",
            "quality_summary": "ملخص جودة استجابات الذكاء الاصطناعي", "evaluated": "الاستجابات المقيّمة", "unrated": "المتبقية للتقييم", "provider_status": "حالة مزوّد الذكاء الاصطناعي", "system_status": "جاهزية النظام",
            "available": "متاح", "unavailable": "غير متاح", "database": "قاعدة البيانات", "app_version": "إصدار التطبيق", "model": "النموذج",
            "login_title": "دخول المقيّم", "login_sub": "مساحة محمية لمتابعة المشاركين، تقييم استجابات الذكاء الاصطناعي وتصدير بيانات الدراسة.", "username": "اسم المستخدم", "password": "كلمة المرور", "sign_in": "تسجيل الدخول", "invalid": "بيانات الدخول غير صحيحة.", "signed_in": "تم تسجيل الدخول.",
            "logs_title": "سجلات المدرّب الذكي", "logs_sub": "راجع المطالبات، الاستجابات، النمط، المزوّد، الزمن والأخطاء المسجلة.", "mode": "النمط", "module": "الوحدة", "concept": "المفهوم", "rows": "عدد السجلات", "search_code": "رمز المشارك", "matches": "السجلات المطابقة", "inspect": "فحص تفاعل", "prompt": "مدخل المتعلم", "response": "استجابة الذكاء الاصطناعي", "diagnostic": "التشخيص التقني", "no_logs": "لا توجد تفاعلات مطابقة لهذه المرشحات.",
            "eval_title": "تقييم استجابات الذكاء الاصطناعي", "eval_sub": "قيّم الاستجابات وفق مقياس LPQS ذي المعايير السبعة لإنتاج دليل تربوي قابل للتحليل.", "load": "عدد الاستجابات", "only_unrated": "غير المقيّمة فقط", "only_llm": "استجابات LLM والأخطاء فقط", "candidate": "الاستجابات المرشحة", "select_interaction": "اختر تفاعلًا للتقييم", "rubric": "تقييم الخبير", "rubric_help": "1 = ضعيف أو غير صحيح، 3 = مقبول جزئيًا، 5 = ممتاز ومناسب تربويًا", "comment": "تعليق المقيّم", "save_eval": "حفظ تقييم الاستجابة", "saved": "تم حفظ التقييم.", "current_summary": "ملخص LPQS الحالي", "full_evals": "جميع التقييمات المحفوظة",
            "conceptual_accuracy": "الدقة المفاهيمية", "answer_relevance": "ملاءمة الإجابة", "pedagogical_clarity": "الوضوح التربوي", "scaffolding_quality": "جودة السقالات التعليمية", "qiskit_alignment": "التوافق مع Qiskit", "reflection_support": "دعم التأمل", "personalization": "التخصيص",
            "analytics_title": "تحليلات التعلم والذكاء الاصطناعي", "analytics_sub": "حلّل الدرجات، التقدم، أداء المفاهيم، أنماط دعم AI والفروق بين المجموعات.", "participants_table": "ملخص المشاركين", "group_comparison": "مقارنة مجموعات الدراسة",
            "exports_title": "تصدير البيانات البحثية", "exports_sub": "حضّر بيانات الدراسة الآمنة للتحليل أو نسخة إدارية كاملة للحفظ المؤمّن.", "anon_title": "تصدير بحثي مجهول الهوية", "anon_body": "مناسب للتحليل، الجداول العلمية والمشاركة داخل فريق البحث دون معلومات تعريفية مباشرة.", "full_title": "نسخة إدارية كاملة", "full_body": "تتضمن بيانات الحسابات لأغراض النسخ الاحتياطي الإداري فقط. تحفظ في مكان آمن.", "prepare_anon": "تحضير التصدير المجهول", "prepare_full": "تحضير النسخة الكاملة", "download": "تنزيل الملف المحضّر", "preview": "معاينة مجموعة البيانات", "dataset": "مجموعة البيانات", "preparing": "جارٍ تحضير المصنف...",
            "students_title": "إدارة المتعلمين", "students_sub": "أنشئ حسابات المشاركين، راجع التسجيلات وحالة الوصول، وابحث في القائمة.", "accounts_title": "حسابات التسجيل", "accounts_sub": "راجع معلومات التسجيل وحالة أول دخول واستعداد الحسابات دون إظهار كلمات المرور.", "details_title": "تفاصيل المتعلم", "details_sub": "راجع الاختبارات، التقدم، التأملات، التفاعلات والاستبيان لمشارك واحد.", "select_participant": "اختر مشاركًا", "participant_code": "رمز المشاركة", "academic_level_label": "المستوى الأكاديمي", "active_label": "حالة الحساب", "yes": "نشط", "no": "غير نشط", "pending": "قيد الانتظار", "learning_gain_label": "مكسب التعلم", "percentage_points": "نقطة مئوية",
            "survey_title": "نتائج الاستبيان", "survey_sub": "راجع تقييمات قابلية الاستخدام والتغذية الراجعة المفتوحة.",
        },
        "fr": {
            "dir": "ltr", "workspace": "Espace évaluateur et recherche", "workspace_sub": "Suivi de la progression, qualité de l’IA et données de recherche.",
            "overview_group": "Vue d’ensemble", "participants_group": "Participants", "ai_group": "IA et qualité", "data_group": "Données et export",
            "dashboard_title": "Tableau de bord évaluateur", "dashboard_sub": "Vue unifiée de la progression, des résultats, de l’usage de l’IA et de la qualité pédagogique des réponses.",
            "filters": "Filtres d’analyse", "group": "Groupe d’étude", "level": "Niveau académique", "language": "Langue d’interface", "completion": "État d’achèvement",
            "all": "Tous", "complete": "Cas complet", "incomplete": "Incomplet", "reset": "Réinitialiser les filtres",
            "students": "Apprenants", "complete_cases": "Cas complets", "paired_tests": "Paires pré/post", "mean_gain": "Gain moyen", "ai_logs": "Interactions IA", "lpqs": "LPQS moyen",
            "registered_note": "Comptes correspondant aux filtres", "complete_note": "Consentement + pré + apprentissage + IA + post + enquête", "paired_note": "Apprenants avec pré-test et post-test", "gain_note": "Différence post-test moins pré-test", "ai_note": "Interactions enregistrées", "lpqs_note": "Qualité pédagogique moyenne des réponses",
            "overview": "Vue d’ensemble", "learning": "Résultats d’apprentissage", "ai_usage": "Usage de l’IA", "quality_system": "Qualité et système",
            "workflow": "Parcours d’achèvement", "workflow_sub": "Nombre de participants ayant atteint chaque étape du protocole.",
            "stage": "Étape", "count": "Nombre", "percent": "Pourcentage", "consent": "Consentement", "pre": "Pré-test", "lesson": "Activité d’apprentissage", "ai": "Interaction IA", "post": "Post-test", "survey": "Enquête",
            "recent": "Participants récents", "recent_sub": "Vue opérationnelle rapide; utilisez l’export pour le jeu complet.", "no_data": "Aucune donnée ne correspond aux filtres.",
            "quick_actions": "Centre d’actions", "quick_actions_sub": "Accédez immédiatement aux outils d’évaluation les plus utilisés, sans descendre en bas de page.", "open_students": "Gérer les apprenants", "quick_students_sub": "Rechercher les comptes, créer des participants et vérifier les inscriptions.", "open_ai_logs": "Voir les journaux IA", "quick_ai_sub": "Inspecter les requêtes, réponses, erreurs et temps d’exécution.", "open_quality": "Évaluer les réponses", "quick_quality_sub": "Appliquer les sept critères LPQS aux réponses du coach IA.", "open_exports": "Ouvrir les exports", "quick_exports_sub": "Préparer un jeu anonymisé ou une sauvegarde administrative sécurisée.",
            "score_summary": "Résumé des scores", "mean_pre": "Moyenne pré-test", "mean_post": "Moyenne post-test", "normalized": "Cas analysés", "concepts": "Performance par concept",
            "usage_provider": "Usage par mode et fournisseur", "usage_task": "Usage par type de soutien", "interaction_health": "Santé des interactions", "fallback_rate": "Taux de fallback", "latency": "Latence moyenne", "usefulness": "Utilité moyenne",
            "quality_summary": "Qualité des réponses IA", "evaluated": "Réponses évaluées", "unrated": "Restant à évaluer", "provider_status": "Fournisseur IA", "system_status": "État du système",
            "available": "Disponible", "unavailable": "Indisponible", "database": "Base de données", "app_version": "Version", "model": "Modèle",
            "login_title": "Connexion évaluateur", "login_sub": "Espace protégé pour suivre les participants, évaluer l’IA et exporter les données.", "username": "Nom d’utilisateur", "password": "Mot de passe", "sign_in": "Se connecter", "invalid": "Identifiants invalides.", "signed_in": "Connexion réussie.",
            "logs_title": "Journaux du coach IA", "logs_sub": "Examinez les requêtes, réponses, modes, fournisseurs, latences et erreurs.", "mode": "Mode", "module": "Module", "concept": "Concept", "rows": "Lignes", "search_code": "Code participant", "matches": "Interactions correspondantes", "inspect": "Inspecter une interaction", "prompt": "Entrée apprenant", "response": "Réponse IA", "diagnostic": "Diagnostic technique", "no_logs": "Aucune interaction ne correspond aux filtres.",
            "eval_title": "Évaluation des réponses IA", "eval_sub": "Évaluez les réponses avec les sept critères LPQS pour produire une preuve pédagogique analysable.", "load": "Réponses à charger", "only_unrated": "Non évaluées uniquement", "only_llm": "LLM et erreurs uniquement", "candidate": "Réponses candidates", "select_interaction": "Sélectionner une interaction", "rubric": "Grille d’expertise", "rubric_help": "1 = faible/incorrect, 3 = acceptable/partiel, 5 = excellent et pédagogiquement adapté", "comment": "Commentaire évaluateur", "save_eval": "Enregistrer l’évaluation", "saved": "Évaluation enregistrée.", "current_summary": "Résumé LPQS actuel", "full_evals": "Évaluations enregistrées",
            "conceptual_accuracy": "Exactitude conceptuelle", "answer_relevance": "Pertinence", "pedagogical_clarity": "Clarté pédagogique", "scaffolding_quality": "Qualité de l’étayage", "qiskit_alignment": "Alignement Qiskit", "reflection_support": "Soutien à la réflexion", "personalization": "Personnalisation",
            "analytics_title": "Analytique d’apprentissage et IA", "analytics_sub": "Analysez les scores, la progression, les concepts, les modes de soutien IA et les groupes.", "participants_table": "Résumé des participants", "group_comparison": "Comparaison des groupes",
            "exports_title": "Export des données de recherche", "exports_sub": "Préparez un jeu anonymisé pour l’analyse ou une sauvegarde administrative complète.", "anon_title": "Export de recherche anonymisé", "anon_body": "Adapté à l’analyse et aux tableaux scientifiques sans identifiants directs.", "full_title": "Sauvegarde administrative complète", "full_body": "Inclut les données de compte; à conserver uniquement dans un emplacement sécurisé.", "prepare_anon": "Préparer l’export anonymisé", "prepare_full": "Préparer la sauvegarde complète", "download": "Télécharger le classeur", "preview": "Aperçu du jeu de données", "dataset": "Jeu de données", "preparing": "Préparation du classeur...",
            "students_title": "Gestion des apprenants", "students_sub": "Créez des comptes, examinez les inscriptions et recherchez les participants.", "accounts_title": "Comptes d’inscription", "accounts_sub": "Examinez les métadonnées d’inscription sans exposer les mots de passe.", "details_title": "Détails de l’apprenant", "details_sub": "Consultez les tests, la progression, les réflexions, les interactions et l’enquête.", "select_participant": "Sélectionner un participant", "participant_code": "Code participant", "academic_level_label": "Niveau académique", "active_label": "État du compte", "yes": "Actif", "no": "Inactif", "pending": "En attente", "learning_gain_label": "Gain d’apprentissage", "percentage_points": "points de pourcentage",
            "survey_title": "Résultats de l’enquête", "survey_sub": "Examinez les scores d’utilisabilité et les commentaires ouverts.",
        },
        "en": {
            "dir": "ltr", "workspace": "Evaluator & research workspace", "workspace_sub": "Monitor progress, AI quality, and research data.",
            "overview_group": "Overview", "participants_group": "Participants", "ai_group": "AI & quality", "data_group": "Data & exports",
            "dashboard_title": "Evaluator & Research Dashboard", "dashboard_sub": "A unified view of learner progress, outcomes, AI use, and pedagogical response quality.",
            "filters": "Analysis filters", "group": "Study group", "level": "Academic level", "language": "Interface language", "completion": "Completion status",
            "all": "All", "complete": "Complete case", "incomplete": "Incomplete", "reset": "Reset filters",
            "students": "Learners", "complete_cases": "Complete cases", "paired_tests": "Paired tests", "mean_gain": "Mean gain", "ai_logs": "AI interactions", "lpqs": "Mean LPQS",
            "registered_note": "Accounts matching current filters", "complete_note": "Consent + pre + learning + AI + post + survey", "paired_note": "Learners with both pre- and post-test", "gain_note": "Post-test minus pre-test", "ai_note": "Recorded interactions", "lpqs_note": "Mean pedagogical response quality",
            "overview": "Overview", "learning": "Learning outcomes", "ai_usage": "AI usage", "quality_system": "Quality & system",
            "workflow": "Study completion funnel", "workflow_sub": "Participants who reached each stage of the protocol.",
            "stage": "Stage", "count": "Count", "percent": "Percent", "consent": "Consent", "pre": "Pre-test", "lesson": "Learning activity", "ai": "AI interaction", "post": "Post-test", "survey": "Survey",
            "recent": "Recent participants", "recent_sub": "Operational snapshot; use Exports for the full dataset.", "no_data": "No data match the current filters.",
            "quick_actions": "Action center", "quick_actions_sub": "Jump directly to the evaluator tools used most often, without scrolling to the bottom of the page.", "open_students": "Manage learners", "quick_students_sub": "Search accounts, create participants, and review registration readiness.", "open_ai_logs": "Review AI logs", "quick_ai_sub": "Inspect prompts, responses, errors, and execution latency.", "open_quality": "Evaluate responses", "quick_quality_sub": "Apply the seven LPQS criteria to AI tutor responses.", "open_exports": "Open exports", "quick_exports_sub": "Prepare an anonymized dataset or a secure administrative backup.",
            "score_summary": "Score summary", "mean_pre": "Mean pre-test", "mean_post": "Mean post-test", "normalized": "Cases analyzed", "concepts": "Concept performance",
            "usage_provider": "Usage by mode and provider", "usage_task": "Usage by support type", "interaction_health": "Interaction health", "fallback_rate": "Fallback rate", "latency": "Mean latency", "usefulness": "Mean usefulness",
            "quality_summary": "AI response quality summary", "evaluated": "Evaluated responses", "unrated": "Remaining unrated", "provider_status": "AI provider status", "system_status": "System readiness",
            "available": "Available", "unavailable": "Unavailable", "database": "Database", "app_version": "App version", "model": "Model",
            "login_title": "Evaluator sign in", "login_sub": "Protected workspace for monitoring participants, evaluating AI responses, and exporting study data.", "username": "Evaluator username", "password": "Evaluator password", "sign_in": "Sign in", "invalid": "Invalid evaluator credentials.", "signed_in": "Signed in.",
            "logs_title": "AI Tutor Logs", "logs_sub": "Review prompts, responses, modes, providers, latency, and recorded diagnostics.", "mode": "Mode", "module": "Module", "concept": "Concept", "rows": "Rows", "search_code": "Participant code", "matches": "Matching interactions", "inspect": "Inspect interaction", "prompt": "Learner prompt", "response": "AI response", "diagnostic": "Technical diagnostic", "no_logs": "No interactions match these filters.",
            "eval_title": "AI Response Evaluation", "eval_sub": "Rate responses with the seven LPQS criteria to create analyzable pedagogical evidence.", "load": "Responses to load", "only_unrated": "Only unrated responses", "only_llm": "LLM and LLM-error responses only", "candidate": "Candidate responses", "select_interaction": "Select an interaction", "rubric": "Expert rubric", "rubric_help": "1 = poor/incorrect, 3 = acceptable/partial, 5 = excellent and pedagogically appropriate", "comment": "Evaluator comment", "save_eval": "Save evaluation", "saved": "Evaluation saved.", "current_summary": "Current LPQS summary", "full_evals": "Saved evaluations",
            "conceptual_accuracy": "Conceptual accuracy", "answer_relevance": "Answer relevance", "pedagogical_clarity": "Pedagogical clarity", "scaffolding_quality": "Scaffolding quality", "qiskit_alignment": "Qiskit alignment", "reflection_support": "Reflection support", "personalization": "Personalization",
            "analytics_title": "Learning & AI Analytics", "analytics_sub": "Analyze scores, progress, concepts, AI support modes, and study-group differences.", "participants_table": "Participant summary", "group_comparison": "Study-group comparison",
            "exports_title": "Research Data Exports", "exports_sub": "Prepare a safe anonymized dataset for analysis or a complete administrative backup.", "anon_title": "Anonymized research export", "anon_body": "Suitable for analysis, manuscript tables, and research-team sharing without direct identifiers.", "full_title": "Full administrative backup", "full_body": "Includes account data for secure administrative backup only.", "prepare_anon": "Prepare anonymized export", "prepare_full": "Prepare full backup", "download": "Download prepared workbook", "preview": "Dataset preview", "dataset": "Dataset", "preparing": "Preparing workbook...",
            "students_title": "Learner Management", "students_sub": "Create participant accounts, review registration, and search the learner list.", "accounts_title": "Registration Accounts", "accounts_sub": "Review registration metadata and access readiness without exposing passwords.", "details_title": "Learner Details", "details_sub": "Inspect tests, progress, reflections, interactions, and survey data for one participant.", "select_participant": "Select participant", "participant_code": "Participant code", "academic_level_label": "Academic level", "active_label": "Account status", "yes": "Active", "no": "Inactive", "pending": "Pending", "learning_gain_label": "Learning gain", "percentage_points": "percentage points",
            "survey_title": "Survey Results", "survey_sub": "Review usability ratings and open-ended feedback.",
        },
    }
    return common[lang]


def evaluator_section(title: str, subtitle: str = "") -> None:
    u = evaluator_ui()
    st.markdown(
        f"<section class='v45-section-head' dir='{u['dir']}'><span>3alimnIA Research</span><h3>{escape(title)}</h3><p>{escape(subtitle)}</p></section>",
        unsafe_allow_html=True,
    )


def evaluator_metric_cards(items: List[Tuple[str, str, str, str]]) -> None:
    """Render evaluator KPIs with consistent multilingual typography."""
    u = evaluator_ui()
    cards = []
    for label, value, note, accent in items:
        cards.append(
            f"<article class='v45-metric {escape(accent)}'><span>{escape(label)}</span><strong>{escape(value)}</strong><small>{escape(note)}</small><i></i></article>"
        )
    st.markdown(f"<div class='v45-metric-grid' dir='{u['dir']}'>{''.join(cards)}</div>", unsafe_allow_html=True)


def evaluator_label_metric(metric: str) -> str:
    u = evaluator_ui()
    return {
        "conceptual_accuracy": u["conceptual_accuracy"],
        "answer_relevance": u["answer_relevance"],
        "pedagogical_clarity": u["pedagogical_clarity"],
        "scaffolding_quality": u["scaffolding_quality"],
        "qiskit_alignment": u["qiskit_alignment"],
        "reflection_support": u["reflection_support"],
        "personalization": u["personalization"],
        "pedagogical_quality_score": "LPQS",
    }.get(str(metric), str(metric).replace("_", " ").title())


def evaluator_filtered_progress() -> pd.DataFrame:
    """Return progress data after evaluator-selected global filters."""
    u = evaluator_ui()
    df = db.progress_summary_df(len(content.LESSONS))
    if df.empty:
        return df
    with st.expander(f"⚙ {u['filters']}", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        groups = sorted([x for x in df.get("study_group", pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if x])
        levels = sorted([x for x in df.get("academic_level", pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if x])
        languages = sorted([x for x in df.get("preferred_language", pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if x])
        selected_groups = c1.multiselect(u["group"], groups, key="v45_filter_groups")
        selected_levels = c2.multiselect(u["level"], levels, key="v45_filter_levels")
        lang_names = {"ar": "العربية", "fr": "Français", "en": "English"}
        selected_languages = c3.multiselect(u["language"], languages, format_func=lambda x: lang_names.get(x, x), key="v45_filter_languages")
        completion_options = [u["all"], u["complete"], u["incomplete"]]
        selected_completion = c4.selectbox(u["completion"], completion_options, key="v45_filter_completion")
        if st.button(u["reset"], key="v45_reset_filters"):
            for key in ["v45_filter_groups", "v45_filter_levels", "v45_filter_languages", "v45_filter_completion"]:
                st.session_state.pop(key, None)
            st.rerun()
    out = df.copy()
    if selected_groups and "study_group" in out:
        out = out[out["study_group"].astype(str).isin(selected_groups)]
    if selected_levels and "academic_level" in out:
        out = out[out["academic_level"].astype(str).isin(selected_levels)]
    if selected_languages and "preferred_language" in out:
        out = out[out["preferred_language"].astype(str).isin(selected_languages)]
    if selected_completion == u["complete"] and "is_complete_case" in out:
        out = out[out["is_complete_case"].astype(bool)]
    elif selected_completion == u["incomplete"] and "is_complete_case" in out:
        out = out[~out["is_complete_case"].astype(bool)]
    return out

def render_evaluator_app() -> None:
    if not st.session_state.evaluator_logged_in:
        render_evaluator_login()
        return
    page = st.session_state.evaluator_page

    # V12.2: keep evaluator routing synchronized with the visible left menu.
    # A previous cleanup renamed menu labels but left the old route names here,
    # which made AI logs / response evaluation / AI metrics / exports appear blank.
    if page == "Evaluator Dashboard":
        render_evaluator_dashboard()
    elif page == "Study Protocol":
        render_study_protocol()
    elif page == "Students":
        render_students_admin()
    elif page == "Registration Accounts":
        render_registration_accounts()
    elif page == "Student Details":
        render_student_details()
    elif page == "AI Tutor Logs":
        render_feedback_logs()
    elif page == "AI Response Evaluation":
        render_llm_performance_evaluation()
    elif page == "AI Metrics":
        render_learning_analytics()
    elif page == "Exports":
        render_results_export()
    # Backward-compatible aliases for older bookmarked/internal pages.
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
    else:
        st.warning(f"Unknown evaluator page: {page}. Returning to dashboard.")
        set_evaluator_page("Evaluator Dashboard")


def render_evaluator_login() -> None:
    u = evaluator_ui()
    hero(u["login_title"], u["login_sub"], localized=True)
    st.markdown(f"<div class='v45-login-note' dir='{u['dir']}'><b>3alimnIA Research</b><span>{escape(u['workspace_sub'])}</span></div>", unsafe_allow_html=True)
    if secret("ADMIN_PASSWORD", "admin123") == "admin123" and not secret("EVALUATOR_PASSWORD_HASH", ""):
        st.warning(i18n.tr("Default evaluator password is still active. Change ADMIN_PASSWORD or use EVALUATOR_PASSWORD_HASH before cloud deployment."))
    with st.form("eval_login"):
        username = st.text_input(u["username"], value=secret("EVALUATOR_USERNAME", "evaluator"))
        password = st.text_input(u["password"], type="password")
        submitted = st.form_submit_button(u["sign_in"], type="primary", use_container_width=True)
    if submitted:
        if evaluator_password_is_valid(username, password):
            db.log_event(None, "evaluator", "sign_in", f"Evaluator username: {username.strip()}")
            st.session_state.evaluator_logged_in = True
            st.success(u["signed_in"])
            router.queue(router.route_key("evaluator", "Evaluator Dashboard"))
            st.rerun()
        else:
            st.error(u["invalid"])


def _safe_count(df: pd.DataFrame) -> int:
    return int(len(df)) if isinstance(df, pd.DataFrame) and not df.empty else 0


def consent_audit_table() -> pd.DataFrame:
    """Build an evaluator-facing audit table without exposing more than needed."""
    students = db.students_df()
    progress = db.progress_summary_df(len(content.LESSONS))
    if students.empty:
        return pd.DataFrame()
    audit = students.copy()
    cols = ["id", "participant_code", "full_name", "email", "institution", "academic_level", "study_group", "created_at", "last_login_at", "is_active"]
    audit = audit[[c for c in cols if c in audit.columns]]
    if not progress.empty:
        keep = ["student_id", "consent_done", "pre_done", "completed_lessons", "ai_interactions", "post_done", "survey_done", "is_complete_case", "complete_case_missing", "progress_percent"]
        progress_small = progress[[c for c in keep if c in progress.columns]].copy()
        audit = audit.merge(progress_small, left_on="id", right_on="student_id", how="left")
    for c in ["consent_done", "pre_done", "completed_lessons", "ai_interactions", "post_done", "survey_done", "is_complete_case"]:
        if c in audit.columns:
            audit[c] = audit[c].fillna(0).astype(int)
    if "progress_percent" in audit.columns:
        audit["progress_percent"] = pd.to_numeric(audit["progress_percent"], errors="coerce").fillna(0).round(1)
    if "complete_case_missing" in audit.columns:
        audit["complete_case_missing"] = audit["complete_case_missing"].fillna("not_started")
    return audit



def _content_collection_size(*names: str) -> int:
    """Return the size of the first available content collection.

    Older platform revisions used *_QUESTIONS names while the current content
    module exposes PRE_TEST and POST_TEST. Keeping a small compatibility helper
    prevents evaluator pages from failing when one naming convention changes.
    """
    for name in names:
        value = getattr(content, name, None)
        if value is not None:
            try:
                return len(value)
            except TypeError:
                continue
    return 0


def _study_protocol_copy() -> Dict[str, Any]:
    lang = i18n.current_lang(st)
    copies: Dict[str, Dict[str, Any]] = {
        "ar": {
            "dir": "rtl",
            "title": "بروتوكول الدراسة",
            "subtitle": "قائمة تشغيلية لإدارة تجربة 3alimnIA بوصفها دراسة تعليمية مضبوطة.",
            "info": "لا تغيّر هذه الصفحة قاعدة البيانات. إنها توثّق تصميم الدراسة النشط، وتتحقق من الموافقة وجاهزية سير العمل، وتجهّز أدلة البروتوكول للمقيّم.",
            "registered": "المتعلمون المسجلون",
            "consent": "الموافقات المؤكدة",
            "complete": "الحالات المكتملة",
            "design": "تصميم الدراسة",
            "design_control": "ضابطة / تجريبية",
            "design_single": "دراسة استطلاعية أحادية المجموعة",
            "config_title": "إعدادات الدراسة الحالية",
            "setting": "الإعداد",
            "value": "القيمة",
            "config_rows": [
                ("إصدار التطبيق", "app_version"),
                ("المجموعة الضابطة مفعلة", "control_enabled"),
                ("سير العمل الافتراضي", "workflow"),
                ("عدد أسئلة الاختبار القبلي", "pre_items"),
                ("عدد أسئلة الاختبار البعدي", "post_items"),
                ("عدد الوحدات التعليمية", "modules"),
                ("مزوّد الذكاء الاصطناعي", "provider"),
                ("منشئ المفاهيم", "concept_builder"),
                ("تسجيل بيانات الذكاء الاصطناعي", "ai_logging"),
            ],
            "enabled": "مفعّل",
            "disabled": "غير مفعّل",
            "workflow": "الموافقة ← الاختبار القبلي ← 6 وحدات تعليمية ← الاختبار البعدي ← الاستبيان",
            "concept_builder": "متاح للمجموعة التجريبية أو الدراسة الأحادية، ويُخفى عن المجموعة الضابطة عند تفعيل وضع الضبط.",
            "ai_logging": "تُسجَّل المهمة والنمط والمزوّد وزمن الاستجابة وتقييم الفائدة وتوقيت الطلب.",
            "safeguards_title": "ضوابط سير العمل البحثي",
            "safeguard": "الضابط",
            "status": "الحالة",
            "evidence": "الدليل",
            "implemented": "مطبّق",
            "conditional": "مشروط",
            "safeguards": [
                ("بوابة الموافقة قبل أنشطة التعلم", "implemented", "صفحة إشعار البحث وجدول consent_records"),
                ("الاختبار القبلي قبل الوصول إلى الدروس", "implemented", "يقفل تنقل المتعلم الوحدات حتى إتمام الاختبار القبلي"),
                ("طلاب المجموعة الضابطة لا يتلقون دعم الذكاء الاصطناعي", "conditional", "يُطبّق فقط عند ENABLE_CONTROL_GROUP=true"),
                ("الاختبار البعدي بعد المسار التعليمي", "implemented", "يُفتح بعد إكمال أنشطة التعلم المطلوبة"),
                ("تصدير مجهول الهوية للتحليل", "implemented", "تجهّز صفحة التصدير مصنفًا مجهول الهوية"),
                ("مراجعة جودة استجابات الذكاء الاصطناعي", "implemented", "مقياس تقييم المقيّم لاستجابات الذكاء الاصطناعي"),
            ],
            "audit_title": "مراجعة الموافقة والاكتمال",
            "no_participants": "لم يُسجَّل أي مشارك بعد.",
            "missing_consent": "مشارك/مشاركون بلا موافقة مسجلة. يجب عدم إدراجهم في التحليل إلى أن تُحل الحالة.",
            "audit_columns": {
                "participant_code": "رمز المشارك", "full_name": "الاسم", "study_group": "مجموعة الدراسة",
                "consent_done": "الموافقة", "pre_done": "القبلي", "completed_lessons": "الوحدات المكتملة",
                "ai_interactions": "تفاعلات AI", "post_done": "البعدي", "survey_done": "الاستبيان",
                "is_complete_case": "حالة مكتملة", "complete_case_missing": "العناصر الناقصة", "progress_percent": "نسبة التقدم",
            },
            "download_title": "تنزيل أدلة البروتوكول",
            "download_button": "تنزيل مصنف بروتوكول الدراسة",
        },
        "fr": {
            "dir": "ltr",
            "title": "Protocole d’étude",
            "subtitle": "Liste opérationnelle pour conduire le pilote 3alimnIA comme étude éducative contrôlée.",
            "info": "Cette page ne modifie pas la base de données. Elle documente le plan d’étude actif, vérifie le consentement et la préparation du parcours, puis prépare les preuves du protocole pour l’évaluateur.",
            "registered": "Apprenants inscrits",
            "consent": "Consentements confirmés",
            "complete": "Cas complets",
            "design": "Plan d’étude",
            "design_control": "Contrôle / expérimental",
            "design_single": "Pilote à groupe unique",
            "config_title": "Configuration active de l’étude",
            "setting": "Paramètre",
            "value": "Valeur",
            "config_rows": [
                ("Version de l’application", "app_version"),
                ("Groupe contrôle activé", "control_enabled"),
                ("Parcours par défaut", "workflow"),
                ("Questions du pré-test", "pre_items"),
                ("Questions du post-test", "post_items"),
                ("Modules d’apprentissage", "modules"),
                ("Fournisseur IA", "provider"),
                ("Concept Builder", "concept_builder"),
                ("Journalisation des données IA", "ai_logging"),
            ],
            "enabled": "Activé",
            "disabled": "Désactivé",
            "workflow": "Consentement → Pré-test → 6 modules → Post-test → Enquête",
            "concept_builder": "Disponible pour les apprenants expérimentaux ou à groupe unique; masqué aux contrôles lorsque le mode contrôle est activé.",
            "ai_logging": "La tâche, le mode, le fournisseur, la latence, l’utilité et l’heure de la requête sont journalisés.",
            "safeguards_title": "Garanties du parcours de recherche",
            "safeguard": "Garantie",
            "status": "État",
            "evidence": "Preuve",
            "implemented": "Implémenté",
            "conditional": "Conditionnel",
            "safeguards": [
                ("Consentement avant les activités d’apprentissage", "implemented", "Page Notice de recherche et table consent_records"),
                ("Pré-test avant l’accès aux leçons", "implemented", "La navigation verrouille les modules jusqu’à la fin du pré-test"),
                ("Aucun soutien IA pour le groupe contrôle", "conditional", "Actif uniquement lorsque ENABLE_CONTROL_GROUP=true"),
                ("Post-test après le parcours d’apprentissage", "implemented", "Débloqué après les activités requises"),
                ("Export anonymisé pour l’analyse", "implemented", "La page Export prépare un classeur anonymisé"),
                ("Révision de la qualité des réponses IA", "implemented", "Grille d’évaluation des réponses IA"),
            ],
            "audit_title": "Audit du consentement et de l’achèvement",
            "no_participants": "Aucun participant n’est encore inscrit.",
            "missing_consent": "participant(s) sans consentement enregistré. Ne pas les inclure dans l’analyse avant résolution.",
            "audit_columns": {
                "participant_code": "Code participant", "full_name": "Nom", "study_group": "Groupe d’étude",
                "consent_done": "Consentement", "pre_done": "Pré-test", "completed_lessons": "Modules terminés",
                "ai_interactions": "Interactions IA", "post_done": "Post-test", "survey_done": "Enquête",
                "is_complete_case": "Cas complet", "complete_case_missing": "Éléments manquants", "progress_percent": "Progression (%)",
            },
            "download_title": "Télécharger les preuves du protocole",
            "download_button": "Télécharger le classeur du protocole",
        },
        "en": {
            "dir": "ltr",
            "title": "Study Protocol",
            "subtitle": "Operational checklist for running the 3alimnIA pilot as a controlled educational study.",
            "info": "This page does not change the database. It documents the active study design, checks consent and workflow readiness, and prepares protocol evidence for the evaluator.",
            "registered": "Registered students",
            "consent": "Consent confirmed",
            "complete": "Complete cases",
            "design": "Study design",
            "design_control": "Control / experimental",
            "design_single": "Single-arm pilot",
            "config_title": "Active study configuration",
            "setting": "Setting",
            "value": "Value",
            "config_rows": [
                ("App version", "app_version"),
                ("Control group enabled", "control_enabled"),
                ("Default workflow", "workflow"),
                ("Pre-test items", "pre_items"),
                ("Post-test items", "post_items"),
                ("Learning modules", "modules"),
                ("AI provider", "provider"),
                ("Concept Builder", "concept_builder"),
                ("AI data logging", "ai_logging"),
            ],
            "enabled": "Enabled",
            "disabled": "Disabled",
            "workflow": "Consent → Pre-test → 6 learning modules → Post-test → Survey",
            "concept_builder": "Enabled for experimental/single-arm students; hidden for control students when control mode is enabled.",
            "ai_logging": "AI task, mode, provider, latency, usefulness rating, and request timing are logged.",
            "safeguards_title": "Research workflow safeguards",
            "safeguard": "Safeguard",
            "status": "Status",
            "evidence": "Evidence",
            "implemented": "Implemented",
            "conditional": "Conditional",
            "safeguards": [
                ("Consent gate before learning tasks", "implemented", "Research Notice page and consent_records table"),
                ("Pre-test before access to lessons", "implemented", "Student navigation locks learning modules until pre-test is complete"),
                ("Control students do not receive AI support", "conditional", "Active only when ENABLE_CONTROL_GROUP=true"),
                ("Post-test after learning path", "implemented", "Post-test unlocks after required learning activities"),
                ("Anonymized export for analysis", "implemented", "Exports page prepares anonymized workbook"),
                ("AI response quality review", "implemented", "Evaluator rubric for AI responses"),
            ],
            "audit_title": "Consent and completion audit",
            "no_participants": "No participants have been registered yet.",
            "missing_consent": "participant(s) have no recorded consent. They should not be included in analysis until resolved.",
            "audit_columns": {
                "participant_code": "Participant code", "full_name": "Full name", "study_group": "Study group",
                "consent_done": "Consent", "pre_done": "Pre-test", "completed_lessons": "Completed lessons",
                "ai_interactions": "AI interactions", "post_done": "Post-test", "survey_done": "Survey",
                "is_complete_case": "Complete case", "complete_case_missing": "Missing items", "progress_percent": "Progress (%)",
            },
            "download_title": "Download protocol evidence",
            "download_button": "Download study protocol workbook",
        },
    }
    return copies.get(lang, copies["en"])


def render_study_protocol() -> None:
    copy = _study_protocol_copy()
    hero(copy["title"], copy["subtitle"], localized=True)
    st.info(copy["info"])

    progress = db.progress_summary_df(len(content.LESSONS))
    students = db.students_df()
    consent_audit = consent_audit_table()
    control_enabled = control_group_enabled()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(copy["registered"], _safe_count(students))
    c2.metric(copy["consent"], int(progress["consent_done"].sum()) if not progress.empty and "consent_done" in progress else 0)
    c3.metric(copy["complete"], int(progress["is_complete_case"].sum()) if not progress.empty and "is_complete_case" in progress else 0)
    c4.metric(copy["design"], copy["design_control"] if control_enabled else copy["design_single"])

    st.markdown(f"### {copy['config_title']}")
    config_values = {
        "app_version": getattr(db, "APP_VERSION", "unknown"),
        "control_enabled": copy["enabled"] if control_enabled else copy["disabled"],
        "workflow": copy["workflow"],
        "pre_items": str(_content_collection_size("PRE_TEST", "PRE_TEST_QUESTIONS")),
        "post_items": str(_content_collection_size("POST_TEST", "POST_TEST_QUESTIONS")),
        "modules": str(len(content.LESSONS)),
        "provider": secret("LLM_PROVIDER", "local") or "local",
        "concept_builder": copy["concept_builder"],
        "ai_logging": copy["ai_logging"],
    }
    config_rows = [
        {copy["setting"]: label, copy["value"]: config_values[key]}
        for label, key in copy["config_rows"]
    ]
    config_df = pd.DataFrame(config_rows)
    st.dataframe(config_df, use_container_width=True, hide_index=True)

    st.markdown(f"### {copy['safeguards_title']}")
    checklist_rows = []
    for safeguard, status_key, evidence in copy["safeguards"]:
        checklist_rows.append({
            copy["safeguard"]: safeguard,
            copy["status"]: copy[status_key],
            copy["evidence"]: evidence,
        })
    checklist = pd.DataFrame(checklist_rows)
    st.dataframe(checklist, use_container_width=True, hide_index=True)

    st.markdown(f"### {copy['audit_title']}")
    if consent_audit.empty:
        st.info(copy["no_participants"])
    else:
        show_cols = [
            "participant_code", "full_name", "study_group", "consent_done", "pre_done", "completed_lessons",
            "ai_interactions", "post_done", "survey_done", "is_complete_case", "complete_case_missing", "progress_percent"
        ]
        audit_display = consent_audit[[c for c in show_cols if c in consent_audit.columns]].copy()
        audit_display = audit_display.rename(columns=copy["audit_columns"])
        st.dataframe(audit_display, use_container_width=True, hide_index=True)
        missing_consent = consent_audit[consent_audit.get("consent_done", 0).eq(0)] if "consent_done" in consent_audit else pd.DataFrame()
        if not missing_consent.empty:
            st.warning(f"{len(missing_consent)} {copy['missing_consent']}")

    st.markdown(f"### {copy['download_title']}")
    # Keep stable English sheet names for research scripts while localizing the UI.
    protocol_tables = {
        "study_configuration": pd.DataFrame([
            {"setting": label, "value": config_values[key]}
            for label, key in copy["config_rows"]
        ]),
        "workflow_safeguards": pd.DataFrame([
            {"safeguard": safeguard, "status": copy[status_key], "evidence": evidence}
            for safeguard, status_key, evidence in copy["safeguards"]
        ]),
        "consent_completion_audit": consent_audit,
    }
    st.download_button(
        copy["download_button"],
        data=to_excel_bytes(protocol_tables),
        file_name="qai_study_protocol_evidence.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )



def render_evaluator_quick_actions(u: Dict[str, Any]) -> None:
    """Render a compact command center above evaluator analytics.

    The dashboard previously placed operational shortcuts beneath the participant
    table, forcing laptop users to scroll past a long dataset before reaching
    common tasks. This command center keeps those routes visible at the top while
    preserving the native sidebar as the complete navigation source.
    """
    actions = [
        ("01", "👥", u["open_students"], u["quick_students_sub"], "Students", "v49_quick_students"),
        ("02", "◈", u["open_ai_logs"], u["quick_ai_sub"], "AI Tutor Logs", "v49_quick_ai"),
        ("03", "✓", u["open_quality"], u["quick_quality_sub"], "AI Response Evaluation", "v49_quick_quality"),
        ("04", "⇩", u["open_exports"], u["quick_exports_sub"], "Exports", "v49_quick_exports"),
    ]
    with st.container(border=True):
        st.markdown("<span class='v49-command-center-marker'></span>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='v49-command-head' dir='{u['dir']}'><div><span>3alimnIA Research</span><h3>{escape(u['quick_actions'])}</h3></div><p>{escape(u['quick_actions_sub'])}</p></div>",
            unsafe_allow_html=True,
        )
        cols = st.columns(4, gap="small")
        for col, (number, icon, title, subtitle, route, key) in zip(cols, actions):
            with col:
                st.markdown(
                    f"<article class='v49-action-card' dir='{u['dir']}'><div class='v49-action-top'><span class='v49-action-icon'>{escape(icon)}</span><small>{escape(number)}</small></div><h4>{escape(title)}</h4><p>{escape(subtitle)}</p></article>",
                    unsafe_allow_html=True,
                )
                if st.button(title, key=key, use_container_width=True):
                    set_evaluator_page(route)

def render_evaluator_dashboard() -> None:
    """Render the evaluator command centre with live study data.

    V6.2 deliberately uses Streamlit-native metrics, tabs, tables, and download
    controls. Plotly is limited to analytical figures and inherits the active
    Streamlit theme, so light/dark mode stays coherent without server-time logic.
    """
    u = evaluator_ui()
    lang = i18n.current_lang(st)
    copy = {
        "ar": {
            "title": "لوحة ذكاء التعلّم والتقييم",
            "subtitle": "نظرة تنفيذية موحّدة على التقدم، نتائج الاختبارات، استخدام المدرّب التوليدي، وجودة الاستجابات وفق LPQS.",
            "overview": "نظرة عامة",
            "learners": "المتعلمون",
            "ai_quality": "الذكاء الاصطناعي وLPQS",
            "exports": "التصدير البحثي",
            "registered": "المتعلمون المسجلون",
            "completion": "متوسط إتمام المسار",
            "gain": "متوسط التحسن",
            "ai_interactions": "تفاعلات الذكاء الاصطناعي",
            "complete_cases": "الحالات المكتملة",
            "paired": "اختبارات قبلية/بعدية مكتملة",
            "lpqs": "متوسط LPQS",
            "pre_post": "الاختبار القبلي مقابل البعدي",
            "activity": "نشاط المدرّب التوليدي عبر الزمن",
            "completion_chart": "توزيع تقدم المتعلمين",
            "student_table": "سجل تقدم المتعلمين",
            "filter_level": "المستوى الأكاديمي",
            "all": "الكل",
            "participant": "رمز المشاركة",
            "name": "المتعلم",
            "level": "المستوى",
            "language": "اللغة",
            "progress": "نسبة الإتمام",
            "pre": "الاختبار القبلي",
            "post": "الاختبار البعدي",
            "gain_col": "التحسن",
            "ai_messages": "تفاعلات AI",
            "case_status": "حالة الاكتمال",
            "complete": "مكتملة",
            "incomplete": "غير مكتملة",
            "ai_modes": "أنماط استخدام المدرّب",
            "ai_daily": "التفاعلات اليومية",
            "quality_dimensions": "أبعاد الجودة التربوية",
            "provider_health": "صحة خدمة الذكاء الاصطناعي",
            "fallback": "نسبة الاستجابة الاحتياطية",
            "latency": "متوسط زمن الاستجابة",
            "usefulness": "فائدة الرد حسب المتعلم",
            "download_title": "بيانات جاهزة للتحليل",
            "download_body": "نزّل نسخة مجهولة الهوية للتحليل الإحصائي، أو انتقل إلى مركز التصدير الكامل لإعداد ملفات البحث والنسخ الإدارية.",
            "download_csv": "تنزيل ملخص المشاركين CSV",
            "download_xlsx": "تنزيل الحزمة البحثية Excel",
            "open_export": "فتح مركز التصدير الكامل",
            "privacy": "لا تتضمن الحزمة البحثية الأسماء أو البريد الإلكتروني أو المؤسسة أو معرّفات قاعدة البيانات الداخلية.",
            "no_data": "لا توجد بيانات كافية ضمن المرشحات الحالية.",
            "reference": "الخط المرجعي يعني عدم وجود تحسن.",
            "date": "التاريخ",
            "interactions": "التفاعلات",
            "active_learners": "المتعلمون النشطون",
        },
        "fr": {
            "title": "Tableau de pilotage de l’apprentissage et de l’évaluation",
            "subtitle": "Vue unifiée de la progression, des résultats, de l’usage du coach génératif et de la qualité LPQS.",
            "overview": "Vue d’ensemble",
            "learners": "Apprenants",
            "ai_quality": "IA et LPQS",
            "exports": "Export recherche",
            "registered": "Apprenants inscrits",
            "completion": "Progression moyenne",
            "gain": "Gain moyen",
            "ai_interactions": "Interactions IA",
            "complete_cases": "Cas complets",
            "paired": "Pré/post-tests appariés",
            "lpqs": "LPQS moyen",
            "pre_post": "Pré-test versus post-test",
            "activity": "Activité du coach génératif dans le temps",
            "completion_chart": "Distribution de la progression",
            "student_table": "Suivi détaillé des apprenants",
            "filter_level": "Niveau académique",
            "all": "Tous",
            "participant": "Code participant",
            "name": "Apprenant",
            "level": "Niveau",
            "language": "Langue",
            "progress": "Progression",
            "pre": "Pré-test",
            "post": "Post-test",
            "gain_col": "Gain",
            "ai_messages": "Interactions IA",
            "case_status": "Statut",
            "complete": "Complet",
            "incomplete": "Incomplet",
            "ai_modes": "Modes d’utilisation du coach",
            "ai_daily": "Interactions quotidiennes",
            "quality_dimensions": "Dimensions de qualité pédagogique",
            "provider_health": "Santé du service IA",
            "fallback": "Taux de secours",
            "latency": "Latence moyenne",
            "usefulness": "Utilité perçue",
            "download_title": "Données prêtes pour l’analyse",
            "download_body": "Téléchargez une version anonymisée ou ouvrez le centre d’export complet pour les fichiers de recherche et les sauvegardes administratives.",
            "download_csv": "Télécharger le résumé CSV",
            "download_xlsx": "Télécharger le classeur de recherche",
            "open_export": "Ouvrir le centre d’export",
            "privacy": "L’export recherche exclut les noms, e-mails, établissements et identifiants internes de la base.",
            "no_data": "Aucune donnée suffisante pour les filtres actuels.",
            "reference": "La diagonale représente l’absence d’amélioration.",
            "date": "Date",
            "interactions": "Interactions",
            "active_learners": "Apprenants actifs",
        },
        "en": {
            "title": "Learning and Evaluation Intelligence Dashboard",
            "subtitle": "A unified operational view of progress, assessment outcomes, generative-coach usage, and LPQS response quality.",
            "overview": "Overview",
            "learners": "Learners",
            "ai_quality": "AI and LPQS",
            "exports": "Research export",
            "registered": "Registered learners",
            "completion": "Average path completion",
            "gain": "Average learning gain",
            "ai_interactions": "AI interactions",
            "complete_cases": "Complete cases",
            "paired": "Paired pre/post tests",
            "lpqs": "Average LPQS",
            "pre_post": "Pre-test versus post-test",
            "activity": "Generative-coach activity over time",
            "completion_chart": "Learner progress distribution",
            "student_table": "Learner progress register",
            "filter_level": "Academic level",
            "all": "All",
            "participant": "Participant code",
            "name": "Learner",
            "level": "Level",
            "language": "Language",
            "progress": "Completion",
            "pre": "Pre-test",
            "post": "Post-test",
            "gain_col": "Gain",
            "ai_messages": "AI interactions",
            "case_status": "Completion status",
            "complete": "Complete",
            "incomplete": "Incomplete",
            "ai_modes": "Coach usage modes",
            "ai_daily": "Daily interactions",
            "quality_dimensions": "Pedagogical quality dimensions",
            "provider_health": "AI service health",
            "fallback": "Fallback rate",
            "latency": "Average latency",
            "usefulness": "Learner-rated usefulness",
            "download_title": "Analysis-ready datasets",
            "download_body": "Download an anonymized study extract or open the complete export centre for research workbooks and administrative backups.",
            "download_csv": "Download participant summary CSV",
            "download_xlsx": "Download research workbook",
            "open_export": "Open full export centre",
            "privacy": "The research export excludes names, email addresses, institutions, and internal database identifiers.",
            "no_data": "There is not enough data for the current filters.",
            "reference": "The diagonal reference line represents no improvement.",
            "date": "Date",
            "interactions": "Interactions",
            "active_learners": "Active learners",
        },
    }[lang]

    hero(copy["title"], copy["subtitle"], localized=True)
    render_evaluator_quick_actions(u)
    df = evaluator_filtered_progress()
    evaluations = db.llm_evaluations_df()
    allowed_codes = set(df["participant_code"].dropna().astype(str).tolist()) if not df.empty and "participant_code" in df else set()
    if allowed_codes and not evaluations.empty and "participant_code" in evaluations:
        evaluations = evaluations[evaluations["participant_code"].astype(str).isin(allowed_codes)].copy()

    logs = db.ai_logs_df(limit=None)
    if allowed_codes and not logs.empty and "participant_code" in logs:
        logs = logs[logs["participant_code"].astype(str).isin(allowed_codes)].copy()

    paired = pd.DataFrame()
    if not df.empty and {"pre_done", "post_done"}.issubset(df.columns):
        paired = df[df["pre_done"].astype(bool) & df["post_done"].astype(bool)].copy()
    gain = pd.to_numeric(paired.get("learning_gain", pd.Series(dtype=float)), errors="coerce").dropna()
    mean_gain = float(gain.mean()) if not gain.empty else None
    total_ai = int(pd.to_numeric(df.get("ai_interactions", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not df.empty else 0
    complete_cases = int(df["is_complete_case"].astype(bool).sum()) if not df.empty and "is_complete_case" in df else 0
    completion = pd.to_numeric(df.get("progress_percent", pd.Series(dtype=float)), errors="coerce").dropna()
    mean_completion = float(completion.mean()) if not completion.empty else None
    lpqs_series = pd.to_numeric(evaluations.get("pedagogical_quality_score", pd.Series(dtype=float)), errors="coerce").dropna()
    mean_lpqs = float(lpqs_series.mean()) if not lpqs_series.empty else None

    st.markdown("<span class='v62-evaluator-marker'></span>", unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4, gap="small")
    k1.metric(copy["registered"], len(df), help=u["registered_note"])
    k2.metric(copy["completion"], f"{mean_completion:.1f}%" if mean_completion is not None else "—")
    k3.metric(copy["gain"], f"{mean_gain:+.1f} pp" if mean_gain is not None else "—", help=u["gain_note"])
    k4.metric(copy["ai_interactions"], total_ai, help=u["ai_note"])

    tab_overview, tab_learners, tab_ai, tab_exports = st.tabs([
        copy["overview"], copy["learners"], copy["ai_quality"], copy["exports"]
    ])

    with tab_overview:
        s1, s2, s3 = st.columns(3, gap="small")
        s1.metric(copy["complete_cases"], complete_cases)
        s2.metric(copy["paired"], len(paired))
        s3.metric(copy["lpqs"], f"{mean_lpqs:.2f}/5" if mean_lpqs is not None else "—")

        chart_left, chart_right = st.columns(2, gap="large")
        with chart_left:
            with st.container(border=True):
                st.markdown(f"### {copy['pre_post']}")
                if paired.empty:
                    st.info(copy["no_data"])
                else:
                    plot_df = paired.copy()
                    plot_df["pre_score"] = pd.to_numeric(plot_df["pre_score"], errors="coerce")
                    plot_df["post_score"] = pd.to_numeric(plot_df["post_score"], errors="coerce")
                    plot_df = plot_df.dropna(subset=["pre_score", "post_score"])
                    color_col = "academic_level" if "academic_level" in plot_df else None
                    fig = px.scatter(
                        plot_df,
                        x="pre_score",
                        y="post_score",
                        color=color_col,
                        hover_name="participant_code" if "participant_code" in plot_df else None,
                        labels={"pre_score": copy["pre"], "post_score": copy["post"], "academic_level": copy["level"]},
                    )
                    fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line=dict(color="#94A3B8", dash="dash", width=1.5))
                    fig.update_xaxes(range=[0, 100], gridcolor="rgba(148,163,184,.18)")
                    fig.update_yaxes(range=[0, 100], gridcolor="rgba(148,163,184,.18)")
                    fig.update_layout(height=360, margin=dict(l=12, r=12, t=16, b=12), legend_title_text="", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, width="stretch", theme="streamlit", key="v62_pre_post")
                    st.caption(copy["reference"])

        with chart_right:
            with st.container(border=True):
                st.markdown(f"### {copy['activity']}")
                if logs.empty or "created_at" not in logs:
                    st.info(copy["no_data"])
                else:
                    activity = logs.copy()
                    activity["created_at"] = pd.to_datetime(activity["created_at"], errors="coerce")
                    activity = activity.dropna(subset=["created_at"])
                    activity["date"] = activity["created_at"].dt.date
                    daily = activity.groupby("date", as_index=False).agg(
                        interactions=("interaction_id", "count"),
                        active_learners=("participant_code", "nunique"),
                    )
                    daily_long = daily.melt(id_vars="date", value_vars=["interactions", "active_learners"], var_name="metric", value_name="value")
                    daily_long["metric"] = daily_long["metric"].map({"interactions": copy["interactions"], "active_learners": copy["active_learners"]})
                    fig = px.line(daily_long, x="date", y="value", color="metric", markers=True, labels={"date": copy["date"], "value": "", "metric": ""})
                    fig.update_layout(height=360, margin=dict(l=12, r=12, t=16, b=12), legend_orientation="h", legend_y=-0.2, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    fig.update_xaxes(gridcolor="rgba(148,163,184,.12)")
                    fig.update_yaxes(gridcolor="rgba(148,163,184,.18)")
                    st.plotly_chart(fig, width="stretch", theme="streamlit", key="v62_activity")

        with st.container(border=True):
            st.markdown(f"### {copy['completion_chart']}")
            if completion.empty:
                st.info(copy["no_data"])
            else:
                hist_df = pd.DataFrame({"progress_percent": completion.clip(0, 100)})
                fig = px.histogram(hist_df, x="progress_percent", nbins=10, labels={"progress_percent": copy["progress"]})
                fig.update_layout(height=280, showlegend=False, margin=dict(l=12, r=12, t=12, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                fig.update_xaxes(range=[0, 100], gridcolor="rgba(148,163,184,.12)")
                fig.update_yaxes(gridcolor="rgba(148,163,184,.18)")
                st.plotly_chart(fig, width="stretch", theme="streamlit", key="v62_completion")

    with tab_learners:
        st.markdown(f"### {copy['student_table']}")
        if df.empty:
            st.info(copy["no_data"])
        else:
            levels = sorted([x for x in df.get("academic_level", pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if x])
            selected_level = st.selectbox(copy["filter_level"], [copy["all"]] + levels, key="v62_level_filter")
            table_df = df.copy()
            if selected_level != copy["all"] and "academic_level" in table_df:
                table_df = table_df[table_df["academic_level"].astype(str).eq(selected_level)]
            table_df["case_status"] = table_df.get("is_complete_case", False).astype(bool).map({True: copy["complete"], False: copy["incomplete"]})
            columns = ["participant_code", "full_name", "academic_level", "preferred_language", "progress_percent", "pre_score", "post_score", "learning_gain", "ai_interactions", "case_status"]
            table_df = table_df[[c for c in columns if c in table_df.columns]].copy()
            table_df = table_df.rename(columns={
                "participant_code": copy["participant"], "full_name": copy["name"], "academic_level": copy["level"],
                "preferred_language": copy["language"], "progress_percent": copy["progress"], "pre_score": copy["pre"],
                "post_score": copy["post"], "learning_gain": copy["gain_col"], "ai_interactions": copy["ai_messages"],
                "case_status": copy["case_status"],
            })
            st.dataframe(
                table_df,
                width="stretch",
                height=440,
                hide_index=True,
                column_config={
                    copy["progress"]: st.column_config.ProgressColumn(copy["progress"], min_value=0, max_value=100, format="%.0f%%"),
                    copy["pre"]: st.column_config.NumberColumn(copy["pre"], format="%.1f%%"),
                    copy["post"]: st.column_config.NumberColumn(copy["post"], format="%.1f%%"),
                    copy["gain_col"]: st.column_config.NumberColumn(copy["gain_col"], format="%+.1f pp"),
                    copy["ai_messages"]: st.column_config.NumberColumn(copy["ai_messages"], format="%d"),
                },
                key="v62_learner_table",
            )

    with tab_ai:
        health_1, health_2, health_3 = st.columns(3, gap="small")
        fallback_rate = None
        mean_latency = None
        mean_usefulness = None
        if not logs.empty:
            fallback = pd.to_numeric(logs.get("is_fallback_used", pd.Series(dtype=float)), errors="coerce").fillna(0)
            fallback_rate = float(fallback.mean() * 100) if len(fallback) else None
            latency = pd.to_numeric(logs.get("latency_ms", pd.Series(dtype=float)), errors="coerce").dropna()
            mean_latency = float(latency.mean()) if not latency.empty else None
            usefulness = pd.to_numeric(logs.get("student_usefulness_rating", pd.Series(dtype=float)), errors="coerce").dropna()
            mean_usefulness = float(usefulness.mean()) if not usefulness.empty else None
        health_1.metric(copy["fallback"], f"{fallback_rate:.1f}%" if fallback_rate is not None else "—")
        health_2.metric(copy["latency"], f"{mean_latency:.0f} ms" if mean_latency is not None else "—")
        health_3.metric(copy["usefulness"], f"{mean_usefulness:.2f}/5" if mean_usefulness is not None else "—")

        ai_left, ai_right = st.columns(2, gap="large")
        with ai_left:
            with st.container(border=True):
                st.markdown(f"### {copy['ai_modes']}")
                if logs.empty or "mode" not in logs:
                    st.info(copy["no_data"])
                else:
                    modes = logs.groupby("mode", dropna=False).size().reset_index(name="interactions").sort_values("interactions", ascending=False)
                    fig = px.bar(modes, x="interactions", y="mode", orientation="h", labels={"interactions": copy["interactions"], "mode": ""})
                    fig.update_layout(height=330, margin=dict(l=12, r=12, t=12, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    fig.update_xaxes(gridcolor="rgba(148,163,184,.18)")
                    st.plotly_chart(fig, width="stretch", theme="streamlit", key="v62_ai_modes")

        with ai_right:
            with st.container(border=True):
                st.markdown(f"### {copy['quality_dimensions']}")
                metric_cols = ["conceptual_accuracy", "answer_relevance", "pedagogical_clarity", "scaffolding_quality", "qiskit_alignment", "reflection_support", "personalization"]
                quality_rows = []
                if not evaluations.empty:
                    for col in metric_cols:
                        if col in evaluations:
                            values = pd.to_numeric(evaluations[col], errors="coerce").dropna()
                            if not values.empty:
                                quality_rows.append({"metric": evaluator_label_metric(col), "score": float(values.mean())})
                if not quality_rows:
                    st.info(copy["no_data"])
                else:
                    quality_df = pd.DataFrame(quality_rows).sort_values("score")
                    fig = px.bar(quality_df, x="score", y="metric", orientation="h", range_x=[0, 5], labels={"score": "LPQS", "metric": ""})
                    fig.update_layout(height=330, margin=dict(l=12, r=12, t=12, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    fig.update_xaxes(gridcolor="rgba(148,163,184,.18)")
                    st.plotly_chart(fig, width="stretch", theme="streamlit", key="v62_lpqs")

    with tab_exports:
        with st.container(border=True):
            st.markdown(f"### {copy['download_title']}")
            st.write(copy["download_body"])
            st.info(copy["privacy"])
            anon_progress = db.anonymize_dataframe(df)
            csv_data = anon_progress.to_csv(index=False).encode("utf-8-sig") if not anon_progress.empty else b""
            research_tables = db.research_export_tables(len(content.LESSONS), anonymized=True)
            workbook = to_excel_bytes(research_tables)
            d1, d2, d3 = st.columns(3, gap="small")
            d1.download_button(copy["download_csv"], data=csv_data, file_name="3alimnia_participant_summary_anonymized.csv", mime="text/csv", width="stretch", disabled=not bool(csv_data))
            d2.download_button(copy["download_xlsx"], data=workbook, file_name="3alimnia_research_export_anonymized.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
            if d3.button(copy["open_export"], width="stretch", key="v62_open_full_export"):
                set_evaluator_page("Exports")

def render_students_admin() -> None:
    u = evaluator_ui()
    hero(u["students_title"], u["students_sub"], localized=True)
    with st.expander(f"+ {i18n.tr('Create participant account as evaluator')}", expanded=False):
        with st.form("evaluator_create_student"):
            c1, c2 = st.columns(2)
            with c1:
                full_name = st.text_input(i18n.tr("Full name"))
                email = st.text_input(i18n.tr("Email"))
                institution = st.text_input(i18n.tr("Institution"))
            with c2:
                academic_level = st.selectbox(i18n.tr("Academic level"), ["Licence", "Master", "PhD", "Other"], key="eval_level")
                preferred_language = st.selectbox(u["language"], ["ar", "fr", "en"], format_func=lambda x: {"ar": "العربية", "fr": "Français", "en": "English"}[x])
                prior_python = st.slider(i18n.tr("Prior Python level"), 0, 3, 1, key="eval_python")
                prior_quantum = st.slider(i18n.tr("Prior quantum knowledge"), 0, 3, 0, key="eval_quantum")
            password = st.text_input(i18n.tr("Initial password"), type="password")
            submitted = st.form_submit_button(i18n.tr("Create participant"), type="primary", use_container_width=True)
        if submitted:
            try:
                assigned_group = "" if control_group_enabled() else "single_arm"
                student = db.create_student(
                    full_name, email, institution, academic_level, prior_python, prior_quantum, password,
                    study_group=assigned_group, preferred_language=preferred_language,
                )
                if control_group_enabled():
                    group = db.assign_study_group(student["id"])
                    student = db.get_student(student["id"]) or student
                    db.log_event(student["id"], "system", "study_group_assigned", json.dumps({"study_group": group, "method": "balanced_alternation"}))
                db.log_event(student["id"], "evaluator", "account_created_by_evaluator", "Evaluator created participant account")
                st.success(f"{student['participant_code']} · {study_group_label(student)}")
            except Exception as exc:
                st.error(f"{i18n.tr('Could not create participant')}: {exc}")

    df = db.students_df()
    if df.empty:
        st.info(u["no_data"])
        return
    evaluator_section(u["participants_table"])
    c1, c2, c3 = st.columns([1.4, 1, 1])
    query = c1.text_input(i18n.tr("Search by participant code, name, email, or institution"), key="v45_student_search")
    groups = sorted(df["study_group"].dropna().astype(str).unique().tolist()) if "study_group" in df else []
    selected_groups = c2.multiselect(u["group"], groups, key="v45_student_groups")
    only_active = c3.checkbox(i18n.tr("Only active accounts"), key="v45_students_active")
    filtered = df.copy()
    if query.strip():
        q = query.strip().lower()
        searchable = (filtered["participant_code"].astype(str)+" "+filtered["full_name"].astype(str)+" "+filtered.get("email","").astype(str)+" "+filtered.get("institution","").astype(str)).str.lower()
        filtered = filtered[searchable.str.contains(q, na=False)]
    if selected_groups:
        filtered = filtered[filtered["study_group"].astype(str).isin(selected_groups)]
    if only_active and "is_active" in filtered:
        filtered = filtered[pd.to_numeric(filtered["is_active"], errors="coerce").fillna(0).eq(1)]
    st.dataframe(filtered, use_container_width=True, hide_index=True)


def render_registration_accounts() -> None:
    u = evaluator_ui()
    hero(u["accounts_title"], u["accounts_sub"], localized=True)
    st.info(i18n.tr("This evaluator view shows registration metadata needed to support the pilot study. It never displays student passwords, password hashes, or password-reset tokens."))
    df = db.students_df()
    if df.empty:
        st.info(u["no_data"])
        return
    accounts = df.copy()
    for col in ["email", "institution", "academic_level", "preferred_language", "created_at", "last_login_at"]:
        if col not in accounts.columns:
            accounts[col] = ""
        accounts[col] = accounts[col].fillna("")
    accounts["is_active"] = pd.to_numeric(accounts.get("is_active", 1), errors="coerce").fillna(1).astype(int)
    accounts["email_missing"] = accounts["email"].astype(str).str.strip().eq("")
    accounts["has_signed_in"] = accounts["last_login_at"].astype(str).str.strip().ne("")
    evaluator_metric_cards([
        (i18n.tr("Registered accounts"), str(len(accounts)), "", "blue"),
        (i18n.tr("Active accounts"), str(int(accounts["is_active"].sum())), "", "cyan"),
        (i18n.tr("Missing email"), str(int(accounts["email_missing"].sum())), "", "gold"),
        (i18n.tr("Signed in at least once"), str(int(accounts["has_signed_in"].sum())), "", "navy"),
    ])
    evaluator_section(u["filters"])
    q = st.text_input(i18n.tr("Search by participant code, name, email, or institution"), key="v45_accounts_search")
    fc1, fc2, fc3 = st.columns(3)
    only_active = fc1.checkbox(i18n.tr("Only active accounts"), value=False)
    only_missing_email = fc2.checkbox(i18n.tr("Only accounts missing email"), value=False)
    only_never_signed = fc3.checkbox(i18n.tr("Only never signed in"), value=False)
    filtered = accounts.copy()
    if q.strip():
        query = q.strip().lower()
        searchable = (filtered["participant_code"].astype(str)+" "+filtered["full_name"].astype(str)+" "+filtered["email"].astype(str)+" "+filtered["institution"].astype(str)).str.lower()
        filtered = filtered[searchable.str.contains(query, na=False)]
    if only_active:
        filtered = filtered[filtered["is_active"].eq(1)]
    if only_missing_email:
        filtered = filtered[filtered["email_missing"]]
    if only_never_signed:
        filtered = filtered[~filtered["has_signed_in"]]
    display_cols = ["participant_code", "full_name", "email", "institution", "academic_level", "preferred_language", "study_group", "created_at", "last_login_at", "is_active"]
    display = filtered[[c for c in display_cols if c in filtered.columns]].copy()
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.download_button(i18n.tr("Download account registration list (CSV)"), data=display.to_csv(index=False).encode("utf-8-sig"), file_name="3alimnia_registration_accounts.csv", mime="text/csv", use_container_width=True)


def render_student_details() -> None:
    u = evaluator_ui()
    hero(u["details_title"], u["details_sub"], localized=True)
    df = db.students_df()
    if df.empty:
        st.info(u["no_data"])
        return
    code = st.selectbox(u["select_participant"], df["participant_code"].tolist(), format_func=lambda c: f"{c} · {df[df['participant_code']==c]['full_name'].iloc[0]}")
    student = db.get_student_by_code(code)
    if not student:
        return
    pre = db.get_test_attempt(student["id"], "pre")
    post = db.get_test_attempt(student["id"], "post")
    progress = db.get_lesson_progress(student["id"])
    logs = db.ai_logs_df(limit=250, participant_code=student["participant_code"])
    lang = i18n.current_lang(st)
    academic_levels = {
        "ar": {"Licence": "ليسانس", "Master": "ماستر", "PhD": "دكتوراه", "Other": "أخرى"},
        "fr": {"Licence": "Licence", "Master": "Master", "PhD": "Doctorat", "Other": "Autre"},
        "en": {"Licence": "Bachelor / Licence", "Master": "Master", "PhD": "PhD", "Other": "Other"},
    }
    raw_level = str(student.get("academic_level") or "—")
    level_value = academic_levels.get(lang, {}).get(raw_level, raw_level)
    active_value = u["yes"] if bool(student.get("is_active", 1)) else u["no"]
    pre_value = f"{pre['score']:.1f}%" if pre else u["pending"]
    post_value = f"{post['score']:.1f}%" if post else u["pending"]
    gain_value = f"{post['score']-pre['score']:.1f} {u['percentage_points']}" if pre and post else "—"
    evaluator_metric_cards([
        (u["participant_code"], str(student["participant_code"]), "", "navy"),
        (u["academic_level_label"], level_value, "", "blue"),
        (u["active_label"], active_value, "", "cyan"),
        (u["pre"], pre_value, "", "blue"),
        (u["post"], post_value, "", "cyan"),
        (u["learning_gain_label"], gain_value, "", "gold"),
    ])
    tab_summary, tab_learning, tab_ai, tab_timeline = st.tabs([u["overview"], u["learning"], u["ai_usage"], i18n.tr("Learning timeline")])
    with tab_summary:
        profile = pd.DataFrame([{
            "participant_code": student.get("participant_code"), "full_name": student.get("full_name"), "email": student.get("email"),
            "institution": student.get("institution"), "academic_level": student.get("academic_level"), "preferred_language": student.get("preferred_language"),
            "study_group": student.get("study_group"), "last_login_at": student.get("last_login_at"), "is_active": student.get("is_active"),
        }])
        profile.loc[0, "academic_level"] = level_value
        profile.loc[0, "preferred_language"] = i18n.LANGUAGE_LABELS.get(str(student.get("preferred_language") or ""), str(student.get("preferred_language") or "—"))
        profile.loc[0, "is_active"] = active_value
        profile_display = i18n.localize_dataframe(profile, lang)
        st.dataframe(profile_display, use_container_width=True, hide_index=True)
        render_completion_requirements(student)
    with tab_learning:
        if progress.empty:
            st.info(u["no_data"])
        else:
            st.dataframe(progress, use_container_width=True, hide_index=True)
    with tab_ai:
        if logs.empty:
            st.info(u["no_data"])
        else:
            st.dataframe(logs, use_container_width=True, hide_index=True)
    with tab_timeline:
        timeline = db.student_events_df(student["id"], limit=250)
        if timeline.empty:
            st.info(u["no_data"])
        else:
            st.dataframe(timeline, use_container_width=True, hide_index=True)


def render_progress_monitor() -> None:
    hero("Progress Monitor", "Track completion of the one-group pre-test/post-test learning flow.")
    df = db.progress_summary_df(len(content.LESSONS))
    if df.empty:
        st.info("No students registered yet.")
        return
    cols = ["participant_code", "full_name", "consent_done", "pre_done", "completed_lessons", "ai_interactions", "post_done", "survey_done", "is_complete_case", "complete_case_missing", "progress_percent"]
    st.dataframe(df[[c for c in cols if c in df.columns]], use_container_width=True, hide_index=True)
    render_progress_bars(df, "participant_code", "progress_percent", "Completion progress")



def _parse_event_detail(detail: Any) -> Dict[str, Any]:
    """Parse JSON event_detail safely for research analytics."""
    if isinstance(detail, dict):
        return detail
    if detail is None:
        return {}
    try:
        return json.loads(str(detail))
    except Exception:
        return {"raw_detail": str(detail)}


def v125_research_interaction_tables(anonymized: bool = False) -> Dict[str, pd.DataFrame]:
    """Derived research tables for V12.5 analytics.

    These tables convert raw events_log rows into analysis-ready indicators:
    concept-builder use, simulator completion, quick checks, and time-before-AI.
    """
    events = db.events_log_df()
    if events.empty:
        empty = pd.DataFrame()
        return {
            "concept_builder_events": empty,
            "learning_activity_events": empty,
            "ai_request_timing_parsed": empty,
            "student_research_journey": empty,
        }

    rows: List[Dict[str, Any]] = []
    for _, row in events.iterrows():
        detail = _parse_event_detail(row.get("event_detail"))
        event_type = str(row.get("event_type") or "")
        base = {
            "created_at": row.get("created_at"),
            "student_id": row.get("student_id"),
            "participant_code": row.get("participant_code"),
            "full_name": row.get("full_name"),
            "actor_role": row.get("actor_role"),
            "event_type": event_type,
            "lesson_id": detail.get("lesson_id", ""),
            "source": detail.get("source", ""),
            "task": detail.get("task", ""),
            "step": detail.get("step", ""),
            "seconds_before_ai": detail.get("seconds_before_ai"),
            "interaction_id": detail.get("interaction_id", ""),
            "quality": detail.get("quality", ""),
            "self_report": detail.get("self_report", ""),
            "answer_length": len(str(detail.get("answer", ""))) if "answer" in detail else None,
        }
        rows.append(base)

    parsed = pd.DataFrame(rows)
    if "seconds_before_ai" in parsed.columns:
        parsed["seconds_before_ai"] = pd.to_numeric(parsed["seconds_before_ai"], errors="coerce")
    try:
        student_groups = db.students_df()[["participant_code", "study_group"]]
        parsed = parsed.merge(student_groups, how="left", on="participant_code")
        parsed["study_group"] = parsed["study_group"].fillna("unknown")
    except Exception:
        parsed["study_group"] = "unknown"

    concept_mask = parsed["event_type"].astype(str).str.startswith("concept_builder") | parsed["event_type"].astype(str).eq("generated_visual_card")
    concept_events = parsed[concept_mask].copy()
    if not concept_events.empty:
        concept_events["builder_action"] = concept_events["event_type"].astype(str).str.replace("concept_builder_", "", regex=False)
        concept_events.loc[concept_events["event_type"].eq("generated_visual_card"), "builder_action"] = "visual_card"

    learning_types = ["animation_viewed", "simulator_opened", "simulator_completed", "check_answered"]
    learning_events = parsed[parsed["event_type"].isin(learning_types)].copy()

    timing_events = parsed[parsed["event_type"].eq("ai_request_timing")].copy()

    journey = pd.DataFrame()
    if not parsed.empty and "participant_code" in parsed.columns:
        grouped = parsed.groupby("participant_code", dropna=False)
        summary_rows = []
        for participant, g in grouped:
            if participant is None or str(participant) == "nan":
                continue
            summary_rows.append({
                "participant_code": participant,
                "study_group": str(g["study_group"].dropna().iloc[0]) if "study_group" in g and not g["study_group"].dropna().empty else "unknown",
                "animation_views": int(g["event_type"].eq("animation_viewed").sum()),
                "simulator_opens": int(g["event_type"].eq("simulator_opened").sum()),
                "simulator_completions": int(g["event_type"].eq("simulator_completed").sum()),
                "quick_checks_answered": int(g["event_type"].eq("check_answered").sum()),
                "concept_builder_requests": int(g["event_type"].astype(str).str.startswith("concept_builder").sum()),
                "visual_cards_generated": int(g["event_type"].eq("generated_visual_card").sum()),
                "ai_timing_events": int(g["event_type"].eq("ai_request_timing").sum()),
                "mean_seconds_before_ai": round(float(pd.to_numeric(g["seconds_before_ai"], errors="coerce").mean()), 2) if pd.to_numeric(g["seconds_before_ai"], errors="coerce").notna().any() else None,
            })
        journey = pd.DataFrame(summary_rows)

    tables = {
        "concept_builder_events": concept_events,
        "learning_activity_events": learning_events,
        "ai_request_timing_parsed": timing_events,
        "student_research_journey": journey,
    }
    if anonymized:
        tables = {name: db.anonymize_dataframe(df) for name, df in tables.items()}
    return tables


def render_v125_research_dashboard() -> None:
    """Research-facing dashboard for interaction traces added in V12.x."""
    st.markdown("### V12.5 research interaction dashboard")
    st.caption("This section turns raw platform traces into paper-ready indicators: simulator use, Concept Builder use, quick checks, and time before AI requests.")

    tables = v125_research_interaction_tables(anonymized=False)
    concept_events = tables.get("concept_builder_events", pd.DataFrame())
    learning_events = tables.get("learning_activity_events", pd.DataFrame())
    timing_events = tables.get("ai_request_timing_parsed", pd.DataFrame())
    journey = tables.get("student_research_journey", pd.DataFrame())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Concept Builder events", int(len(concept_events)))
    c2.metric("Simulator completions", int(learning_events["event_type"].eq("simulator_completed").sum()) if not learning_events.empty else 0)
    c3.metric("Quick checks", int(learning_events["event_type"].eq("check_answered").sum()) if not learning_events.empty else 0)
    if not timing_events.empty and "seconds_before_ai" in timing_events:
        avg_wait = pd.to_numeric(timing_events["seconds_before_ai"], errors="coerce").mean()
        c4.metric("Mean seconds before AI", "—" if pd.isna(avg_wait) else f"{avg_wait:.1f}s")
    else:
        c4.metric("Mean seconds before AI", "—")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Concept Builder", "Simulator journey", "AI timing", "Student summary", "Group comparison"])

    with tab1:
        if concept_events.empty:
            st.info("No Concept Builder events recorded yet.")
        else:
            st.markdown("#### Requests by action")
            by_action = concept_events.groupby("builder_action", as_index=False).size().rename(columns={"size": "events"}).sort_values("events", ascending=False)
            st.dataframe(by_action, use_container_width=True, hide_index=True)
            render_progress_bars(by_action, "builder_action", "events", "Concept Builder events by action")

            st.markdown("#### Requests by lesson")
            by_lesson = concept_events.groupby(["lesson_id", "builder_action"], as_index=False).size().rename(columns={"size": "events"}).sort_values("events", ascending=False)
            st.dataframe(by_lesson, use_container_width=True, hide_index=True)
            st.download_button(
                "Download Concept Builder events CSV",
                data=db.anonymize_dataframe(concept_events).to_csv(index=False).encode("utf-8"),
                file_name="qai_concept_builder_events.csv",
                mime="text/csv",
            )

    with tab2:
        if learning_events.empty:
            st.info("No animation/simulator/check events recorded yet.")
        else:
            st.markdown("#### Learning activity counts")
            activity = learning_events.groupby("event_type", as_index=False).size().rename(columns={"size": "events"}).sort_values("events", ascending=False)
            st.dataframe(activity, use_container_width=True, hide_index=True)
            render_progress_bars(activity, "event_type", "events", "Learning activity events")

            st.markdown("#### Activity by lesson")
            by_lesson = learning_events.groupby(["lesson_id", "event_type"], as_index=False).size().rename(columns={"size": "events"}).sort_values(["lesson_id", "events"], ascending=[True, False])
            st.dataframe(by_lesson, use_container_width=True, hide_index=True)
            st.download_button(
                "Download learning activity events CSV",
                data=db.anonymize_dataframe(learning_events).to_csv(index=False).encode("utf-8"),
                file_name="qai_learning_activity_events.csv",
                mime="text/csv",
            )

    with tab3:
        if timing_events.empty:
            st.info("No time-before-AI events recorded yet.")
        else:
            st.markdown("#### Mean wait before AI by source/task")
            timing_events["seconds_before_ai"] = pd.to_numeric(timing_events["seconds_before_ai"], errors="coerce")
            by_task = timing_events.groupby(["source", "task"], as_index=False)["seconds_before_ai"].agg(["count", "mean", "median"]).reset_index()
            by_task = by_task.rename(columns={"count": "events", "mean": "mean_seconds", "median": "median_seconds"})
            for col in ["mean_seconds", "median_seconds"]:
                by_task[col] = by_task[col].round(2)
            st.dataframe(by_task.sort_values("events", ascending=False), use_container_width=True, hide_index=True)
            render_progress_bars(by_task.rename(columns={"mean_seconds": "value"}), "task", "value", "Mean seconds before AI by task")
            st.download_button(
                "Download AI timing events CSV",
                data=db.anonymize_dataframe(timing_events).to_csv(index=False).encode("utf-8"),
                file_name="qai_ai_timing_events.csv",
                mime="text/csv",
            )

    with tab4:
        if journey.empty:
            st.info("No student-level interaction summary yet.")
        else:
            st.dataframe(journey, use_container_width=True, hide_index=True)
            st.download_button(
                "Download student research journey CSV",
                data=db.anonymize_dataframe(journey).to_csv(index=False).encode("utf-8"),
                file_name="qai_student_research_journey.csv",
                mime="text/csv",
            )

    with tab5:
        st.markdown("#### Control / experimental comparison")
        try:
            progress = db.progress_summary_df(len(content.LESSONS))
            if progress.empty or "study_group" not in progress.columns:
                st.info("No group-level data available yet.")
            else:
                group_summary = progress.groupby("study_group", dropna=False).agg(
                    participants=("participant_code", "count"),
                    mean_pre_score=("pre_score", "mean"),
                    mean_post_score=("post_score", "mean"),
                    mean_learning_gain=("learning_gain", "mean"),
                    mean_completed_lessons=("completed_lessons", "mean"),
                    mean_ai_interactions=("ai_interactions", "mean"),
                ).reset_index()
                for col in ["mean_pre_score", "mean_post_score", "mean_learning_gain", "mean_completed_lessons", "mean_ai_interactions"]:
                    if col in group_summary.columns:
                        group_summary[col] = group_summary[col].round(2)
                st.dataframe(group_summary, use_container_width=True, hide_index=True)
                st.download_button(
                    "Download group comparison CSV",
                    data=group_summary.to_csv(index=False).encode("utf-8"),
                    file_name="qai_group_comparison_summary.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        except Exception as exc:
            st.warning(f"Could not build group comparison yet: {exc}")

def render_learning_analytics() -> None:
    u = evaluator_ui()
    hero(u["analytics_title"], u["analytics_sub"], localized=True)
    df = evaluator_filtered_progress()
    if df.empty:
        st.info(u["no_data"])
        return
    paired = df[df.get("pre_done", False).astype(bool) & df.get("post_done", False).astype(bool)].copy()
    allowed_ids = set(pd.to_numeric(df.get("student_id", pd.Series(dtype=float)), errors="coerce").dropna().astype(int).tolist())
    allowed_codes = set(df.get("participant_code", pd.Series(dtype=str)).dropna().astype(str).tolist())
    pre = pd.to_numeric(paired.get("pre_score", pd.Series(dtype=float)), errors="coerce").dropna()
    post = pd.to_numeric(paired.get("post_score", pd.Series(dtype=float)), errors="coerce").dropna()
    gain = pd.to_numeric(paired.get("learning_gain", pd.Series(dtype=float)), errors="coerce").dropna()
    evaluator_metric_cards([
        (u["students"], str(len(df)), "", "navy"),
        (u["paired_tests"], str(len(paired)), "", "blue"),
        (u["mean_pre"], f"{pre.mean():.1f}%" if not pre.empty else "—", "", "blue"),
        (u["mean_post"], f"{post.mean():.1f}%" if not post.empty else "—", "", "cyan"),
        (u["mean_gain"], f"{gain.mean():.1f} pp" if not gain.empty else "—", "", "gold"),
        (u["ai_logs"], str(int(pd.to_numeric(df.get('ai_interactions',0), errors='coerce').fillna(0).sum())), "", "cyan"),
    ])
    tab1, tab2, tab3, tab4 = st.tabs([u["participants_table"], u["concepts"], u["ai_usage"], u["group_comparison"]])
    with tab1:
        cols = ["participant_code", "full_name", "preferred_language", "study_group", "pre_score", "post_score", "learning_gain", "completed_lessons", "ai_interactions", "progress_percent", "is_complete_case"]
        st.dataframe(df[[c for c in cols if c in df.columns]], use_container_width=True, hide_index=True)
        numeric_cols = [c for c in ["pre_score", "post_score", "learning_gain", "completed_lessons", "ai_interactions", "progress_percent"] if c in df]
        if numeric_cols:
            stats = df[numeric_cols].apply(pd.to_numeric, errors="coerce").describe().round(2)
            st.dataframe(stats, use_container_width=True)
    with tab2:
        concept_df = db.concept_scores_df()
        if not concept_df.empty and allowed_ids and "student_id" in concept_df:
            concept_df = concept_df[pd.to_numeric(concept_df["student_id"], errors="coerce").isin(allowed_ids)].copy()
        if concept_df.empty:
            st.info(u["no_data"])
        else:
            concept_df = concept_df.copy()
            concept_df["concept"] = concept_df["concept"].astype(str).map(lambda x: i18n.concept_label(x, i18n.current_lang(st)))
            pivot = concept_df.pivot_table(index="concept", columns="attempt_type", values="percentage", aggfunc="mean").reset_index()
            pivot.columns.name = None
            if "pre" in pivot and "post" in pivot:
                pivot["gain"] = pd.to_numeric(pivot["post"], errors="coerce") - pd.to_numeric(pivot["pre"], errors="coerce")
            for col in [c for c in pivot.columns if c != "concept"]:
                pivot[col] = pd.to_numeric(pivot[col], errors="coerce").round(1)
            st.dataframe(pivot, use_container_width=True, hide_index=True)
            if "gain" in pivot:
                render_progress_bars(pivot.rename(columns={"concept":"label","gain":"value"}), "label", "value")
    with tab3:
        logs = db.ai_logs_df(limit=None)
        if not logs.empty and allowed_codes and "participant_code" in logs:
            logs = logs[logs["participant_code"].astype(str).isin(allowed_codes)].copy()
        if logs.empty:
            st.info(u["no_data"])
        else:
            observer = logs.groupby(["module", "lesson_id"], dropna=False).agg(
                interactions=("interaction_id", "count"),
                avg_latency_ms=("latency_ms", "mean"),
                avg_response_words=("response_word_count", "mean"),
                avg_student_usefulness=("student_usefulness_rating", "mean"),
                fallback_count=("is_fallback_used", "sum"),
            ).reset_index().sort_values("interactions", ascending=False)
            for col in ["avg_latency_ms", "avg_response_words", "avg_student_usefulness"]:
                if col in observer:
                    observer[col] = pd.to_numeric(observer[col], errors="coerce").round(2)
            st.dataframe(observer, use_container_width=True, hide_index=True)
            render_progress_bars(observer, "module", "interactions")
            task_summary = logs.groupby("task", dropna=False).size().reset_index(name="interactions").sort_values("interactions", ascending=False)
            st.dataframe(task_summary, use_container_width=True, hide_index=True)
            render_progress_bars(task_summary, "task", "interactions")
        timing_raw = db.ai_request_timing_events_df()
        if not timing_raw.empty and allowed_codes and "participant_code" in timing_raw:
            timing_raw = timing_raw[timing_raw["participant_code"].astype(str).isin(allowed_codes)].copy()
        if not timing_raw.empty:
            rows=[]
            for _, row in timing_raw.iterrows():
                try: detail=json.loads(row.get("event_detail") or "{}")
                except Exception: detail={}
                rows.append({"participant_code":row.get("participant_code"),"lesson_id":detail.get("lesson_id",""),"source":detail.get("source",""),"task":detail.get("task",""),"seconds_before_ai":detail.get("seconds_before_ai")})
            timing=pd.DataFrame(rows)
            if not timing.empty:
                timing["seconds_before_ai"]=pd.to_numeric(timing["seconds_before_ai"],errors="coerce")
                st.dataframe(timing, use_container_width=True, hide_index=True)
    with tab4:
        if "study_group" not in df:
            st.info(u["no_data"])
        else:
            group_summary = df.groupby("study_group", dropna=False).agg(
                participants=("participant_code","count"),
                mean_pre_score=("pre_score","mean"),
                mean_post_score=("post_score","mean"),
                mean_learning_gain=("learning_gain","mean"),
                mean_completed_lessons=("completed_lessons","mean"),
                mean_ai_interactions=("ai_interactions","mean"),
            ).reset_index()
            for col in [c for c in group_summary.columns if c.startswith("mean_")]:
                group_summary[col]=pd.to_numeric(group_summary[col],errors="coerce").round(2)
            st.dataframe(group_summary, use_container_width=True, hide_index=True)
            st.download_button(i18n.tr("Download group comparison CSV"), data=group_summary.to_csv(index=False).encode("utf-8-sig"), file_name="3alimnia_group_comparison.csv", mime="text/csv", use_container_width=True)


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
    u = evaluator_ui()
    hero(u["eval_title"], u["eval_sub"], localized=True)
    saved = db.llm_evaluations_df()
    all_ai = db.ai_logs_df(limit=None)
    llm_total = int(all_ai["mode"].isin(["llm", "llm_error"]).sum()) if not all_ai.empty and "mode" in all_ai else len(all_ai)
    evaluated_n = len(saved)
    lpqs_values = pd.to_numeric(saved.get("pedagogical_quality_score", pd.Series(dtype=float)), errors="coerce").dropna()
    evaluator_metric_cards([
        (u["evaluated"], str(evaluated_n), "", "cyan"),
        (u["unrated"], str(max(llm_total-evaluated_n, 0)), "", "gold"),
        (u["lpqs"], f"{lpqs_values.mean():.2f}/5" if not lpqs_values.empty else "—", "", "blue"),
    ])
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        limit = c1.selectbox(u["load"], [10, 20, 50, 100], index=1)
        only_unrated = c2.checkbox(u["only_unrated"], value=True)
        only_llm = c3.checkbox(u["only_llm"], value=True)
    candidates = db.llm_candidate_interactions_df(limit=limit, only_unrated=only_unrated, only_llm=only_llm)
    if candidates.empty:
        st.info(u["no_data"])
        summary = db.llm_evaluation_summary_df()
        if not summary.empty:
            summary = summary.copy(); summary["metric"] = summary["metric"].map(evaluator_label_metric)
            st.dataframe(summary, use_container_width=True, hide_index=True)
        return

    evaluator_section(u["candidate"])
    preview_cols = ["interaction_id", "created_at", "participant_code", "concept", "task", "mode", "provider", "model", "latency_ms", "response_word_count", "existing_quality_score"]
    st.dataframe(candidates[[c for c in preview_cols if c in candidates.columns]], use_container_width=True, hide_index=True)
    interaction_ids = candidates["interaction_id"].astype(int).tolist()
    selected_id = st.selectbox(u["select_interaction"], interaction_ids, format_func=lambda x: f"#{x} · {candidates[candidates['interaction_id']==x]['participant_code'].iloc[0] or '—'}")
    row = candidates[candidates["interaction_id"] == selected_id].iloc[0].to_dict()

    st.markdown(f"<div class='v45-ai-context' dir='{u['dir']}'><span>{escape(str(row.get('participant_code') or '—'))}</span><b>{escape(i18n.concept_label(str(row.get('concept') or '—'), i18n.current_lang(st)))}</b><small>{escape(str(row.get('task') or '—'))} · {escape(str(row.get('provider') or '—'))}</small></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        evaluator_section(u["prompt"])
        st.markdown(f"<div class='v45-transcript learner' dir='{u['dir']}'>{escape(str(row.get('prompt') or '[No input]'))}</div>", unsafe_allow_html=True)
    with c2:
        evaluator_section(u["response"])
        st.markdown(f"<div class='v45-transcript ai' dir='{u['dir']}'>{escape(str(row.get('response') or ''))}</div>", unsafe_allow_html=True)
    if row.get("diagnostic"):
        with st.expander(u["diagnostic"]):
            st.code(str(row.get("diagnostic"))[:4000])

    evaluator_section(u["rubric"], u["rubric_help"])
    with st.form(f"llm_eval_{selected_id}"):
        c1, c2 = st.columns(2)
        with c1:
            conceptual_accuracy = st.slider(u["conceptual_accuracy"], 1, 5, 3)
            answer_relevance = st.slider(u["answer_relevance"], 1, 5, 3)
            pedagogical_clarity = st.slider(u["pedagogical_clarity"], 1, 5, 3)
            scaffolding_quality = st.slider(u["scaffolding_quality"], 1, 5, 3)
        with c2:
            qiskit_alignment = st.slider(u["qiskit_alignment"], 1, 5, 3)
            reflection_support = st.slider(u["reflection_support"], 1, 5, 3)
            personalization = st.slider(u["personalization"], 1, 5, 3)
            preview_score = (conceptual_accuracy + answer_relevance + pedagogical_clarity + scaffolding_quality + qiskit_alignment + reflection_support + personalization) / 7
            st.metric("LPQS", f"{preview_score:.2f}/5")
        overall_comment = st.text_area(u["comment"], height=110)
        submitted = st.form_submit_button(u["save_eval"], type="primary", use_container_width=True)
    if submitted:
        db.save_llm_evaluation(selected_id, secret("EVALUATOR_USERNAME", "evaluator"), conceptual_accuracy, answer_relevance, pedagogical_clarity, scaffolding_quality, qiskit_alignment, reflection_support, personalization, overall_comment)
        st.success(u["saved"])
        st.rerun()

    evaluator_section(u["current_summary"])
    summary = db.llm_evaluation_summary_df()
    if summary.empty:
        st.info(u["no_data"])
    else:
        summary = summary.copy(); summary["metric"] = summary["metric"].map(evaluator_label_metric)
        st.dataframe(summary, use_container_width=True, hide_index=True)
        render_progress_bars(summary, "metric", "mean_score")
    with st.expander(u["full_evals"]):
        st.dataframe(db.llm_evaluations_df(), use_container_width=True, hide_index=True)


def render_feedback_logs() -> None:
    u = evaluator_ui()
    hero(u["logs_title"], u["logs_sub"], localized=True)
    options = db.ai_filter_options()
    if not any(options.values()) and db.count_rows("ai_interactions") == 0:
        st.info(u["no_data"])
        return
    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
        mode_filter = c1.multiselect(u["mode"], options.get("mode", []))
        module_filter = c2.multiselect(u["module"], options.get("module", []))
        concept_filter = c3.multiselect(u["concept"], options.get("concept", []), format_func=lambda x: i18n.concept_label(x, i18n.current_lang(st)))
        participant_code = c4.text_input(u["search_code"])
        max_rows = c5.selectbox(u["rows"], [50, 100, 200, 500], index=1)
    filtered = db.ai_logs_df(limit=max_rows, mode=mode_filter, module=module_filter, concept=concept_filter, participant_code=participant_code.strip() or None)
    if filtered.empty:
        st.info(u["no_logs"])
        return

    fallback = pd.to_numeric(filtered.get("is_fallback_used", pd.Series(dtype=float)), errors="coerce").fillna(0)
    latency = pd.to_numeric(filtered.get("latency_ms", pd.Series(dtype=float)), errors="coerce").dropna()
    usefulness = pd.to_numeric(filtered.get("student_usefulness_rating", pd.Series(dtype=float)), errors="coerce").dropna()
    evaluator_metric_cards([
        (u["matches"], str(len(filtered)), "", "blue"),
        (u["fallback_rate"], f"{fallback.mean()*100:.1f}%" if len(fallback) else "—", "", "gold"),
        (u["latency"], f"{latency.mean():.0f} ms" if not latency.empty else "—", "", "cyan"),
        (u["usefulness"], f"{usefulness.mean():.2f}/5" if not usefulness.empty else "—", "", "navy"),
    ])

    evaluator_section(u["matches"])
    compact_cols = ["interaction_id", "created_at", "participant_code", "module", "concept", "task", "mode", "provider", "model", "latency_ms", "response_word_count", "student_usefulness_rating", "is_fallback_used", "error_type"]
    compact = filtered[[c for c in compact_cols if c in filtered.columns]].copy()
    if "concept" in compact:
        compact["concept"] = compact["concept"].astype(str).map(lambda x: i18n.concept_label(x, i18n.current_lang(st)))
    st.dataframe(compact, use_container_width=True, hide_index=True)

    evaluator_section(u["inspect"])
    ids = filtered["interaction_id"].astype(int).tolist()
    selected_id = st.selectbox(u["inspect"], ids, format_func=lambda x: f"#{x} · {filtered[filtered['interaction_id']==x]['participant_code'].iloc[0] or '—'}", key="v45_log_inspector")
    row = filtered[filtered["interaction_id"] == selected_id].iloc[0].to_dict()
    st.markdown(f"<div class='v45-ai-context' dir='{u['dir']}'><span>{escape(str(row.get('participant_code') or '—'))}</span><b>{escape(i18n.concept_label(str(row.get('concept') or '—'), i18n.current_lang(st)))}</b><small>{escape(str(row.get('task') or '—'))} · {escape(str(row.get('mode') or '—'))} · {escape(str(row.get('provider') or '—'))}</small></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='v45-transcript learner' dir='{u['dir']}'><b>{escape(u['prompt'])}</b><p>{escape(str(row.get('prompt') or ''))}</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='v45-transcript ai' dir='{u['dir']}'><b>{escape(u['response'])}</b><p>{escape(str(row.get('response') or ''))}</p></div>", unsafe_allow_html=True)
    if row.get("diagnostic"):
        with st.expander(u["diagnostic"]):
            st.code(str(row.get("diagnostic"))[:5000])


def render_survey_results() -> None:
    u = evaluator_ui()
    hero(u["survey_title"], u["survey_sub"], localized=True)
    survey = db.survey_df()
    if survey.empty:
        st.info(u["no_data"])
        return
    rows, open_rows = [], []
    for _, row in survey.iterrows():
        responses = json.loads(row.get("responses_json") or "{}")
        open_feedback = json.loads(row.get("open_feedback_json") or "{}")
        rows.append({"participant_code": row["participant_code"], "full_name": row["full_name"], **responses})
        open_rows.append({"participant_code": row["participant_code"], "full_name": row["full_name"], **open_feedback})
    likert_df, open_df = pd.DataFrame(rows), pd.DataFrame(open_rows)
    numeric_cols = [key for key, _ in content.SURVEY_ITEMS if key in likert_df]
    mean_score = float(likert_df[numeric_cols].stack().mean()) if numeric_cols else None
    evaluator_metric_cards([
        (u["survey"], str(len(likert_df)), "", "blue"),
        (u["usefulness"], f"{mean_score:.2f}/5" if mean_score is not None else "—", "", "cyan"),
    ])
    tab1, tab2 = st.tabs([i18n.tr("Likert responses"), i18n.tr("Open-ended feedback")])
    with tab1:
        st.dataframe(likert_df, use_container_width=True, hide_index=True)
        if numeric_cols:
            means = likert_df[numeric_cols].mean().reset_index(); means.columns = ["item", "mean_score"]
            st.dataframe(means, use_container_width=True, hide_index=True)
            render_progress_bars(means, "item", "mean_score")
    with tab2:
        st.dataframe(open_df, use_container_width=True, hide_index=True)


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
    u = evaluator_ui()
    hero(u["exports_title"], u["exports_sub"], localized=True)
    st.markdown(f"<div class='v45-export-grid' dir='{u['dir']}'><article><span>01</span><h3>{escape(u['anon_title'])}</h3><p>{escape(u['anon_body'])}</p></article><article class='secure'><span>02</span><h3>{escape(u['full_title'])}</h3><p>{escape(u['full_body'])}</p></article></div>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    prepare_anon = col_a.button(u["prepare_anon"], type="primary", use_container_width=True)
    prepare_full = col_b.button(u["prepare_full"], use_container_width=True)
    if prepare_anon:
        with st.spinner(u["preparing"]):
            dfs = db.research_export_tables(len(content.LESSONS), anonymized=True)
            dfs.update(v125_research_interaction_tables(anonymized=True))
            st.session_state["export_tables"] = dfs
            st.session_state["export_excel"] = to_excel_bytes(dfs)
            st.session_state["export_filename"] = "3alimnia_research_export_anonymized.xlsx"
            st.session_state["export_kind"] = "anonymized"
            db.log_event(None, "evaluator", "anonymized_export_prepared", "Evaluator prepared anonymized research export")
    if prepare_full:
        with st.spinner(u["preparing"]):
            dfs = {"students": db.students_df(), **db.research_export_tables(len(content.LESSONS), anonymized=False)}
            dfs.update(v125_research_interaction_tables(anonymized=False))
            st.session_state["export_tables"] = dfs
            st.session_state["export_excel"] = to_excel_bytes(dfs)
            st.session_state["export_filename"] = "3alimnia_full_admin_backup.xlsx"
            st.session_state["export_kind"] = "full"
            db.log_event(None, "evaluator", "full_backup_prepared", "Evaluator prepared full administrative backup")
    if "export_excel" in st.session_state:
        kind = st.session_state.get("export_kind", "anonymized")
        st.success(u["anon_title"] if kind == "anonymized" else u["full_title"])
        st.download_button(u["download"], data=st.session_state["export_excel"], file_name=st.session_state.get("export_filename", "3alimnia_export.xlsx"), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", use_container_width=True)
        dfs = st.session_state.get("export_tables", {})
        if dfs:
            evaluator_section(u["preview"])
            selected = st.selectbox(u["dataset"], list(dfs.keys()))
            data = dfs[selected]
            preview = data.head(200) if hasattr(data, "head") else data
            st.dataframe(preview, use_container_width=True, hide_index=True)
            if hasattr(data, "__len__") and len(data) > 200:
                st.caption(f"200 / {len(data)}")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> None:
    db.init_db()
    init_state()
    i18n.install_streamlit_i18n(st)
    i18n.apply_language_css(st, i18n.current_lang(st))
    perform_scroll_top_if_requested()

    # V4.8 uses Streamlit's native sidebar as a true application rail.
    # Unlike an in-page column, the native rail owns its viewport and scrollbar,
    # so a long learner/evaluator menu never increases the document height or
    # forces users to scroll the main page merely to reach navigation items.
    role = st.session_state.get("role")
    with st.sidebar:
        st.markdown("<span class='v48-native-sidebar-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
        render_sidebar(st.sidebar)

    render_global_escape_navigation()

    if role == "student":
        render_student_app()
    elif role == "evaluator":
        render_evaluator_app()
    else:
        render_role_selection()


if __name__ == "__main__":
    main()
