from __future__ import annotations

import base64
from functools import lru_cache
from html import escape
from pathlib import Path
from textwrap import dedent
from typing import Dict

BRAND_NAME = "3alimnIA"
# Backward-compatible alias used by older UI components.
BRAND_NAME_LATIN = BRAND_NAME
BRAND_NAME_AR = "علّمنيا"
BRAND_TAGLINE_EN = "Difficult concepts, guided by generative AI."
BRAND_TAGLINE_AR = "نفهم المفاهيم الصعبة خطوة بخطوة بالذكاء التوليدي."
BRAND_TAGLINE_FR = "Comprendre les concepts difficiles, pas à pas, avec l'IA générative."
DEFAULT_LOGO_VARIANT = "official"

ASSET_DIR = Path(__file__).resolve().parent / "assets" / "branding"
OFFICIAL_LOGO_PATH = ASSET_DIR / "3alimnia_logo.png"
HEADER_WHITE_LOGO_PATH = ASSET_DIR / "3alimnia_header_logo_white.png"

LANGUAGES: Dict[str, str] = {
    "العربية": "ar",
    "Français": "fr",
    "English": "en",
}

TRACKS = {
    "quantum": {
        "icon": "Q",
        "accent": "quantum",
        "status": {"ar": "متاح الآن", "fr": "Disponible", "en": "Available now"},
        "name": {"ar": "الحوسبة الكمية", "fr": "Informatique quantique", "en": "Quantum Computing"},
        "short_name": {"ar": "مسار الكوانتوم", "fr": "Parcours Quantum", "en": "Quantum Path"},
        "description": {
            "ar": "تعلّم الكيوبت، القياس، التراكب، التشابك، وبرمجة Qiskit عبر مسار مرئي وتطبيقي.",
            "fr": "Apprenez les qubits, la mesure, la superposition, l'intrication et Qiskit grâce à un parcours visuel et pratique.",
            "en": "Learn qubits, measurement, superposition, entanglement, and Qiskit through a visual, practice-based path.",
        },
        "audience": {
            "ar": "للمبتدئين وطلبة الإعلام الآلي والهندسة",
            "fr": "Débutants et étudiants en informatique / ingénierie",
            "en": "Beginners and computing or engineering students",
        },
    },
    "ml": {
        "icon": "ML",
        "accent": "ml",
        "status": {"ar": "قريبًا", "fr": "Bientôt", "en": "Coming soon"},
        "name": {"ar": "تعلّم الآلة", "fr": "Machine Learning", "en": "Machine Learning"},
        "short_name": {"ar": "مسار تعلّم الآلة", "fr": "Parcours ML", "en": "ML Path"},
        "description": {
            "ar": "افهم النماذج والبيانات والتدريب والتقييم من خلال تجارب صغيرة وتفسير بصري للأخطاء والنتائج.",
            "fr": "Comprenez les modèles, les données, l'entraînement et l'évaluation grâce à des expériences guidées et visuelles.",
            "en": "Understand models, data, training, and evaluation through small experiments and visual error analysis.",
        },
        "audience": {
            "ar": "للطلبة والمبتدئين في الذكاء الاصطناعي",
            "fr": "Étudiants et débutants en IA appliquée",
            "en": "Students starting applied AI",
        },
    },
    "ai": {
        "icon": "AI",
        "accent": "ai",
        "status": {"ar": "قريبًا", "fr": "Bientôt", "en": "Coming soon"},
        "name": {"ar": "أساسيات الذكاء الاصطناعي", "fr": "Fondements de l'IA", "en": "AI Foundations"},
        "short_name": {"ar": "مسار الذكاء الاصطناعي", "fr": "Parcours IA", "en": "AI Foundations"},
        "description": {
            "ar": "اربط بين البحث والاستدلال والتمثيل والشبكات العصبية والذكاء الاصطناعي المسؤول بدل حفظ تعريفات منفصلة.",
            "fr": "Reliez recherche, raisonnement, représentation, réseaux neuronaux et IA responsable dans un parcours cohérent.",
            "en": "Connect search, reasoning, representation, neural networks, and responsible AI in one coherent journey.",
        },
        "audience": {
            "ar": "لكل من يريد فهم الذكاء الاصطناعي بعمق",
            "fr": "Pour comprendre l'IA au-delà des définitions",
            "en": "For learners who want more than definitions",
        },
    },
}

TEXT = {
    "ar": {
        "direction": "rtl",
        "eyebrow": "منصة تعليمية مدعومة بالذكاء التوليدي",
        "headline": "من المفهوم الصعب إلى فهم واضح وتطبيق حقيقي.",
        "subheadline": "اختر مسارك، جرّب الفكرة بنفسك، شاهدها بصريًا، ثم استخدم مدرّب الذكاء الاصطناعي للحصول على تلميح موجّه بدل جواب جاهز.",
        "badges": ["شرح بصري", "تعلّم تطبيقي", "مدرّب AI مقيّد تربويًا", "تحليلات تعلّم"],
        "paths_kicker": "المسارات التعليمية",
        "paths_title": "ماذا تريد أن تتعلّم اليوم؟",
        "paths_body": "تنطلق المنصة بمسار الكوانتوم، ثم تتوسع تدريجيًا إلى تعلّم الآلة وأساسيات الذكاء الاصطناعي ضمن نفس المحرك التربوي.",
        "start_quantum": "ابدأ مسار الكوانتوم",
        "preview_ml": "استكشف المسار القادم",
        "preview_ai": "استكشف المسار القادم",
        "roadmap": "قيد التطوير",
        "roadmap_title": "هذا المسار ظاهر في المنتج، لكنه لن يُفتح قبل اكتمال محتواه التعليمي.",
        "roadmap_body": "سيُبنى كل مسار من وحدات قصيرة، محاكاة بصرية، محاولة أولى من المتعلم، دعم توليدي موجّه، وتقويم يثبت الفهم.",
        "roadmap_steps": ["خريطة المفاهيم", "دروس مرئية قصيرة", "محاولة المتعلم أولًا", "دعم توليدي موجّه", "دليل الإتقان"],
        "how_kicker": "كيف تعمل علّمنيا؟",
        "how_title": "الذكاء التوليدي يساند التفكير ولا يستبدله",
        "steps": [
            ("01", "ألاحظ وأجرّب", "يشاهد المتعلم شرحًا بصريًا، يغيّر مدخلات المحاكاة، ثم يكتب توقعه أو محاولته الأولى."),
            ("02", "أطلب تلميحًا ذكيًا", "يقدّم المدرّب تشخيصًا، مثالًا، سؤالًا موجّهًا، أو خطوة تالية من دون إعطاء الحل النهائي مباشرة."),
            ("03", "أبرهن أنني فهمت", "تُسجّل المهام والاختبارات والتأملات والتفاعلات لتكوين دليل حقيقي على التقدّم."),
        ],
        "research_kicker": "للجامعات والباحثين",
        "research_title": "منصة تعلّم وأداة تقييم علمي في الوقت نفسه",
        "research_body": "يمكن للمقيّمين متابعة التقدّم، مراجعة تفاعلات الذكاء الاصطناعي، تطبيق LPQS، وتصدير بيانات مجهولة الهوية للبحث والتطوير.",
        "evaluator_button": "دخول فضاء المقيّم والباحث",
        "language_label": "اللغة",
        "nav_caption": "مسارات واضحة لفهم المفاهيم الصعبة.",
    },
    "fr": {
        "direction": "ltr",
        "eyebrow": "PLATEFORME D'APPRENTISSAGE ASSISTÉE PAR IA GÉNÉRATIVE",
        "headline": "Des concepts difficiles à une compréhension claire et applicable.",
        "subheadline": "Choisissez un parcours, tentez d'abord, explorez visuellement, puis demandez à l'AI Coach un indice guidé plutôt qu'une réponse toute faite.",
        "badges": ["Explications visuelles", "Apprentissage pratique", "Coach IA contraint", "Learning analytics"],
        "paths_kicker": "PARCOURS D'APPRENTISSAGE",
        "paths_title": "Que souhaitez-vous apprendre aujourd'hui ?",
        "paths_body": "La plateforme démarre avec le parcours quantique, puis s'étend progressivement au Machine Learning et aux fondements de l'IA.",
        "start_quantum": "Commencer le parcours Quantum",
        "preview_ml": "Découvrir le prochain parcours",
        "preview_ai": "Découvrir le prochain parcours",
        "roadmap": "EN DÉVELOPPEMENT",
        "roadmap_title": "Le parcours est visible dans le produit, mais restera fermé jusqu'à validation de son contenu pédagogique.",
        "roadmap_body": "Chaque parcours comprendra des micro-modules, des simulations, une tentative apprenant-first, un soutien génératif guidé et des preuves de maîtrise.",
        "roadmap_steps": ["Carte des concepts", "Micro-leçons visuelles", "Tentative apprenant-first", "Soutien GenAI", "Preuve de maîtrise"],
        "how_kicker": "COMMENT FONCTIONNE 3alimnIA ?",
        "how_title": "L'IA générative soutient le raisonnement sans le remplacer",
        "steps": [
            ("01", "Observer et tenter", "L'apprenant explore une explication ou une simulation, puis formule une prédiction ou une première réponse."),
            ("02", "Demander un indice", "Le coach propose un diagnostic, une analogie, une question ou l'étape suivante sans livrer immédiatement la solution."),
            ("03", "Démontrer la maîtrise", "Tâches, tests, réflexions et traces d'interaction produisent des preuves de progression."),
        ],
        "research_kicker": "UNIVERSITÉS ET RECHERCHE",
        "research_title": "Une plateforme d'apprentissage et un instrument scientifique",
        "research_body": "Les évaluateurs suivent la progression, examinent les interactions IA, appliquent le LPQS et exportent des données anonymisées.",
        "evaluator_button": "Ouvrir l'espace évaluateur",
        "language_label": "Langue",
        "nav_caption": "Des parcours clairs pour maîtriser les concepts difficiles.",
    },
    "en": {
        "direction": "ltr",
        "eyebrow": "GENERATIVE-AI LEARNING PLATFORM",
        "headline": "From difficult concepts to clear, applicable understanding.",
        "subheadline": "Choose a path, attempt first, explore visually, and ask the AI Coach for a guided scaffold rather than a ready-made answer.",
        "badges": ["Visual explanations", "Practice-based learning", "Constrained AI Coach", "Learning analytics"],
        "paths_kicker": "LEARNING PATHS",
        "paths_title": "What do you want to learn today?",
        "paths_body": "The platform launches with Quantum Computing, then expands to Machine Learning and AI Foundations through the same pedagogical engine.",
        "start_quantum": "Start Quantum Path",
        "preview_ml": "Preview upcoming path",
        "preview_ai": "Preview upcoming path",
        "roadmap": "IN DEVELOPMENT",
        "roadmap_title": "This path is visible in the product, but remains locked until its curriculum is complete.",
        "roadmap_body": "Each path will combine micro-modules, visual simulations, a learner-first attempt, guided GenAI support, and mastery evidence.",
        "roadmap_steps": ["Concept map", "Visual micro-lessons", "Learner-first attempt", "GenAI scaffold", "Mastery evidence"],
        "how_kicker": "HOW 3alimnIA WORKS",
        "how_title": "Generative AI supports reasoning instead of replacing it",
        "steps": [
            ("01", "Observe and attempt", "The learner explores an explanation or simulation, then makes a prediction or first attempt."),
            ("02", "Request a scaffold", "The coach offers a diagnosis, analogy, question, or next step without immediately giving the final answer."),
            ("03", "Demonstrate mastery", "Tasks, tests, reflections, and interaction traces provide evidence of progress."),
        ],
        "research_kicker": "FOR UNIVERSITIES & RESEARCHERS",
        "research_title": "A learning platform and a scientific evaluation instrument",
        "research_body": "Evaluators monitor progress, review AI interactions, apply LPQS, and export anonymized evidence.",
        "evaluator_button": "Open evaluator workspace",
        "language_label": "Language",
        "nav_caption": "Clear paths through difficult concepts.",
    },
}


def lang_code(language_label: str | None) -> str:
    return LANGUAGES.get(language_label or "العربية", "ar")


@lru_cache(maxsize=1)
def official_logo_data_uri() -> str:
    if not OFFICIAL_LOGO_PATH.exists():
        return ""
    payload = base64.b64encode(OFFICIAL_LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{payload}"


def _fallback_mark_svg(size: int = 66) -> str:
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 72 72" role="img" aria-label="{escape(BRAND_NAME)} logo" xmlns="http://www.w3.org/2000/svg">
      <defs><linearGradient id="brandOrbit" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0A2A78"/><stop offset=".62" stop-color="#1066D9"/><stop offset="1" stop-color="#12C8E6"/></linearGradient></defs>
      <path d="M46 14c-10-6-24-2-29 8-6 12 1 27 14 31 7 2 14 0 19-4" fill="none" stroke="#0A2A78" stroke-width="9" stroke-linecap="round"/>
      <ellipse cx="36" cy="36" rx="29" ry="12" fill="none" stroke="url(#brandOrbit)" stroke-width="4" transform="rotate(-28 36 36)"/>
      <circle cx="58" cy="20" r="4" fill="#18C9E6"/><circle cx="17" cy="53" r="4" fill="#1269D6"/>
    </svg>"""


def logo_lockup_html(compact: bool = False, language: str = "ar") -> str:
    """Return the approved official 3alimnIA logo as an embedded image.

    The image is embedded as a data URI so Streamlit Cloud does not depend on
    a browser-accessible local file path. The visual identity remains exactly
    the approved blue/cyan/gold horizontal logo.
    """
    data_uri = official_logo_data_uri()
    compact_class = " brand-compact" if compact else ""
    if data_uri:
        mark = (
            f"<img class='brand-approved-logo-img' src='{data_uri}' "
            f"alt='{escape(BRAND_NAME)} - {escape(BRAND_NAME_AR)}'/>"
        )
    else:
        mark = _fallback_mark_svg(44 if compact else 68)
    return dedent(
        f"""
        <div class='brand-lockup brand-approved-lockup{compact_class}' dir='ltr'>
          <div class='brand-official-logo'>{mark}</div>
        </div>
        """
    ).strip()

def hero_copy_html(language: str = "ar") -> str:
    t = TEXT[language]
    badge_html = "".join(f"<span>{escape(item)}</span>" for item in t["badges"])
    return dedent(
        f"""
        <div class='brand-hero-copy v4-hero-copy' dir='{t['direction']}'>
          <div class='brand-eyebrow'>{escape(t['eyebrow'])}</div>
          <h1>{escape(t['headline'])}</h1>
          <p>{escape(t['subheadline'])}</p>
          <div class='brand-hero-badges'>{badge_html}</div>
        </div>
        """
    ).strip()


def hero_visual_html(language: str = "ar") -> str:
    labels = {
        "ar": ("كوانتوم", "ML", "AI", "تعلّم"),
        "fr": ("Quantum", "ML", "IA", "Apprendre"),
        "en": ("Quantum", "ML", "AI", "Learn"),
    }[language]
    return dedent(
        f"""
        <div class='brand-hero-visual v4-hero-visual' aria-hidden='true' dir='ltr'>
          <div class='v4-visual-grid'></div>
          <div class='brand-visual-orbit orbit-one'></div>
          <div class='brand-visual-orbit orbit-two'></div>
          <div class='v4-orbit-dot dot-one'></div><div class='v4-orbit-dot dot-two'></div><div class='v4-orbit-dot dot-three'></div>
          <div class='brand-visual-core'><span>AI</span><b>{escape(labels[3])}</b></div>
          <div class='brand-visual-node node-q'>{escape(labels[0])}</div>
          <div class='brand-visual-node node-ml'>{escape(labels[1])}</div>
          <div class='brand-visual-node node-ai'>{escape(labels[2])}</div>
        </div>
        """
    ).strip()


def landing_hero_html(language: str = "ar") -> str:
    """Backward-compatible non-widget hero used by old previews."""
    t = TEXT[language]
    return f"<section class='brand-landing-hero' dir='{t['direction']}'>{hero_copy_html(language)}{hero_visual_html(language)}</section>"


def section_heading_html(kicker: str, title: str, body: str, language: str = "ar", extra_class: str = "") -> str:
    direction = TEXT[language]["direction"]
    body_html = f"<p>{escape(body)}</p>" if body else ""
    return f"<div class='brand-section-heading {escape(extra_class)}' dir='{direction}'><span>{escape(kicker)}</span><h2>{escape(title)}</h2>{body_html}</div>"


def preview_panel_html(track: Dict[str, object], language: str = "ar") -> str:
    t = TEXT[language]
    steps = "".join(f"<span>{index}. {escape(step)}</span>" for index, step in enumerate(t["roadmap_steps"], start=1))
    return dedent(
        f"""
        <div class='brand-preview-panel' dir='{t['direction']}'>
          <div><span class='brand-preview-label'>{escape(t['roadmap'])}</span><h3>{escape(track['short_name'][language])}</h3><h4>{escape(t['roadmap_title'])}</h4><p>{escape(t['roadmap_body'])}</p></div>
          <div class='brand-preview-steps'>{steps}</div>
        </div>
        """
    ).strip()


def how_grid_html(language: str = "ar") -> str:
    t = TEXT[language]
    cards = "".join(f"<article class='brand-how-card'><div class='brand-how-number'>{escape(num)}</div><h3>{escape(title)}</h3><p>{escape(body)}</p></article>" for num, title, body in t["steps"])
    return f"<div class='brand-how-grid' dir='{t['direction']}'>{cards}</div>"


def research_strip_html(language: str = "ar") -> str:
    t = TEXT[language]
    return dedent(
        f"""
        <section class='brand-research-strip' dir='{t['direction']}'>
          <div class='v4-research-icon'>LPQS</div>
          <div><span class='brand-preview-label'>{escape(t['research_kicker'])}</span><h3>{escape(t['research_title'])}</h3><p>{escape(t['research_body'])}</p></div>
        </section>
        """
    ).strip()


def track_card_html(track_id: str, language: str = "ar", selected: bool = False) -> str:
    track = TRACKS[track_id]
    selected_class = " brand-track-selected" if selected else ""
    return (
        f"<article class='brand-track-card brand-accent-{escape(track['accent'])}{selected_class}' dir='{TEXT[language]['direction']}'>"
        "<div class='brand-track-topline'>"
        f"<span class='brand-track-icon'>{escape(track['icon'])}</span>"
        f"<span class='brand-track-status'>{escape(track['status'][language])}</span>"
        "</div>"
        f"<h3>{escape(track['name'][language])}</h3>"
        f"<p>{escape(track['description'][language])}</p>"
        f"<div class='brand-track-audience'>{escape(track['audience'][language])}</div>"
        "</article>"
    )

def sidebar_brand_html(language: str = "ar") -> str:
    return logo_lockup_html(compact=True, language=language)
