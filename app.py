from __future__ import annotations

from html import escape
from typing import Callable, Dict, List

import streamlit as st

import branding
import db
import i18n
import main_app
import router
import ui_v6
from config import APP_ICON, APP_TITLE, load_css


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed",
)
load_css()


def _bootstrap() -> None:
    db.init_db()
    main_app.init_state()
    i18n.install_streamlit_i18n(st)
    i18n.apply_language_css(st, i18n.current_lang(st))
    main_app.perform_scroll_top_if_requested()


def _route_renderer(role: str, internal_page: str, renderer: Callable[[], None]) -> Callable[[], None]:
    def _page() -> None:
        st.session_state.role = role
        if role == "student":
            st.session_state.student_page = internal_page
        elif role == "evaluator":
            st.session_state.evaluator_page = internal_page
        renderer()

    _page.__name__ = f"render_{role}_{internal_page.lower().replace(' ', '_').replace('-', '_')}"
    return _page


def _ensure_public(route_name: str) -> None:
    if st.session_state.get("role") is not None:
        st.session_state.role = None
        router.queue(router.route_key("public", route_name))
        st.rerun()


def _public_home() -> None:
    _ensure_public("home")
    ui_v6.render_home()


def _public_programs() -> None:
    _ensure_public("programs")
    ui_v6.render_programs()


def _public_ai_studio() -> None:
    _ensure_public("ai_studio")
    ui_v6.render_ai_studio()


def _public_institutions() -> None:
    _ensure_public("institutions")
    ui_v6.render_institutions()


def _student_access() -> None:
    if st.session_state.get("role") != "student":
        st.session_state.role = "student"
        st.session_state.student_page = "Student Home"
        router.queue(router.route_key("student", "Student Home"))
        st.rerun()
    main_app.render_student_app()


def _evaluator_access() -> None:
    if st.session_state.get("role") != "evaluator":
        st.session_state.role = "evaluator"
        st.session_state.evaluator_page = "Evaluator Dashboard"
        router.queue(router.route_key("evaluator", "Evaluator Dashboard"))
        st.rerun()
    main_app.render_evaluator_app()


def _toolbar_copy() -> Dict[str, str]:
    lang = i18n.current_lang(st)
    values = {
        "ar": {
            "student": "فضاء المتعلم",
            "evaluator": "فضاء المقيّم والباحث",
            "home": "الرئيسية",
            "account": "تغيير الحساب",
            "workspace": "تغيير الفضاء",
            "logout": "تسجيل الخروج",
            "language": "اللغة",
        },
        "fr": {
            "student": "Espace apprenant",
            "evaluator": "Espace évaluateur et recherche",
            "home": "Accueil",
            "account": "Changer de compte",
            "workspace": "Changer d’espace",
            "logout": "Se déconnecter",
            "language": "Langue",
        },
        "en": {
            "student": "Learner workspace",
            "evaluator": "Evaluator & research workspace",
            "home": "Home",
            "account": "Change account",
            "workspace": "Switch workspace",
            "logout": "Sign out",
            "language": "Language",
        },
    }
    return values.get(lang, values["en"])


def _queue_home() -> None:
    role = st.session_state.get("role")
    if role == "student":
        st.session_state.student_page = "Student Home"
        router.queue(router.route_key("student", "Student Home"))
    elif role == "evaluator":
        st.session_state.evaluator_page = "Evaluator Dashboard"
        router.queue(router.route_key("evaluator", "Evaluator Dashboard"))
    else:
        router.queue(router.route_key("public", "home"))


def _render_toolbar(current_title: str) -> None:
    """Render a stable workspace toolbar with the official logo on every page.

    The layout is mirrored for RTL so the white logo stays on the visual right in
    Arabic and on the visual left in French/English. All controls remain native
    Streamlit widgets to preserve reliable routing and callbacks.
    """
    role = st.session_state.get("role")
    lang = i18n.current_lang(st)
    direction = i18n.direction(lang)
    copy = _toolbar_copy()
    workspace = copy.get(role) or getattr(branding, "BRAND_NAME_LATIN", branding.BRAND_NAME)

    with st.container(border=True, key="v68_workspace_toolbar"):
        st.markdown("<span class='v5-toolbar-marker v68-toolbar-marker' aria-hidden='true'></span>", unsafe_allow_html=True)

        if role in {"student", "evaluator"}:
            if lang == "ar":
                logout_col, workspace_col, account_col, home_col, language_col, identity_col, logo_col = st.columns(
                    [1.02, 1.18, 1.28, .88, 1.25, 2.28, 1.48], gap="small", vertical_alignment="center"
                )
            else:
                logo_col, identity_col, language_col, home_col, account_col, workspace_col, logout_col = st.columns(
                    [1.48, 2.28, 1.25, .88, 1.28, 1.18, 1.02], gap="small", vertical_alignment="center"
                )

            with logo_col:
                st.markdown("<span class='v68-internal-logo-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
                if branding.HEADER_WHITE_LOGO_PATH.exists():
                    st.image(str(branding.HEADER_WHITE_LOGO_PATH), use_container_width=True)
                elif branding.OFFICIAL_LOGO_PATH.exists():
                    st.image(str(branding.OFFICIAL_LOGO_PATH), use_container_width=True)

            with identity_col:
                st.markdown(
                    f"<div class='v5-toolbar-identity v68-toolbar-identity' dir='{direction}'>"
                    f"<span>{escape(workspace)}</span><strong>{escape(current_title)}</strong></div>",
                    unsafe_allow_html=True,
                )
            with language_col:
                main_app.render_language_selector(st, key="v5_global_language", label_visibility="collapsed")
            with home_col:
                st.button(copy["home"], key="v5_home", use_container_width=True, on_click=_queue_home)
            with account_col:
                st.button(copy["account"], key="v5_account", use_container_width=True, on_click=main_app.change_account_callback)
            with workspace_col:
                st.button(copy["workspace"], key="v5_workspace", use_container_width=True, on_click=main_app.switch_workspace_callback)
            with logout_col:
                st.button(copy["logout"], key="v5_logout", type="primary", use_container_width=True, on_click=main_app.logout_callback)
        else:
            logo_col, identity_col, language_col = st.columns([1.5, 4.7, 1.35], gap="small", vertical_alignment="center")
            with logo_col:
                st.markdown("<span class='v68-internal-logo-marker' aria-hidden='true'></span>", unsafe_allow_html=True)
                if branding.HEADER_WHITE_LOGO_PATH.exists():
                    st.image(str(branding.HEADER_WHITE_LOGO_PATH), use_container_width=True)
            with identity_col:
                st.markdown(
                    f"<div class='v5-toolbar-identity v68-toolbar-identity' dir='{direction}'>"
                    f"<span>{escape(workspace)}</span><strong>{escape(current_title)}</strong></div>",
                    unsafe_allow_html=True,
                )
            with language_col:
                main_app.render_language_selector(st, key="v5_global_language", label_visibility="collapsed")



def _student_tool_copy() -> Dict[str, str]:
    lang = i18n.current_lang(st)
    values = {
        "ar": {
            "title": "أدوات التعلّم",
            "dashboard": "لوحة المتعلّم",
            "modules": "الوحدات وQiskit",
            "coach": "المدرّب الذكي",
            "plan": "الخطة التكيفية",
            "more": "التقييم والبحث",
            "pre": "الاختبار القبلي",
            "post": "الاختبار البعدي",
            "survey": "الاستبيان",
            "research": "إشعار البحث",
            "locked": "يُفتح بعد إكمال الخطوة السابقة",
        },
        "fr": {
            "title": "Outils d’apprentissage",
            "dashboard": "Tableau apprenant",
            "modules": "Modules & Qiskit",
            "coach": "Coach IA",
            "plan": "Plan adaptatif",
            "more": "Évaluation & recherche",
            "pre": "Pré-test",
            "post": "Post-test",
            "survey": "Questionnaire",
            "research": "Notice de recherche",
            "locked": "Disponible après l’étape précédente",
        },
        "en": {
            "title": "Learning tools",
            "dashboard": "Learner dashboard",
            "modules": "Modules & Qiskit",
            "coach": "AI Coach",
            "plan": "Adaptive plan",
            "more": "Assessment & research",
            "pre": "Pre-test",
            "post": "Post-test",
            "survey": "Survey",
            "research": "Research notice",
            "locked": "Available after the previous step",
        },
    }
    return values.get(lang, values["en"])


def _queue_student_tool(page: str) -> None:
    st.session_state.role = "student"
    st.session_state.student_page = page
    router.queue(router.route_key("student", page))


def _render_student_tool_dock() -> None:
    """Keep the learner's core tools visible on every authenticated page.

    The native router remains the source of truth; this dock only queues routes
    that are registered for the current learner state. Locked destinations stay
    visible so the learning sequence remains understandable.
    """
    student = main_app.current_student()
    if not student:
        return

    copy = _student_tool_copy()
    direction = i18n.direction(i18n.current_lang(st))
    allowed = set(main_app.student_pages_allowed(student))
    current = st.session_state.get("student_page", "Student Home")

    primary_tools = [
        ("Student Home", "⌂", copy["dashboard"]),
        ("Learning Module", "▦", copy["modules"]),
        ("AI Tutor Lab", "◈", copy["coach"]),
        ("Adaptive Plan", "✦", copy["plan"]),
    ]
    secondary_tools = [
        ("Pre-test", "01", copy["pre"]),
        ("Post-test", "02", copy["post"]),
        ("Satisfaction Survey", "✓", copy["survey"]),
        ("Research Notice", "◎", copy["research"]),
    ]

    with st.container(border=True, key="v67_student_tool_dock"):
        st.markdown(
            f"<span class='v67-student-dock-marker' aria-hidden='true'></span>"
            f"<div class='v67-student-dock-title' dir='{direction}'>"
            f"<span class='material-symbols-rounded'>apps</span>"
            f"<strong>{escape(copy['title'])}</strong></div>",
            unsafe_allow_html=True,
        )
        cols = st.columns(4, gap="small")
        for col, (page, icon, label) in zip(cols, primary_tools):
            with col:
                available = page in allowed
                st.button(
                    f"{icon} {label}",
                    key=f"v67_student_tool_{page}",
                    type="primary" if current == page else "secondary",
                    use_container_width=True,
                    disabled=not available,
                    help=None if available else copy["locked"],
                    on_click=_queue_student_tool if available else None,
                    args=(page,) if available else (),
                )

        expanded = any(page == current for page, _, _ in secondary_tools)
        with st.expander(copy["more"], expanded=expanded):
            secondary_cols = st.columns(4, gap="small")
            for col, (page, icon, label) in zip(secondary_cols, secondary_tools):
                with col:
                    available = page in allowed
                    st.button(
                        f"{icon} {label}",
                        key=f"v67_student_secondary_{page}",
                        type="primary" if current == page else "secondary",
                        use_container_width=True,
                        disabled=not available,
                        help=None if available else copy["locked"],
                        on_click=_queue_student_tool if available else None,
                        args=(page,) if available else (),
                    )


def _nav_text() -> Dict[str, str]:
    lang = i18n.current_lang(st)
    values = {
        "ar": {
            "public_section": "المنصة", "home": "الرئيسية", "learner": "فضاء المتعلم", "evaluator": "فضاء المقيّم",
            "programs": "البرامج", "ai_studio": "مختبر الذكاء التوليدي", "institutions": "للجامعات والباحثين",
            "overview": "نظرة عامة", "learning": "التعلّم", "assessment": "التقييم", "research": "البحث والموافقة",
            "account": "الحساب", "platform_home": "العودة إلى واجهة المنصة", "learners": "المتعلمون",
            "ai_quality": "الذكاء الاصطناعي والجودة", "data": "البيانات والتصدير", "evaluator_login": "دخول المقيّم",
        },
        "fr": {
            "public_section": "Plateforme", "home": "Accueil", "learner": "Espace apprenant", "evaluator": "Espace évaluateur",
            "programs": "Programmes", "ai_studio": "Studio IA générative", "institutions": "Universités & recherche",
            "overview": "Vue d’ensemble", "learning": "Apprentissage", "assessment": "Évaluation", "research": "Recherche et consentement",
            "account": "Compte", "platform_home": "Retour à l’accueil de la plateforme", "learners": "Apprenants",
            "ai_quality": "IA et qualité", "data": "Données et export", "evaluator_login": "Connexion évaluateur",
        },
        "en": {
            "public_section": "Platform", "home": "Home", "learner": "Learner workspace", "evaluator": "Evaluator workspace",
            "programs": "Programs", "ai_studio": "Generative AI Studio", "institutions": "Universities & research",
            "overview": "Overview", "learning": "Learning", "assessment": "Assessment", "research": "Research & consent",
            "account": "Account", "platform_home": "Back to platform home", "learners": "Learners",
            "ai_quality": "AI & quality", "data": "Data & exports", "evaluator_login": "Evaluator sign in",
        },
    }
    return values.get(lang, values["en"])

def _page(title: str, icon: str, key: str, callable_: Callable[[], None], *, default: bool = False):
    page = st.Page(callable_, title=title, icon=icon, default=default)
    return key, page


def _build_pages() -> tuple[dict, Dict[str, object]]:
    lang = i18n.current_lang(st)
    role = st.session_state.get("role")
    nav = _nav_text()
    registry: Dict[str, object] = {}

    def add(group: Dict[str, List[object]], section: str, title: str, icon: str, key: str, fn: Callable[[], None], default: bool = False):
        route, page = _page(title, icon, key, fn, default=default)
        group.setdefault(section, []).append(page)
        registry[route] = page

    pages: Dict[str, List[object]] = {}

    if role is None:
        add(pages, nav["public_section"], nav["home"], ":material/home:", router.route_key("public", "home"), _public_home, True)
        add(pages, nav["public_section"], nav["programs"], ":material/library_books:", router.route_key("public", "programs"), _public_programs)
        add(pages, nav["public_section"], nav["ai_studio"], ":material/auto_awesome:", router.route_key("public", "ai_studio"), _public_ai_studio)
        add(pages, nav["public_section"], nav["institutions"], ":material/account_balance:", router.route_key("public", "institutions"), _public_institutions)
        add(pages, nav["public_section"], nav["learner"], ":material/school:", router.route_key("public", "student"), _student_access)
        add(pages, nav["public_section"], nav["evaluator"], ":material/analytics:", router.route_key("public", "evaluator"), _evaluator_access)
        return pages, registry

    if role == "student":
        student = main_app.current_student()
        allowed = main_app.student_pages_allowed(student)
        labels = main_app.learning_ui_copy()
        page_defs = [
            ("Overview", "Student Home", labels["home"], ":material/dashboard:", True),
            ("Learning", "Adaptive Plan", labels["plan"], ":material/route:", False),
            ("Learning", "Learning Module", labels["modules"], ":material/menu_book:", False),
            ("Learning", "AI Tutor Lab", labels["tutor"], ":material/smart_toy:", False),
            ("Assessment", "Pre-test", labels["pre"], ":material/quiz:", False),
            ("Assessment", "Post-test", labels["post"], ":material/fact_check:", False),
            ("Assessment", "Satisfaction Survey", labels["survey"], ":material/rate_review:", False),
            ("Research", "Research Notice", labels["notice"], ":material/policy:", False),
            ("Account", "Sign in", i18n.page_label("Sign in", lang), ":material/login:", False),
            ("Account", "Create account", i18n.page_label("Create account", lang), ":material/person_add:", False),
        ]
        for section, internal, title, icon, default in page_defs:
            if internal not in allowed:
                continue
            add(
                pages,
                {"Overview": nav["overview"], "Learning": nav["learning"], "Assessment": nav["assessment"], "Research": nav["research"], "Account": nav["account"]}.get(section, section),
                title,
                icon,
                router.route_key("student", internal),
                _route_renderer("student", internal, main_app.render_student_app),
                default=default,
            )
        # Keep public home registered and visible as an explicit escape route.
        add(pages, nav["account"], nav["platform_home"], ":material/apps:", router.route_key("public", "home"), _public_home)
        return pages, registry

    # Evaluator role.
    if not st.session_state.get("evaluator_logged_in"):
        add(pages, nav["evaluator"], nav["evaluator_login"], ":material/login:", router.route_key("evaluator", "Evaluator Dashboard"), _route_renderer("evaluator", "Evaluator Dashboard", main_app.render_evaluator_app), True)
        add(pages, nav["account"], nav["platform_home"], ":material/apps:", router.route_key("public", "home"), _public_home)
        return pages, registry

    evaluator_defs = [
        ("Overview", "Evaluator Dashboard", ":material/dashboard:"),
        ("Overview", "Study Protocol", ":material/assignment:"),
        ("Learners", "Students", ":material/groups:"),
        ("Learners", "Registration Accounts", ":material/manage_accounts:"),
        ("Learners", "Student Details", ":material/person_search:"),
        ("AI Quality", "AI Tutor Logs", ":material/chat:") ,
        ("AI Quality", "AI Response Evaluation", ":material/rate_review:"),
        ("AI Quality", "AI Metrics", ":material/monitoring:"),
        ("Data", "Exports", ":material/download:"),
    ]
    for idx, (section, internal, icon) in enumerate(evaluator_defs):
        add(
            pages,
            {"Overview": nav["overview"], "Learners": nav["learners"], "AI Quality": nav["ai_quality"], "Data": nav["data"]}.get(section, section),
            i18n.page_label(internal, lang),
            icon,
            router.route_key("evaluator", internal),
            _route_renderer("evaluator", internal, main_app.render_evaluator_app),
            default=idx == 0,
        )
    add(pages, nav["account"], nav["platform_home"], ":material/apps:", router.route_key("public", "home"), _public_home)
    return pages, registry


def main() -> None:
    _bootstrap()
    pages, registry = _build_pages()
    navigation = st.navigation(pages, position="hidden")
    router.register_pages(registry)
    router.process_pending_route()
    if st.session_state.get("role") is None:
        ui_v6.render_public_header(getattr(navigation, "title", APP_TITLE))
    else:
        _render_toolbar(getattr(navigation, "title", APP_TITLE))
        if st.session_state.get("role") == "student":
            _render_student_tool_dock()
    navigation.run()


if __name__ == "__main__":
    main()
