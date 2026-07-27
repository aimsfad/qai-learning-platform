from __future__ import annotations

from html import escape
from typing import Callable, Dict, List, Tuple

import streamlit as st

import branding
import content
import i18n
import router


COPY: Dict[str, Dict[str, object]] = {
    "ar": {
        "dir": "rtl",
        "nav_home": "الرئيسية",
        "nav_programs": "البرامج",
        "nav_ai": "مختبر الذكاء التوليدي",
        "nav_institutions": "للجامعات والباحثين",
        "hero_kicker": "منصة تعلّم توليدية تقيس الفهم لا الحفظ",
        "hero_title": "تعلّم المفاهيم الصعبة عبر التجربة، ثم اطلب مساعدة ذكية موجهة.",
        "hero_body": "تجمع علّمنيا بين المسارات التعليمية، الشرح البصري، البرمجة التطبيقية، مدرّب ذكاء توليدي مقيّد تربويًا، وتقييم علمي لجودة استجابات الذكاء الاصطناعي.",
        "start": "ابدأ التعلّم",
        "explore": "استكشف البرامج",
        "evaluator": "فضاء المقيّم والباحث",
        "trust": ["العربية · Français · English", "تعلّم تطبيقي", "AI بعد محاولة المتعلم", "LPQS للتقييم التربوي"],
        "stats": [("6", "وحدات Qiskit"), ("3", "لغات واجهة ومحتوى"), ("7", "معايير LPQS"), ("24/7", "دعم تعلّم موجّه")],
        "programs_kicker": "مسارات واضحة مثل أفضل المنصات العالمية",
        "programs_title": "ابدأ بمسار، ثم انتقل من الأساسيات إلى الإتقان",
        "programs_body": "كل برنامج يوضح المستوى، المدة، الوحدات، المتطلبات، ومخرجات التعلّم قبل أن يبدأ الطالب.",
        "available": "متاح الآن",
        "coming": "قريبًا",
        "level": "المستوى",
        "duration": "المدة المتوقعة",
        "modules": "الوحدات",
        "beginner": "مبتدئ",
        "hours": "4–6 ساعات",
        "view_program": "عرض البرنامج",
        "start_program": "ابدأ المسار",
        "engine_kicker": "الميزة الفارقة",
        "engine_title": "محرك تعلّم توليدي، لا مجرد روبوت محادثة",
        "engine_body": "يُفعَّل الذكاء الاصطناعي داخل دورة تعلم مضبوطة: محاولة، تشخيص، تلميح، تطبيق، ثم دليل إتقان.",
        "engine_steps": [
            ("01", "حاول أولًا", "يكتب المتعلم توقعه أو تفسيره قبل طلب المساعدة."),
            ("02", "شاهد وجرّب", "تُعرض الفكرة بصريًا وتُربط بكود أو نشاط تطبيقي."),
            ("03", "اطلب تلميحًا", "يقدّم المدرّب سؤالًا أو تشبيهًا أو خطوة تالية، لا حلًا جاهزًا."),
            ("04", "اثبت الفهم", "تُقاس النتيجة باختبار، انعكاس، وسجل تعلم قابل للتحليل."),
        ],
        "pillars": [
            ("smart_toy", "مدرّب AI تربوي", "دعم متدرج داخل الدرس بعد محاولة المتعلم، مع تسجيل السياق وزمن الاستجابة."),
            ("auto_awesome", "استوديو إنتاج مواد", "إنشاء شرح، تشبيه، اختبار قصير، وجسر Qiskit من قوالب تربوية مضبوطة."),
            ("fact_check", "تقييم الاستجابات", "LPQS يقيس الدقة والوضوح والسقالات والتخصيص والتوافق مع Qiskit."),
            ("monitoring", "تحليلات تعلم وبحث", "تقدم المتعلمين، التفاعلات، الاختبارات، والتصدير المجهول للبحث العلمي."),
        ],
        "institution_kicker": "للجامعات، المختبرات، ومراكز التكوين",
        "institution_title": "منصة تعليمية وأداة قياس علمي في نظام واحد",
        "institution_body": "يمكن للمؤسسة تشغيل برنامج، متابعة التقدم، تقييم جودة الذكاء الاصطناعي، وإنشاء بيانات بحثية مجهولة الهوية دون فقدان سياق التعلم.",
        "institution_cta": "استكشف فضاء المقيّم",
        "catalog_title": "البرامج والمسارات",
        "catalog_body": "واجهة برامج واضحة تشبه منصات MOOC الحديثة، مع إضافة التعلّم التوليدي والتقييم العلمي.",
        "ai_studio_title": "مختبر الذكاء التوليدي للتعلّم",
        "ai_studio_body": "منظومة لإنتاج الموارد التعليمية ودعم المتعلم وتقييم الاستجابات ضمن ضوابط تربوية واضحة.",
        "institution_page_title": "حلول الجامعات والباحثين",
        "institution_page_body": "تشغيل مجموعات تجريبية، تتبع التقدم، LPQS، التصدير البحثي، وإدارة المشاركين من لوحة واحدة.",
        "how_compares": "لماذا يختلف عن منصات الدورات التقليدية؟",
        "compare_rows": [
            ("مسارات منظمة ومحتوى متعدد اللغات", "✓", "✓"),
            ("شرح بصري وتطبيق Qiskit", "جزئي", "✓"),
            ("AI داخل الدرس بعد محاولة المتعلم", "غالبًا لا", "✓"),
            ("تقييم علمي لجودة استجابة AI", "لا", "✓"),
            ("استوديو إنتاج مواد تعليمية", "محدود", "✓"),
            ("تصدير بيانات بحثية مجهولة", "محدود", "✓"),
        ],
        "traditional": "منصة تعليمية تقليدية",
        "ours": "3alimnIA",
        "footer": "3alimnIA · تعلّم توليدي مضبوط تربويًا · الجزائر",
    },
    "fr": {
        "dir": "ltr",
        "nav_home": "Accueil",
        "nav_programs": "Programmes",
        "nav_ai": "Studio IA générative",
        "nav_institutions": "Universités & recherche",
        "hero_kicker": "Une plateforme générative qui mesure la compréhension",
        "hero_title": "Comprenez les concepts difficiles par l’action, puis demandez une aide IA guidée.",
        "hero_body": "3alimnIA combine parcours structurés, explications visuelles, pratique, coach IA contraint et évaluation scientifique de la qualité pédagogique des réponses générées.",
        "start": "Commencer à apprendre",
        "explore": "Explorer les programmes",
        "evaluator": "Espace évaluateur et recherche",
        "trust": ["العربية · Français · English", "Apprentissage pratique", "IA après la tentative", "Évaluation LPQS"],
        "stats": [("6", "modules Qiskit"), ("3", "langues"), ("7", "critères LPQS"), ("24/7", "aide guidée")],
        "programs_kicker": "DES PARCOURS CLAIRS, COMME LES MEILLEURES PLATEFORMES",
        "programs_title": "Partez des fondamentaux et progressez vers la maîtrise",
        "programs_body": "Chaque programme présente le niveau, la durée, les modules, les prérequis et les acquis attendus avant l’inscription.",
        "available": "Disponible",
        "coming": "Bientôt",
        "level": "Niveau",
        "duration": "Durée estimée",
        "modules": "Modules",
        "beginner": "Débutant",
        "hours": "4–6 heures",
        "view_program": "Voir le programme",
        "start_program": "Commencer",
        "engine_kicker": "NOTRE DIFFÉRENCIATION",
        "engine_title": "Un moteur d’apprentissage génératif, pas seulement un chatbot",
        "engine_body": "L’IA intervient dans une boucle contrôlée : tentative, diagnostic, indice, application, puis preuve de maîtrise.",
        "engine_steps": [
            ("01", "Tenter d’abord", "L’apprenant formule une prédiction ou une première explication."),
            ("02", "Voir et manipuler", "Le concept est visualisé puis relié au code ou à une activité."),
            ("03", "Demander un indice", "Le coach propose une question, une analogie ou l’étape suivante."),
            ("04", "Prouver la maîtrise", "Tests, réflexions et traces d’usage constituent une preuve d’apprentissage."),
        ],
        "pillars": [
            ("smart_toy", "Coach IA pédagogique", "Aide progressive dans la leçon, après une tentative, avec contexte et traçabilité."),
            ("auto_awesome", "Studio de contenu", "Génération d’explications, analogies, quiz et ponts Qiskit via des modèles validés."),
            ("fact_check", "Évaluation des réponses", "LPQS mesure exactitude, clarté, scaffolding, personnalisation et alignement Qiskit."),
            ("monitoring", "Analytics & recherche", "Progression, interactions, évaluations et exports anonymisés pour la recherche."),
        ],
        "institution_kicker": "UNIVERSITÉS, LABORATOIRES ET CENTRES DE FORMATION",
        "institution_title": "Une plateforme pédagogique et un instrument scientifique",
        "institution_body": "Déployez un programme, suivez les progrès, évaluez l’IA et exportez des données anonymisées sans perdre le contexte d’apprentissage.",
        "institution_cta": "Découvrir l’espace évaluateur",
        "catalog_title": "Programmes et parcours",
        "catalog_body": "Une expérience de catalogue claire inspirée des MOOC modernes, enrichie par l’IA pédagogique et la mesure scientifique.",
        "ai_studio_title": "Studio d’apprentissage génératif",
        "ai_studio_body": "Produire des ressources, soutenir l’apprenant et évaluer les réponses générées avec des garde-fous pédagogiques.",
        "institution_page_title": "Solutions pour universités et chercheurs",
        "institution_page_body": "Groupes d’étude, suivi, LPQS, export scientifique et gestion des participants dans un seul espace.",
        "how_compares": "En quoi 3alimnIA dépasse une plateforme de cours classique ?",
        "compare_rows": [
            ("Parcours structurés et contenu multilingue", "✓", "✓"),
            ("Visualisation et pratique Qiskit", "Partiel", "✓"),
            ("IA intégrée après la tentative", "Rare", "✓"),
            ("Évaluation scientifique des réponses IA", "Non", "✓"),
            ("Studio de production pédagogique", "Limité", "✓"),
            ("Export de données de recherche anonymisées", "Limité", "✓"),
        ],
        "traditional": "Plateforme classique",
        "ours": "3alimnIA",
        "footer": "3alimnIA · Apprentissage génératif encadré · Algérie",
    },
    "en": {
        "dir": "ltr",
        "nav_home": "Home",
        "nav_programs": "Programs",
        "nav_ai": "Generative AI Studio",
        "nav_institutions": "Universities & research",
        "hero_kicker": "A generative learning platform that measures understanding",
        "hero_title": "Learn difficult concepts by doing, then ask for guided AI support.",
        "hero_body": "3alimnIA combines structured paths, visual explanations, hands-on practice, a constrained AI coach, and scientific evaluation of the pedagogical quality of generated responses.",
        "start": "Start learning",
        "explore": "Explore programs",
        "evaluator": "Evaluator & research workspace",
        "trust": ["العربية · Français · English", "Practice-based learning", "AI after learner attempt", "LPQS evaluation"],
        "stats": [("6", "Qiskit modules"), ("3", "languages"), ("7", "LPQS criteria"), ("24/7", "guided support")],
        "programs_kicker": "CLEAR PATHS, INSPIRED BY WORLD-CLASS LEARNING PLATFORMS",
        "programs_title": "Start with fundamentals and progress toward mastery",
        "programs_body": "Every program clearly presents level, duration, modules, prerequisites, and expected outcomes before enrollment.",
        "available": "Available now",
        "coming": "Coming soon",
        "level": "Level",
        "duration": "Estimated time",
        "modules": "Modules",
        "beginner": "Beginner",
        "hours": "4–6 hours",
        "view_program": "View program",
        "start_program": "Start path",
        "engine_kicker": "OUR DIFFERENTIATOR",
        "engine_title": "A generative learning engine, not just a chatbot",
        "engine_body": "AI operates inside a controlled learning loop: attempt, diagnose, scaffold, apply, and demonstrate mastery.",
        "engine_steps": [
            ("01", "Attempt first", "The learner writes a prediction or initial explanation before asking for help."),
            ("02", "See and manipulate", "The concept is visualized and connected to code or a hands-on task."),
            ("03", "Request a scaffold", "The coach offers a question, analogy, or next step instead of the final answer."),
            ("04", "Prove mastery", "Tests, reflections, and interaction traces provide evidence of learning."),
        ],
        "pillars": [
            ("smart_toy", "Pedagogical AI Coach", "Progressive support inside the lesson after an attempt, with context and traceability."),
            ("auto_awesome", "Learning Content Studio", "Generate explanations, analogies, quizzes, and Qiskit bridges from validated templates."),
            ("fact_check", "AI Response Evaluation", "LPQS measures accuracy, clarity, scaffolding, personalization, and Qiskit alignment."),
            ("monitoring", "Learning Analytics & Research", "Progress, interactions, assessments, and anonymized research exports."),
        ],
        "institution_kicker": "FOR UNIVERSITIES, LABS, AND TRAINING CENTERS",
        "institution_title": "A learning platform and a scientific instrument in one system",
        "institution_body": "Run a program, monitor progress, evaluate AI quality, and export anonymized evidence without losing the learning context.",
        "institution_cta": "Explore evaluator workspace",
        "catalog_title": "Programs and learning paths",
        "catalog_body": "A clear modern MOOC-style catalog, extended with pedagogical AI and scientific measurement.",
        "ai_studio_title": "Generative Learning Studio",
        "ai_studio_body": "Create resources, support learners, and evaluate generated responses within explicit pedagogical guardrails.",
        "institution_page_title": "Solutions for universities and researchers",
        "institution_page_body": "Study cohorts, progress monitoring, LPQS, research exports, and participant management in one place.",
        "how_compares": "How is 3alimnIA different from a traditional course platform?",
        "compare_rows": [
            ("Structured paths and multilingual content", "✓", "✓"),
            ("Visual explanation and Qiskit practice", "Partial", "✓"),
            ("AI embedded after learner attempt", "Rare", "✓"),
            ("Scientific evaluation of AI responses", "No", "✓"),
            ("Learning-content generation studio", "Limited", "✓"),
            ("Anonymized research-data export", "Limited", "✓"),
        ],
        "traditional": "Traditional platform",
        "ours": "3alimnIA",
        "footer": "3alimnIA · Pedagogically constrained generative learning · Algeria",
    },
}


def copy() -> Dict[str, object]:
    return COPY.get(i18n.current_lang(st), COPY["en"])


def _logo_img() -> str:
    uri = branding.official_logo_data_uri()
    if not uri:
        return branding.logo_lockup_html(compact=False, language=i18n.current_lang(st))
    return f"<img src='{uri}' alt='3alimnIA' class='v6-logo-img'/>"


def _route_button(label: str, route: str, *, key: str, primary: bool = False, icon: str = "") -> None:
    text = f"{icon} {label}".strip()
    if st.button(text, key=key, type="primary" if primary else "secondary", use_container_width=True):
        router.navigate(route)


def render_public_utility_bar() -> None:
    c = copy()
    with st.container():
        st.markdown("<span class='v6-public-bar-marker'></span>", unsafe_allow_html=True)
        logo_col, language_col, access_col = st.columns([5.2, 1.25, 1.7], gap="small", vertical_alignment="center")
        with logo_col:
            st.markdown(f"<div class='v6-mini-brand'>{_logo_img()}</div>", unsafe_allow_html=True)
        with language_col:
            import main_app
            main_app.render_language_selector(st, key="v6_public_language", label_visibility="collapsed")
        with access_col:
            _route_button(str(c["start"]), router.route_key("public", "student"), key="v6_public_access", primary=True)


def render_home() -> None:
    c = copy()
    direction = str(c["dir"])
    st.markdown("<span class='v6-home-marker'></span>", unsafe_allow_html=True)
    with st.container(border=False):
        left, right = st.columns([1.08, .92], gap="large", vertical_alignment="center")
        with left:
            st.markdown(
                f"""
                <section class='v6-hero-copy' dir='{direction}'>
                  <div class='v6-kicker'>{escape(str(c['hero_kicker']))}</div>
                  <h1>{escape(str(c['hero_title']))}</h1>
                  <p>{escape(str(c['hero_body']))}</p>
                  <div class='v6-trust-row'>{''.join(f'<span>{escape(str(x))}</span>' for x in c['trust'])}</div>
                </section>
                """,
                unsafe_allow_html=True,
            )
            a, b, d = st.columns([1.05, 1.05, 1.15], gap="small")
            with a:
                _route_button(str(c["start"]), router.route_key("public", "student"), key="v6_hero_start", primary=True, icon="▶")
            with b:
                _route_button(str(c["explore"]), router.route_key("public", "programs"), key="v6_hero_programs", icon="▦")
            with d:
                _route_button(str(c["evaluator"]), router.route_key("public", "evaluator"), key="v6_hero_eval", icon="◈")
        with right:
            st.markdown(
                f"""
                <section class='v6-hero-visual' dir='ltr'>
                  <div class='v6-orbital-bg'></div>
                  <div class='v6-visual-logo'>{_logo_img()}</div>
                  <div class='v6-ai-core'><b>AI</b><span>Learn</span></div>
                  <span class='v6-node v6-node-q'>Qiskit</span>
                  <span class='v6-node v6-node-c'>Coach</span>
                  <span class='v6-node v6-node-e'>LPQS</span>
                  <div class='v6-pulse p1'></div><div class='v6-pulse p2'></div><div class='v6-pulse p3'></div>
                </section>
                """,
                unsafe_allow_html=True,
            )
    st.markdown(
        "<section class='v6-stat-grid'>" + "".join(
            f"<article><strong>{escape(str(value))}</strong><span>{escape(str(label))}</span></article>" for value, label in c["stats"]
        ) + "</section>",
        unsafe_allow_html=True,
    )
    _section_heading(str(c["programs_kicker"]), str(c["programs_title"]), str(c["programs_body"]), direction)
    _program_cards(direction, compact=True)
    _section_heading(str(c["engine_kicker"]), str(c["engine_title"]), str(c["engine_body"]), direction)
    st.markdown(
        f"<section class='v6-engine-grid' dir='{direction}'>" + "".join(
            f"<article><span>{escape(str(num))}</span><h3>{escape(str(title))}</h3><p>{escape(str(body))}</p></article>"
            for num, title, body in c["engine_steps"]
        ) + "</section>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<section class='v6-pillar-grid' dir='{direction}'>" + "".join(
            f"<article><div class='material-symbols-rounded'>{escape(str(icon))}</div><h3>{escape(str(title))}</h3><p>{escape(str(body))}</p></article>"
            for icon, title, body in c["pillars"]
        ) + "</section>",
        unsafe_allow_html=True,
    )
    _institution_strip(direction)
    _footer(direction)


def _section_heading(kicker: str, title: str, body: str, direction: str) -> None:
    st.markdown(
        f"<header class='v6-section-head' dir='{direction}'><span>{escape(kicker)}</span><h2>{escape(title)}</h2><p>{escape(body)}</p></header>",
        unsafe_allow_html=True,
    )


def _program_cards(direction: str, compact: bool = False, track_ids: List[str] | None = None) -> None:
    c = copy()
    track_order = track_ids or ["quantum", "ml", "ai"]
    cols = st.columns(len(track_order), gap="large")
    for col, track_id in zip(cols, track_order):
        track = branding.TRACKS[track_id]
        status = c["available"] if track_id == "quantum" else c["coming"]
        with col:
            st.markdown(
                f"""
                <article class='v6-program-card {track_id}' dir='{direction}'>
                  <div class='v6-program-top'><span class='v6-program-icon'>{escape(str(track['icon']))}</span><em>{escape(str(status))}</em></div>
                  <h3>{escape(str(track['name'][i18n.current_lang(st)]))}</h3>
                  <p>{escape(str(track['description'][i18n.current_lang(st)]))}</p>
                  <div class='v6-program-meta'>
                    <span><b>{escape(str(c['level']))}</b>{escape(str(c['beginner']))}</span>
                    <span><b>{escape(str(c['duration']))}</b>{escape(str(c['hours']))}</span>
                    <span><b>{escape(str(c['modules']))}</b>{len(content.LESSONS) if track_id == 'quantum' else '—'}</span>
                  </div>
                </article>
                """,
                unsafe_allow_html=True,
            )
            label = c["start_program"] if track_id == "quantum" else c["view_program"]
            if st.button(str(label), key=f"v6_program_{track_id}_{'compact' if compact else 'full'}", type="primary" if track_id == "quantum" else "secondary", use_container_width=True):
                if track_id == "quantum":
                    router.navigate(router.route_key("public", "student"))
                else:
                    st.session_state["v6_preview_track"] = track_id
                    st.info(track["audience"][i18n.current_lang(st)])


def render_programs() -> None:
    c = copy(); direction = str(c["dir"])
    st.markdown("<span class='v6-catalog-marker'></span>", unsafe_allow_html=True)
    _page_hero(str(c["catalog_title"]), str(c["catalog_body"]), direction, "library_books")
    lang = i18n.current_lang(st)
    all_label = {"ar": "الكل", "fr": "Tous", "en": "All"}[lang]
    options = [("quantum", branding.TRACKS["quantum"]["name"][lang]), ("ml", branding.TRACKS["ml"]["name"][lang]), ("ai", branding.TRACKS["ai"]["name"][lang]), ("all", all_label)]
    current = st.session_state.get("v6_catalog_filter", "all")
    chips = st.columns(4, gap="small")
    for col, (value, label) in zip(chips, options):
        if col.button(str(label), use_container_width=True, key=f"v6_chip_{value}", type="primary" if current == value else "secondary"):
            st.session_state["v6_catalog_filter"] = value
            st.rerun()
    visible = ["quantum", "ml", "ai"] if current == "all" else [current]
    _program_cards(direction, track_ids=visible)
    st.markdown("<div class='v6-program-detail-spacer'></div>", unsafe_allow_html=True)
    _section_heading(str(c["engine_kicker"]), str(c["engine_title"]), str(c["engine_body"]), direction)
    st.markdown(
        f"<section class='v6-course-outline' dir='{direction}'>"
        + "".join(
            f"<article><span>{idx:02d}</span><div><h3>{escape(str(lesson.get('title', '')))}</h3><p>{escape(str(lesson.get('objective', '')))}</p></div></article>"
            for idx, lesson in enumerate(content.lessons_for(i18n.current_lang(st)), start=1)
        )
        + "</section>",
        unsafe_allow_html=True,
    )
    _footer(direction)


def render_ai_studio() -> None:
    c = copy(); direction = str(c["dir"])
    st.markdown("<span class='v6-ai-studio-marker'></span>", unsafe_allow_html=True)
    _page_hero(str(c["ai_studio_title"]), str(c["ai_studio_body"]), direction, "auto_awesome")
    st.markdown(
        f"<section class='v6-studio-flow' dir='{direction}'>" + "".join(
            f"<article><div class='material-symbols-rounded'>{escape(str(icon))}</div><h3>{escape(str(title))}</h3><p>{escape(str(body))}</p></article>"
            for icon, title, body in c["pillars"]
        ) + "</section>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<h2 class='v6-subtitle' dir='{direction}'>{escape(str(c['how_compares']))}</h2>", unsafe_allow_html=True)
    table_rows = "".join(
        f"<tr><td>{escape(str(label))}</td><td>{escape(str(traditional))}</td><td><b>{escape(str(ours))}</b></td></tr>"
        for label, traditional, ours in c["compare_rows"]
    )
    st.markdown(
        f"<div class='v6-comparison-wrap' dir='{direction}'><table><thead><tr><th></th><th>{escape(str(c['traditional']))}</th><th>{escape(str(c['ours']))}</th></tr></thead><tbody>{table_rows}</tbody></table></div>",
        unsafe_allow_html=True,
    )
    a, b = st.columns(2, gap="small")
    with a:
        _route_button(str(c["start"]), router.route_key("public", "student"), key="v6_studio_start", primary=True)
    with b:
        _route_button(str(c["evaluator"]), router.route_key("public", "evaluator"), key="v6_studio_eval")
    _footer(direction)


def render_institutions() -> None:
    c = copy(); direction = str(c["dir"])
    st.markdown("<span class='v6-institution-marker'></span>", unsafe_allow_html=True)
    _page_hero(str(c["institution_page_title"]), str(c["institution_page_body"]), direction, "account_balance")
    cards: List[Tuple[str, str, str]] = [
        ("groups", "Cohorts", "Create participant accounts, study groups, and controlled access."),
        ("monitoring", "Analytics", "Monitor tests, lesson activity, AI interactions, and completion."),
        ("fact_check", "LPQS", "Rate generated responses with a seven-criterion pedagogical rubric."),
        ("download", "Research export", "Export anonymized evidence for analysis and publication."),
    ]
    translations = {
        "ar": [
            ("groups", "المجموعات", "إنشاء حسابات المشاركين ومجموعات الدراسة والتحكم في الوصول."),
            ("monitoring", "التحليلات", "متابعة الاختبارات والتعلّم وتفاعلات AI وحالة الإكمال."),
            ("fact_check", "LPQS", "تقييم الاستجابات المولدة وفق سبعة معايير تربوية."),
            ("download", "التصدير البحثي", "تصدير بيانات مجهولة الهوية للتحليل والنشر العلمي."),
        ],
        "fr": [
            ("groups", "Cohortes", "Créer des comptes, groupes d’étude et accès contrôlés."),
            ("monitoring", "Analytics", "Suivre tests, activités, interactions IA et complétion."),
            ("fact_check", "LPQS", "Évaluer les réponses avec sept critères pédagogiques."),
            ("download", "Export recherche", "Exporter des données anonymisées pour l’analyse et la publication."),
        ],
        "en": cards,
    }
    items = translations[i18n.current_lang(st)]
    st.markdown(
        f"<section class='v6-institution-grid' dir='{direction}'>" + "".join(
            f"<article><div class='material-symbols-rounded'>{escape(icon)}</div><h3>{escape(title)}</h3><p>{escape(body)}</p></article>" for icon, title, body in items
        ) + "</section>",
        unsafe_allow_html=True,
    )
    _institution_strip(direction)
    _footer(direction)


def _page_hero(title: str, body: str, direction: str, icon: str) -> None:
    st.markdown(
        f"""
        <section class='v6-page-hero' dir='{direction}'>
          <div class='material-symbols-rounded'>{escape(icon)}</div>
          <div><span>3alimnIA</span><h1>{escape(title)}</h1><p>{escape(body)}</p></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _institution_strip(direction: str) -> None:
    c = copy()
    st.markdown(
        f"""
        <section class='v6-institution-strip' dir='{direction}'>
          <div><span>{escape(str(c['institution_kicker']))}</span><h2>{escape(str(c['institution_title']))}</h2><p>{escape(str(c['institution_body']))}</p></div>
          <div class='v6-lpqs-badge'><b>LPQS</b><small>7 criteria</small></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    if st.button(str(c["institution_cta"]), key="v6_institution_cta", use_container_width=False):
        router.navigate(router.route_key("public", "evaluator"))


def _footer(direction: str) -> None:
    c = copy()
    st.markdown(
        f"<footer class='v6-footer' dir='{direction}'><div>{_logo_img()}</div><span>{escape(str(c['footer']))}</span></footer>",
        unsafe_allow_html=True,
    )
