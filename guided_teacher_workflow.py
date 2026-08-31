"""Guided teacher workflow state for 3alimnIA V6.16.1.

This module keeps the project journey understandable without changing the
underlying V6.12-V6.16 research, evidence, blueprint, and block engines.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional



WORKFLOW_STEPS: List[Dict[str, str]] = [
    {"key": "setup", "section": "overview"},
    {"key": "resources", "section": "production"},
    {"key": "evidence", "section": "evidence"},
    {"key": "blueprint", "section": "blueprint"},
    {"key": "lessons", "section": "blocks"},
    {"key": "quality", "section": "assets"},
    {"key": "publish", "section": "publish"},
]


COPY: Dict[str, Dict[str, Any]] = {
    "ar": {
        "journey": "رحلة إنشاء المقرر",
        "journey_help": "أنجز المراحل بالترتيب. تُفتح كل مرحلة عندما تصبح مدخلاتها جاهزة.",
        "current_step": "الخطوة الحالية",
        "next_action": "متابعة العمل",
        "project_progress": "تقدم رحلة المشروع",
        "lesson_progress": "تقدم بناء الدروس",
        "advanced_nav": "الانتقال المتقدم بين الأقسام",
        "locked_help": "هذه المرحلة غير متاحة بعد؛ أكمل المرحلة السابقة أولًا.",
        "status": {
            "completed": "مكتملة",
            "in_progress": "قيد الإنجاز",
            "review": "معتمد للنشر",
            "available": "جاهزة للبدء",
            "locked": "غير متاحة",
        },
        "steps": {
            "setup": {
                "title": "إعداد المشروع",
                "short": "الإعداد",
                "description": "حدّد هوية المقرر، المتعلمين، المستوى، اللغات والمدة.",
                "outcome": "بيانات مشروع مكتملة وقابلة للاستعمال في جميع المراحل.",
                "action": "مراجعة إعداد المشروع",
            },
            "resources": {
                "title": "المراجع والبحث",
                "short": "المراجع",
                "description": "أضف ملفات الأستاذ وشغّل البحث عن مصادر وموارد تعليمية مناسبة.",
                "outcome": "حزمة مصادر قابلة للتقييم والاستعمال.",
                "action": "فتح مساحة المراجع والبحث",
            },
            "evidence": {
                "title": "تدقيق الأدلة",
                "short": "الأدلة",
                "description": "قيّم المصادر واستخرج بطاقات المعلومات والمفاهيم ثم اعتمدها.",
                "outcome": "حزمة أدلة معتمدة من الأستاذ.",
                "action": "مراجعة حزمة الأدلة",
            },
            "blueprint": {
                "title": "مخطط المقرر",
                "short": "المخطط",
                "description": "رتّب المفاهيم والوحدات والدروس والأهداف والأنشطة والتقويمات.",
                "outcome": "مخطط مقرر معتمد يوجّه عملية التوليد.",
                "action": "إنشاء أو مراجعة المخطط",
            },
            "lessons": {
                "title": "بناء الدروس",
                "short": "الدروس",
                "description": "أنشئ أجزاء كل درس بصورة مستقلة ثم راجعها واعتمدها.",
                "outcome": "دروس مكتملة من كتل تعليمية معتمدة.",
                "action": "متابعة بناء الدروس",
            },
            "quality": {
                "title": "المراجعة والجودة",
                "short": "الجودة",
                "description": "تحقق من الاكتمال والتسلسل والاستشهادات والمحاذاة والتكرار.",
                "outcome": "مقرر جاهز للمعاينة النهائية.",
                "action": "فحص الجودة والمخرجات",
            },
            "publish": {
                "title": "المعاينة والنشر",
                "short": "النشر",
                "description": "افحص الجاهزية، عاين تجربة المتعلم، اعتمد النسخة النهائية ثم انشرها.",
                "outcome": "مقرر منشور أو جاهز للنشر.",
                "action": "معاينة المقرر والنشر",
            },
        },
    },
    "fr": {
        "journey": "Parcours de création du cours",
        "journey_help": "Avancez dans l’ordre; chaque étape s’ouvre lorsque ses entrées sont prêtes.",
        "current_step": "Étape actuelle",
        "next_action": "Continuer",
        "project_progress": "Progression du projet",
        "lesson_progress": "Progression des leçons",
        "advanced_nav": "Navigation avancée",
        "locked_help": "Cette étape est verrouillée jusqu’à la fin de l’étape précédente.",
        "status": {"completed": "Terminée", "in_progress": "En cours", "review": "Validé pour publication", "available": "Prête", "locked": "Verrouillée"},
        "steps": {
            "setup": {"title": "Configurer le projet", "short": "Projet", "description": "Définissez le cours, le public, le niveau, les langues et la durée.", "outcome": "Fiche projet complète.", "action": "Vérifier le projet"},
            "resources": {"title": "Sources et recherche", "short": "Sources", "description": "Ajoutez les fichiers et recherchez des ressources pédagogiques.", "outcome": "Dossier de sources exploitable.", "action": "Ouvrir les sources"},
            "evidence": {"title": "Validation des preuves", "short": "Preuves", "description": "Évaluez les sources, extrayez les preuves et approuvez-les.", "outcome": "Dossier de preuves approuvé.", "action": "Réviser les preuves"},
            "blueprint": {"title": "Plan du cours", "short": "Plan", "description": "Organisez concepts, unités, leçons, objectifs, activités et évaluations.", "outcome": "Plan approuvé.", "action": "Créer ou réviser le plan"},
            "lessons": {"title": "Construire les leçons", "short": "Leçons", "description": "Générez et approuvez chaque bloc de leçon séparément.", "outcome": "Leçons complètes.", "action": "Continuer les leçons"},
            "quality": {"title": "Révision et qualité", "short": "Qualité", "description": "Contrôlez la cohérence, les citations, l’alignement et les répétitions.", "outcome": "Cours prêt pour l’aperçu.", "action": "Contrôler la qualité"},
            "publish": {"title": "Aperçu et publication", "short": "Publier", "description": "Vérifiez la préparation, prévisualisez, validez la version finale puis publiez.", "outcome": "Cours publié ou prêt.", "action": "Prévisualiser et publier"},
        },
    },
    "en": {
        "journey": "Course creation journey",
        "journey_help": "Complete the stages in order. Each stage unlocks when its inputs are ready.",
        "current_step": "Current step",
        "next_action": "Continue working",
        "project_progress": "Project journey progress",
        "lesson_progress": "Lesson-building progress",
        "advanced_nav": "Advanced section navigation",
        "locked_help": "This stage is locked until the previous stage is complete.",
        "status": {"completed": "Completed", "in_progress": "In progress", "review": "Approved to publish", "available": "Ready", "locked": "Locked"},
        "steps": {
            "setup": {"title": "Set up project", "short": "Setup", "description": "Define the course, learners, level, languages, and duration.", "outcome": "Complete project brief.", "action": "Review project setup"},
            "resources": {"title": "Sources and research", "short": "Sources", "description": "Add teacher files and search for suitable learning resources.", "outcome": "Usable research dossier.", "action": "Open sources and research"},
            "evidence": {"title": "Evidence review", "short": "Evidence", "description": "Score sources, extract evidence and concepts, then approve them.", "outcome": "Teacher-approved evidence bundle.", "action": "Review evidence bundle"},
            "blueprint": {"title": "Course blueprint", "short": "Blueprint", "description": "Organize concepts, units, lessons, outcomes, activities, and assessments.", "outcome": "Approved course blueprint.", "action": "Create or review blueprint"},
            "lessons": {"title": "Build lessons", "short": "Lessons", "description": "Generate, edit, and approve each lesson block independently.", "outcome": "Complete approved lessons.", "action": "Continue lesson building"},
            "quality": {"title": "Review and quality", "short": "Quality", "description": "Check completeness, citations, alignment, consistency, and duplication.", "outcome": "Course ready for final preview.", "action": "Review quality and outputs"},
            "publish": {"title": "Preview and publish", "short": "Publish", "description": "Check readiness, preview the learner experience, approve the final version, then publish.", "outcome": "Published or publication-ready course.", "action": "Preview and publish"},
        },
    },
}


def workflow_copy(language_code: str) -> Dict[str, Any]:
    return COPY.get(str(language_code or "en").lower(), COPY["en"])


def _usable_research(research_runs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [row for row in research_runs if str(row.get("status") or "") in {"completed", "needs_review"}]


def evaluate_workflow(
    project: Dict[str, Any],
    *,
    research_runs: Optional[Iterable[Dict[str, Any]]] = None,
    evidence: Optional[Dict[str, Any]] = None,
    blueprint: Optional[Dict[str, Any]] = None,
    lesson_progress: Optional[Dict[str, int]] = None,
    quality_ready: bool = False,
) -> Dict[str, Any]:
    """Evaluate one strict, teacher-approved seven-stage journey.

    V6.17.1 deliberately prevents later stages from becoming actionable while
    an earlier stage still needs review. This removes the former situation in
    which Sources and Evidence could both appear active at the same time.
    """
    research_rows = list(research_runs or [])
    lesson_progress = dict(lesson_progress or {})
    required_fields = ["project_name", "domain", "unit_title", "target_concept", "target_learners"]
    setup_complete = all(str(project.get(name) or "").strip() for name in required_fields)

    usable = _usable_research(research_rows)
    approved_research = [
        row for row in usable
        if int(row.get("approved_by_teacher") or 0) == 1
        and int(row.get("source_count") or 0) > 0
    ]
    has_reference_material = bool(str(project.get("source_material") or "").strip())

    evidence_exists = bool(evidence)
    evidence_approved = bool(evidence and int(evidence.get("approved_by_teacher") or 0) == 1)
    blueprint_exists = bool(blueprint)
    blueprint_approved = bool(blueprint and int(blueprint.get("approved_by_teacher") or 0) == 1)

    lesson_required = int(lesson_progress.get("required") or 0)
    lesson_available = int(lesson_progress.get("available") or 0)
    lesson_approved = int(lesson_progress.get("approved") or 0)
    lessons_complete = bool(lesson_required > 0 and lesson_approved >= lesson_required)

    statuses: Dict[str, str] = {}
    statuses["setup"] = "completed" if setup_complete else "in_progress"

    if not setup_complete:
        statuses["resources"] = "locked"
    elif approved_research:
        statuses["resources"] = "completed"
    elif usable:
        statuses["resources"] = "review"
    elif has_reference_material:
        statuses["resources"] = "in_progress"
    else:
        statuses["resources"] = "available"

    if statuses["resources"] != "completed":
        statuses["evidence"] = "locked"
    elif evidence_approved:
        statuses["evidence"] = "completed"
    elif evidence_exists:
        statuses["evidence"] = "review"
    else:
        statuses["evidence"] = "available"

    if statuses["evidence"] != "completed":
        statuses["blueprint"] = "locked"
    elif blueprint_approved:
        statuses["blueprint"] = "completed"
    elif blueprint_exists:
        statuses["blueprint"] = "review"
    else:
        statuses["blueprint"] = "available"

    if statuses["blueprint"] != "completed":
        statuses["lessons"] = "locked"
    elif lessons_complete:
        statuses["lessons"] = "completed"
    elif lesson_available > 0 or lesson_approved > 0:
        statuses["lessons"] = "in_progress"
    else:
        statuses["lessons"] = "available"

    if statuses["lessons"] != "completed":
        statuses["quality"] = "locked"
    elif quality_ready:
        statuses["quality"] = "completed"
    else:
        statuses["quality"] = "available"

    project_status = str(project.get("status") or "draft").lower()
    if statuses["quality"] != "completed":
        statuses["publish"] = "locked"
    elif project_status == "published":
        statuses["publish"] = "completed"
    elif project_status == "review":
        statuses["publish"] = "review"
    else:
        statuses["publish"] = "available"

    current_key = "publish"
    for step in WORKFLOW_STEPS:
        if statuses[step["key"]] != "completed":
            current_key = step["key"]
            break

    completed_count = sum(1 for value in statuses.values() if value == "completed")
    requirements = {
        "setup": ["complete_project_brief"],
        "resources": ["run_research", "approve_research"],
        "evidence": ["build_evidence", "approve_evidence"],
        "blueprint": ["build_blueprint", "approve_blueprint"],
        "lessons": ["generate_blocks", "approve_required_blocks"],
        "quality": ["pass_quality_gate"],
        "publish": ["preview_course", "publish_course"],
    }
    return {
        "statuses": statuses,
        "current_key": current_key,
        "completed_count": completed_count,
        "total_steps": len(WORKFLOW_STEPS),
        "progress_pct": int(round(100 * completed_count / len(WORKFLOW_STEPS))),
        "requirements": requirements.get(current_key, []),
        "lesson_progress": {
            "required": lesson_required,
            "available": lesson_available,
            "approved": lesson_approved,
            "complete": lessons_complete,
        },
    }

def load_workflow_state(project: Dict[str, Any]) -> Dict[str, Any]:
    import db
    import lesson_block_generation_engine
    project_id = int(project.get("id") or 0)
    research_df = db.teacher_research_runs_df(project_id, phase_number=1)
    research_runs = research_df.to_dict("records") if hasattr(research_df, "to_dict") else []
    evidence = db.latest_teacher_evidence(project_id, 1, approved_only=False)
    blueprint = db.latest_teacher_blueprint(project_id, approved_only=False)
    approved_blueprint = db.latest_teacher_blueprint(project_id, approved_only=True)

    lesson_required = 0
    lesson_available = 0
    lesson_approved = 0
    if approved_blueprint:
        lessons = list((approved_blueprint.get("blueprint") or {}).get("lessons") or [])
        for lesson in lessons:
            lesson_id = str(lesson.get("lesson_id") or "")
            if not lesson_id:
                continue
            progress = lesson_block_generation_engine.lesson_completion(project_id, lesson_id)
            lesson_required += int(progress.get("required") or 0)
            lesson_available += int(progress.get("available") or 0)
            lesson_approved += int(progress.get("approved") or 0)

    outputs = db.teacher_project_phase_outputs(project_id)
    phase_11 = outputs.get(11) or {}
    phase_quality_ready = str(phase_11.get("status") or "") == "completed"
    all_lessons_complete = bool(lesson_required > 0 and lesson_approved >= lesson_required)
    quality_ready = phase_quality_ready or (all_lessons_complete and str(project.get("status") or "").lower() in {"review", "published"})

    return evaluate_workflow(
        project,
        research_runs=research_runs,
        evidence=evidence,
        blueprint=blueprint,
        lesson_progress={"required": lesson_required, "available": lesson_available, "approved": lesson_approved},
        quality_ready=quality_ready,
    )


def section_for_step(step_key: str) -> str:
    for step in WORKFLOW_STEPS:
        if step["key"] == step_key:
            return step["section"]
    return "overview"


def step_for_section(section: str) -> str:
    for step in WORKFLOW_STEPS:
        if step["section"] == section:
            return step["key"]
    return "setup"
