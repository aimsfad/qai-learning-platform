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
        "programs_kicker": "برامج مصممة للتدرّج والإتقان",
        "programs_title": "ابدأ بمسار، ثم انتقل من الأساسيات إلى الإتقان",
        "programs_body": "كل برنامج يوضح المستوى، المدة، الوحدات، المتطلبات، ومخرجات التعلّم قبل أن يبدأ الطالب.",
        "program_audience": "الفئة المستهدفة",
        "capabilities_kicker": "من التعلّم إلى الدليل",
        "capabilities_title": "قدرات تربوية وبحثية تتجاوز منصة الدورات التقليدية",
        "capabilities_body": "يجمع النظام بين الدعم التوليدي، إنتاج المواد، قياس جودة الاستجابات، وتحليلات التعلّم في تجربة واحدة.",
        "institution_bullets": ["إدارة المجموعات", "تحليلات التعلّم", "تقييم LPQS", "تصدير بحثي مجهول"],
        "lpqs_label": "7 معايير جودة",
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
        "ai_studio_badge": "مختبر الذكاء التوليدي للتعلّم",
        "ai_studio_visual_labels": ["توليد المحتوى", "مدرّب تعلّم", "تقييم LPQS"],
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
        "programs_kicker": "DES PARCOURS CONÇUS POUR PROGRESSER",
        "programs_title": "Partez des fondamentaux et progressez vers la maîtrise",
        "programs_body": "Chaque programme présente le niveau, la durée, les modules, les prérequis et les acquis attendus avant l’inscription.",
        "program_audience": "Public visé",
        "capabilities_kicker": "DE L’APPRENTISSAGE À LA PREUVE",
        "capabilities_title": "Des capacités pédagogiques et scientifiques au-delà d’un catalogue de cours",
        "capabilities_body": "Le système réunit accompagnement génératif, production de ressources, évaluation des réponses et analytics dans une même expérience.",
        "institution_bullets": ["Gestion des cohortes", "Learning analytics", "Évaluation LPQS", "Export anonymisé"],
        "lpqs_label": "7 critères qualité",
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
        "ai_studio_badge": "Studio IA générative pour apprendre",
        "ai_studio_visual_labels": ["Création de contenu", "Coach d’apprentissage", "Évaluation LPQS"],
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
        "programs_kicker": "PATHS DESIGNED FOR PROGRESS AND MASTERY",
        "programs_title": "Start with fundamentals and progress toward mastery",
        "programs_body": "Every program clearly presents level, duration, modules, prerequisites, and expected outcomes before enrollment.",
        "program_audience": "Best for",
        "capabilities_kicker": "FROM LEARNING TO EVIDENCE",
        "capabilities_title": "Pedagogical and research capabilities beyond a traditional course catalog",
        "capabilities_body": "The system unifies generative support, learning-content production, response evaluation, and learning analytics in one experience.",
        "institution_bullets": ["Cohort management", "Learning analytics", "LPQS evaluation", "Anonymized export"],
        "lpqs_label": "7 quality criteria",
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
        "ai_studio_badge": "Generative AI studio for learning",
        "ai_studio_visual_labels": ["Content generation", "Learning coach", "LPQS evaluation"],
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


def _render_official_logo(width: int = 188) -> None:
    """Render the approved logo through Streamlit's media endpoint.

    Using ``st.image`` avoids browser failures caused by very large data URIs
    inside Markdown on Streamlit Community Cloud.
    """
    if branding.OFFICIAL_LOGO_PATH.exists():
        st.image(str(branding.OFFICIAL_LOGO_PATH), width=width)
    else:
        st.markdown(branding.logo_lockup_html(compact=True, language=i18n.current_lang(st)), unsafe_allow_html=True)


def _header_button(label: str, route: str, *, key: str, active: bool = False, cta: bool = False) -> None:
    st.button(
        label,
        key=key,
        type="primary" if active or cta else "secondary",
        use_container_width=True,
        on_click=router.queue,
        args=(route,),
    )


def render_public_header(current_title: str = "") -> None:
    """Render a compact, modern public header with native Streamlit controls."""
    c = copy()
    lang = i18n.current_lang(st)
    header_labels = {
        "ar": {"home": "الرئيسية", "programs": "البرامج", "ai": "مختبر الذكاء", "institutions": "للجامعات", "evaluator": "دخول المقيّم", "start": "ابدأ الآن"},
        "fr": {"home": "Accueil", "programs": "Programmes", "ai": "Studio IA", "institutions": "Universités", "evaluator": "Évaluateur", "start": "Commencer"},
        "en": {"home": "Home", "programs": "Programs", "ai": "AI Studio", "institutions": "Institutions", "evaluator": "Evaluator", "start": "Start now"},
    }[lang]
    with st.container(border=False, key="v61_public_header"):
        logo_col, nav_col, language_col, evaluator_col, start_col = st.columns(
            [1.65, 4.35, 1.0, 1.1, 1.05], gap="small", vertical_alignment="center"
        )
        with logo_col:
            _render_official_logo(176)
        with nav_col:
            home_col, programs_col, ai_col, institutions_col = st.columns([.84, .95, 1.05, 1.06], gap="small")
            nav_items = [
                (home_col, header_labels["home"], router.route_key("public", "home"), "v61_nav_home", str(c["nav_home"])),
                (programs_col, header_labels["programs"], router.route_key("public", "programs"), "v61_nav_programs", str(c["nav_programs"])),
                (ai_col, header_labels["ai"], router.route_key("public", "ai_studio"), "v61_nav_ai", str(c["nav_ai"])),
                (institutions_col, header_labels["institutions"], router.route_key("public", "institutions"), "v61_nav_institutions", str(c["nav_institutions"])),
            ]
            for col, label, route, key, page_title in nav_items:
                with col:
                    _header_button(label, route, key=key, active=current_title == page_title)
        with language_col:
            import main_app
            main_app.render_language_selector(st, key="v61_public_language", label_visibility="collapsed")
        with evaluator_col:
            _header_button(header_labels["evaluator"], router.route_key("public", "evaluator"), key="v61_public_evaluator")
        with start_col:
            _header_button(header_labels["start"], router.route_key("public", "student"), key="v61_public_start", cta=True)


def render_home() -> None:
    c = copy()
    direction = str(c["dir"])
    lang = i18n.current_lang(st)
    visual_subtitle = {
        "ar": "منظومة التعلّم التوليدي",
        "fr": "SYSTÈME D’APPRENTISSAGE GÉNÉRATIF",
        "en": "GENERATIVE LEARNING OS",
    }.get(lang, "GENERATIVE LEARNING OS")
    st.markdown("<span class='v61-home-marker'></span>", unsafe_allow_html=True)
    with st.container(border=False, key="v61_hero"):
        copy_col, visual_col = st.columns([1.13, .87], gap="large", vertical_alignment="center")
        with copy_col:
            st.markdown(
                f"""
                <section class='v61-hero-copy' dir='{direction}'>
                  <div class='v61-eyebrow'><span></span>{escape(str(c['hero_kicker']))}</div>
                  <h1>{escape(str(c['hero_title']))}</h1>
                  <p>{escape(str(c['hero_body']))}</p>
                  <div class='v61-benefit-row'>{''.join(f'<span>{escape(str(x))}</span>' for x in c['trust'])}</div>
                </section>
                """,
                unsafe_allow_html=True,
            )
            start_col, programs_col, evaluator_col = st.columns([1.05, 1.05, 1.18], gap="small")
            with start_col:
                _route_button(str(c["start"]), router.route_key("public", "student"), key="v61_hero_start", primary=True)
            with programs_col:
                _route_button(str(c["explore"]), router.route_key("public", "programs"), key="v61_hero_programs")
            with evaluator_col:
                _route_button(str(c["evaluator"]), router.route_key("public", "evaluator"), key="v61_hero_eval")
        with visual_col:
            st.markdown(
                f"""
                <section class='v61-learning-visual' dir='ltr'>
                  <div class='v61-visual-grid'></div>
                  <div class='v61-visual-label'>
                    <b>3alimn<span>IA</span></b>
                    <small>{escape(visual_subtitle)}</small>
                  </div>
                  <div class='v61-orbit orbit-a'></div><div class='v61-orbit orbit-b'></div>
                  <div class='v61-ai-core'><strong>AI</strong><span>Learn</span></div>
                  <div class='v61-float-card card-q'><b>Qiskit</b><small>Practice</small></div>
                  <div class='v61-float-card card-c'><b>Coach</b><small>Guided hints</small></div>
                  <div class='v61-float-card card-l'><b>LPQS</b><small>Quality evidence</small></div>
                  <i class='v61-dot dot-a'></i><i class='v61-dot dot-b'></i><i class='v61-dot dot-c'></i>
                </section>
                """,
                unsafe_allow_html=True,
            )
    _render_stats_grid(direction, context="home")
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
    _section_heading(str(c["capabilities_kicker"]), str(c["capabilities_title"]), str(c["capabilities_body"]), direction)
    st.markdown(
        f"<section class='v6-pillar-grid v65-capabilities-grid' dir='{direction}'>" + "".join(
            f"<article><div class='material-symbols-rounded'>{escape(str(icon))}</div><h3>{escape(str(title))}</h3><p>{escape(str(body))}</p></article>"
            for icon, title, body in c["pillars"]
        ) + "</section>",
        unsafe_allow_html=True,
    )
    _institution_strip(direction)
    _footer(direction)


def _section_heading(kicker: str, title: str, body: str, direction: str) -> None:
    st.markdown(
        f"""
        <header class='v61-section-head' dir='{direction}'>
          <span class='v61-section-kicker'>{escape(kicker)}</span>
          <h2>{escape(title)}</h2>
          <p>{escape(body)}</p>
        </header>
        """,
        unsafe_allow_html=True,
    )


STAT_ICONS = ("account_tree", "translate", "fact_check", "support_agent")


def _render_stats_grid(direction: str, *, context: str = "home") -> None:
    """Render responsive evidence cards without relying on Streamlit columns."""
    c = copy()
    cards = []
    for icon, (value, label) in zip(STAT_ICONS, c["stats"]):
        cards.append(
            "<article class='v64-stat-card'>"
            f"<div class='v64-stat-icon material-symbols-rounded'>{escape(icon)}</div>"
            "<div class='v64-stat-copy'>"
            f"<strong>{escape(str(value))}</strong>"
            f"<span>{escape(str(label))}</span>"
            "</div></article>"
        )
    st.markdown(
        f"<section class='v64-stats-grid v64-stats-{escape(context)}' dir='{direction}'>"
        + "".join(cards)
        + "</section>",
        unsafe_allow_html=True,
    )


def _render_ai_studio_banner(c: Dict[str, object], direction: str) -> None:
    """Render a localized, responsive AI Studio hero with a compact visual system."""
    labels = list(c["ai_studio_visual_labels"])
    tag_titles = [str(item[1]) for item in c["pillars"][:3]]
    lang = i18n.current_lang(st)
    brand_line = "3alimnIA · علّمنيا" if lang == "ar" else "3alimnIA"
    st.markdown(
        f"""
        <section class='v64-ai-banner' dir='{direction}'>
          <div class='v64-ai-glow glow-one'></div>
          <div class='v64-ai-glow glow-two'></div>
          <div class='v64-ai-banner-copy'>
            <span class='v64-ai-brand'>{escape(brand_line)}</span>
            <div class='v64-ai-badge'>
              <span class='material-symbols-rounded'>auto_awesome</span>
              <b>{escape(str(c['ai_studio_badge']))}</b>
            </div>
            <h1>{escape(str(c['ai_studio_title']))}</h1>
            <p>{escape(str(c['ai_studio_body']))}</p>
            <div class='v64-ai-banner-tags'>
              {''.join(f'<span>{escape(title)}</span>' for title in tag_titles)}
            </div>
          </div>
          <div class='v64-ai-banner-visual' aria-hidden='true'>
            <div class='v64-ai-ring ring-one'></div>
            <div class='v64-ai-ring ring-two'></div>
            <div class='v64-ai-core'><strong>AI</strong><small>Studio</small></div>
            <div class='v64-ai-chip chip-one'>{escape(str(labels[0]))}</div>
            <div class='v64-ai-chip chip-two'>{escape(str(labels[1]))}</div>
            <div class='v64-ai-chip chip-three'>{escape(str(labels[2]))}</div>
            <i class='v64-ai-point point-one'></i>
            <i class='v64-ai-point point-two'></i>
            <i class='v64-ai-point point-three'></i>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _program_cards(direction: str, compact: bool = False, track_ids: List[str] | None = None) -> None:
    c = copy()
    lang = i18n.current_lang(st)
    track_order = track_ids or ["quantum", "ml", "ai"]
    cols = st.columns(len(track_order), gap="large")
    path_labels = {"ar": "مسار تعلّم", "fr": "Parcours", "en": "Learning path"}
    for index, (col, track_id) in enumerate(zip(cols, track_order), start=1):
        track = branding.TRACKS[track_id]
        is_available = track_id == "quantum"
        status = c["available"] if is_available else c["coming"]
        status_class = "available" if is_available else "coming"
        modules_value = len(content.LESSONS) if is_available else "—"
        feature_class = " featured" if is_available else ""
        with col:
            st.markdown(
                f"""
                <article class='v65-program-card {track_id}{feature_class}' dir='{direction}'>
                  <div class='v65-program-head'>
                    <div class='v65-program-icon'>{escape(str(track['icon']))}</div>
                    <div class='v65-program-status {status_class}'>{escape(str(status))}</div>
                  </div>
                  <span class='v65-path-label'>{escape(path_labels[lang])} {index:02d}</span>
                  <h3>{escape(str(track['name'][lang]))}</h3>
                  <p class='v65-program-desc'>{escape(str(track['description'][lang]))}</p>
                  <div class='v65-program-audience'>
                    <span class='material-symbols-rounded'>group</span>
                    <small>{escape(str(c['program_audience']))}</small>
                    <b>{escape(str(track['audience'][lang]))}</b>
                  </div>
                  <div class='v65-program-meta'>
                    <span><small>{escape(str(c['level']))}</small><b>{escape(str(c['beginner']))}</b></span>
                    <span><small>{escape(str(c['duration']))}</small><b>{escape(str(c['hours']))}</b></span>
                    <span><small>{escape(str(c['modules']))}</small><b>{modules_value}</b></span>
                  </div>
                </article>
                """,
                unsafe_allow_html=True,
            )
            label = c["start_program"] if is_available else c["view_program"]
            if st.button(
                str(label),
                key=f"v65_program_{track_id}_{'compact' if compact else 'full'}",
                type="primary" if is_available else "secondary",
                use_container_width=True,
            ):
                if is_available:
                    router.navigate(router.route_key("public", "student"))
                else:
                    st.session_state["v6_preview_track"] = track_id
                    st.info(track["audience"][lang])


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
    _render_ai_studio_banner(c, direction)
    action_a, action_b = st.columns(2, gap="small")
    with action_a:
        _route_button(str(c["start"]), router.route_key("public", "student"), key="v64_studio_start", primary=True)
    with action_b:
        _route_button(str(c["evaluator"]), router.route_key("public", "evaluator"), key="v64_studio_eval")
    _render_stats_grid(direction, context="studio")
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
    bullets = "".join(
        f"<span><i class='material-symbols-rounded'>check_circle</i>{escape(str(item))}</span>"
        for item in c["institution_bullets"]
    )
    st.markdown(
        f"""
        <section class='v65-institution-banner' dir='{direction}'>
          <div class='v65-institution-copy'>
            <span class='v65-institution-kicker'>{escape(str(c['institution_kicker']))}</span>
            <h2>{escape(str(c['institution_title']))}</h2>
            <p>{escape(str(c['institution_body']))}</p>
            <div class='v65-institution-trust'>{bullets}</div>
          </div>
          <div class='v65-institution-evidence'>
            <div class='v65-evidence-orbit'></div>
            <strong>LPQS</strong>
            <span>{escape(str(c['lpqs_label']))}</span>
          </div>
        </section>
        <span class='v65-institution-cta-marker'></span>
        """,
        unsafe_allow_html=True,
    )
    if st.button(
        str(c["institution_cta"]),
        key="v65_institution_cta",
        type="primary",
        use_container_width=False,
    ):
        router.navigate(router.route_key("public", "evaluator"))


def _footer(direction: str) -> None:
    c = copy()
    st.markdown(
        f"<footer class='v6-footer' dir='{direction}'><strong class='v601-footer-brand'>3alimn<span>IA</span></strong><span>{escape(str(c['footer']))}</span></footer>",
        unsafe_allow_html=True,
    )
