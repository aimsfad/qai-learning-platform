"""Simplified five-stage teacher journey for 3alimnIA V6.18.4.

The production engines keep their detailed seven-stage state internally. This
module groups that state into five teacher-facing decisions so the default UI
shows the pedagogical workflow rather than the implementation workflow.
"""
from __future__ import annotations

from typing import Any, Dict, List


SIMPLE_STEPS: List[Dict[str, str]] = [
    {"key": "setup", "section": "overview"},
    {"key": "sources", "section": "sources"},
    {"key": "plan", "section": "blueprint"},
    {"key": "lessons", "section": "lessons"},
    {"key": "review", "section": "review"},
]


COPY: Dict[str, Dict[str, Any]] = {
    "ar": {
        "title": "إنشاء المقرر في خمس خطوات",
        "help": "نفّذي الإجراء الرئيسي الظاهر في الشاشة، وستفتح الخطوة التالية تلقائيًا بعد الاعتماد.",
        "continue": "متابعة من حيث توقفت",
        "advanced": "الوضع المتقدم",
        "simple": "الوضع المبسط",
        "steps": {
            "setup": {"short": "إعداد المقرر", "title": "إعداد المقرر", "description": "حددي هوية المقرر ومستواه ومدته ولغته وطريقة تدريسه."},
            "sources": {"short": "مصادر المقرر", "title": "إضافة المصادر والتحقق منها", "description": "ارفعي الملفات أو شغلي البحث، ثم راجعي المصادر واعتمديها."},
            "plan": {"short": "خطة المقرر", "title": "مراجعة خطة المقرر", "description": "راجعي الوحدات والدروس، عدّليها عند الحاجة، ثم اعتمدي الخطة."},
            "lessons": {"short": "إنشاء الدروس", "title": "إنشاء الدروس", "description": "أنشئي كل درس كاملًا، راجعي أقسامه، ثم اعتمديه وانتقلي إلى التالي."},
            "review": {"short": "المراجعة والاعتماد والنشر", "title": "المراجعة والاعتماد والنشر", "description": "افحصي الجاهزية، راجعي الدروس والمصادر، عايني نسخة المتعلم، ثم اعتمدي النسخة النهائية وانشريها."},
        },
        "status": {"completed": "مكتملة", "in_progress": "قيد الإنجاز", "review": "معتمد للنشر", "available": "جاهزة", "locked": "غير متاحة"},
    },
    "fr": {
        "title": "Créer le cours en cinq étapes",
        "help": "Effectuez l’action principale affichée; l’étape suivante s’ouvrira automatiquement après validation.",
        "continue": "Reprendre où vous vous êtes arrêté",
        "advanced": "Mode avancé",
        "simple": "Mode simplifié",
        "steps": {
            "setup": {"short": "Configurer", "title": "Configurer le cours", "description": "Définissez l’identité, le niveau, la durée, la langue et la pédagogie."},
            "sources": {"short": "Sources", "title": "Ajouter et vérifier les sources", "description": "Ajoutez les fichiers ou lancez la recherche, puis approuvez les sources."},
            "plan": {"short": "Plan", "title": "Valider le plan du cours", "description": "Révisez les unités et les leçons, puis approuvez le plan."},
            "lessons": {"short": "Leçons", "title": "Créer les leçons", "description": "Générez chaque leçon complète, révisez-la et approuvez-la."},
            "review": {"short": "Réviser, valider et publier", "title": "Réviser, valider et publier", "description": "Vérifiez la préparation, révisez, prévisualisez, validez la version finale puis publiez."},
        },
        "status": {"completed": "Terminée", "in_progress": "En cours", "review": "Validé pour publication", "available": "Prête", "locked": "Verrouillée"},
    },
    "en": {
        "title": "Create the course in five steps",
        "help": "Complete the main action shown on screen. The next step opens automatically after approval.",
        "continue": "Continue where you left off",
        "advanced": "Advanced mode",
        "simple": "Simple mode",
        "steps": {
            "setup": {"short": "Course setup", "title": "Set up the course", "description": "Define the course identity, level, duration, language, and teaching approach."},
            "sources": {"short": "Course sources", "title": "Add and verify sources", "description": "Upload files or run research, then review and approve the sources."},
            "plan": {"short": "Course plan", "title": "Review the course plan", "description": "Review units and lessons, edit if needed, then approve the plan."},
            "lessons": {"short": "Create lessons", "title": "Create lessons", "description": "Generate each complete lesson, review its sections, then approve it."},
            "review": {"short": "Review, approve & publish", "title": "Review, approve and publish", "description": "Check readiness, review lessons and sources, preview the learner view, approve the final version, then publish."},
        },
        "status": {"completed": "Completed", "in_progress": "In progress", "review": "Approved to publish", "available": "Ready", "locked": "Locked"},
    },
}


def copy(language_code: str) -> Dict[str, Any]:
    return COPY.get(str(language_code or "en").lower(), COPY["en"])


def _combined_sources_status(statuses: Dict[str, str]) -> str:
    resources = str(statuses.get("resources") or "locked")
    evidence = str(statuses.get("evidence") or "locked")
    if resources == "completed" and evidence == "completed":
        return "completed"
    if resources == "locked":
        return "locked"
    if resources != "completed":
        return resources
    # Research is approved; evidence is now the active substep.
    return evidence if evidence != "locked" else "available"


def _combined_review_status(statuses: Dict[str, str]) -> str:
    quality = str(statuses.get("quality") or "locked")
    publish = str(statuses.get("publish") or "locked")
    if publish == "completed":
        return "completed"
    if quality == "locked":
        return "locked"
    if quality != "completed":
        return quality
    return publish if publish != "locked" else "available"


def build_simple_state(base_state: Dict[str, Any]) -> Dict[str, Any]:
    base_statuses = dict(base_state.get("statuses") or {})
    statuses = {
        "setup": str(base_statuses.get("setup") or "in_progress"),
        "sources": _combined_sources_status(base_statuses),
        "plan": str(base_statuses.get("blueprint") or "locked"),
        "lessons": str(base_statuses.get("lessons") or "locked"),
        "review": _combined_review_status(base_statuses),
    }
    current_key = "review"
    for step in SIMPLE_STEPS:
        if statuses.get(step["key"]) != "completed":
            current_key = step["key"]
            break
    completed = sum(1 for value in statuses.values() if value == "completed")
    return {
        "statuses": statuses,
        "current_key": current_key,
        "completed_count": completed,
        "total_steps": len(SIMPLE_STEPS),
        "progress_pct": int(round(100 * completed / max(len(SIMPLE_STEPS), 1))),
        "lesson_progress": dict(base_state.get("lesson_progress") or {}),
        "base_state": base_state,
    }


def source_substep(base_state: Dict[str, Any]) -> str:
    statuses = dict(base_state.get("statuses") or {})
    if str(statuses.get("resources") or "") != "completed":
        return "research"
    if str(statuses.get("evidence") or "") != "completed":
        return "evidence"
    return "complete"


def review_substep(base_state: Dict[str, Any]) -> str:
    statuses = dict(base_state.get("statuses") or {})
    if str(statuses.get("quality") or "") != "completed":
        return "quality"
    return "publish"
