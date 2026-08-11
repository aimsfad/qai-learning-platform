"""Deterministic pedagogical quality gate for generated lessons.

V6.19.0 adds a transparent, inspectable quality layer above block validation.
The gate is intentionally deterministic: it does not ask an LLM to grade its
own lesson.  It aggregates structural evidence already present in the approved
blueprint and generated lesson sections, highlights missing learning-design
moves, and preserves the teacher as the final pedagogical decision maker.

The numeric score is advisory. Only structural/integrity blockers prevent
approval. Pedagogical weaknesses are surfaced as review items so a teacher can
accept, revise, or regenerate deliberately.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping

import lesson_content_renderer


DIMENSIONS: List[Dict[str, Any]] = [
    {"key": "alignment", "weight": 0.16, "ar": "المحاذاة مع الأهداف", "fr": "Alignement des objectifs", "en": "Outcome alignment"},
    {"key": "learner_activation", "weight": 0.12, "ar": "فاعلية المتعلم", "fr": "Activation de l'apprenant", "en": "Learner activation"},
    {"key": "scaffolding", "weight": 0.16, "ar": "التدرج في الدعم", "fr": "Étayage progressif", "en": "Scaffolding"},
    {"key": "practice_transfer", "weight": 0.12, "ar": "الممارسة والنقل", "fr": "Pratique et transfert", "en": "Practice and transfer"},
    {"key": "assessment_feedback", "weight": 0.16, "ar": "التقويم والتغذية الراجعة", "fr": "Évaluation et feedback", "en": "Assessment and feedback"},
    {"key": "misconception_repair", "weight": 0.10, "ar": "تشخيص التصورات الخاطئة", "fr": "Correction des conceptions erronées", "en": "Misconception repair"},
    {"key": "metacognition", "weight": 0.08, "ar": "ما وراء المعرفة", "fr": "Métacognition", "en": "Metacognition"},
    {"key": "representation_access", "weight": 0.10, "ar": "تنوع التمثيل والتفاعل", "fr": "Variété de représentation", "en": "Representation and access"},
]

REQUIRED_BLOCKS = (
    "activation",
    "explanation",
    "worked_example",
    "guided_practice",
    "independent_practice",
    "misconceptions",
    "formative_assessment",
    "summary",
    "resources",
)


def _lang(language_code: str) -> str:
    value = str(language_code or "en").lower()
    if value.startswith("ar"):
        return "ar"
    if value.startswith("fr"):
        return "fr"
    return "en"


def _row_map(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
    return {str(row.get("block_type") or ""): row for row in rows if str(row.get("block_type") or "")}


def _text(row: Mapping[str, Any] | None) -> str:
    if not row:
        return ""
    return str(row.get("content_text") or "")


def _lower(value: str) -> str:
    return str(value or "").casefold()


def _has_any(text: str, tokens: Iterable[str]) -> bool:
    low = _lower(text)
    return any(_lower(token) in low for token in tokens)


def _ratio(*checks: bool) -> float:
    if not checks:
        return 0.0
    return sum(1 for check in checks if check) / len(checks)


def _strip_fenced_code(text: str) -> str:
    return re.sub(r"```.*?```", "", str(text or ""), flags=re.DOTALL)


def _unsafe_html(text: str) -> bool:
    prose = _strip_fenced_code(text)
    return bool(re.search(r"<\s*(script|iframe|object|embed|form|style)\b", prose, flags=re.IGNORECASE))


def _validation(row: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not row:
        return {}
    value = row.get("validation")
    if not isinstance(value, Mapping):
        run = row.get("run")
        if isinstance(run, Mapping):
            value = run.get("validation")
    return dict(value) if isinstance(value, Mapping) else {}


def dimension_label(key: str, language_code: str = "ar") -> str:
    lang = _lang(language_code)
    item = next((item for item in DIMENSIONS if item["key"] == key), None)
    return str((item or {}).get(lang) or (item or {}).get("en") or key)


def issue_label(code: str, language_code: str = "ar") -> str:
    lang = _lang(language_code)
    labels = {
        "ar": {
            "missing_lesson_section": "قسم مطلوب من الدرس غير موجود.",
            "block_validation_error": "يوجد خطأ بنيوي أو تقني في أحد أقسام الدرس.",
            "unsafe_html_detected": "يوجد HTML غير آمن داخل محتوى مولّد.",
            "outcomes_missing": "لا توجد أهداف تعلم صريحة مرتبطة بالدرس.",
            "source_traceability_weak": "الدرس مرتبط بمصادر معتمدة لكن الاستشهاد بها ضعيف داخل المسودة.",
            "activation_weak": "تنشيط المعارف السابقة يحتاج استرجاعًا أو سؤالًا تشخيصيًا أوضح.",
            "scaffolding_weak": "تدرج الدعم بين المثال والتدريب الموجّه والاستقلالي يحتاج تحسينًا.",
            "transfer_weak": "المسودة تحتاج مهمة نقل أو تطبيق جديد بعد المثال.",
            "assessment_weak": "التقويم يحتاج معيار نجاح وتغذية راجعة وقاعدة قرار تعليمية أوضح.",
            "misconception_weak": "قسم التصورات الخاطئة يحتاج تشخيصًا وتصحيحًا وفحصًا فارقًا أوضح.",
            "metacognition_weak": "الملخص يحتاج سؤال تأمل أو تخطيط للمراجعة التالية.",
            "representation_weak": "المسودة تعتمد نمط عرض واحدًا تقريبًا؛ أضف تمثيلًا أو طريقة استجابة بديلة عند ملاءمتها.",
        },
        "fr": {
            "missing_lesson_section": "Une section obligatoire de la leçon est absente.",
            "block_validation_error": "Une section contient une erreur structurelle ou technique.",
            "unsafe_html_detected": "Du HTML non sûr apparaît dans le contenu généré.",
            "outcomes_missing": "Aucun objectif d’apprentissage explicite n’est relié à la leçon.",
            "source_traceability_weak": "La leçon a des sources approuvées mais leur traçabilité est faible dans le brouillon.",
            "activation_weak": "L’activation des acquis devrait mieux solliciter le rappel ou le diagnostic.",
            "scaffolding_weak": "La progression exemple guidé → pratique guidée → autonomie doit être renforcée.",
            "transfer_weak": "Ajoutez une tâche de transfert ou une nouvelle application après l’exemple.",
            "assessment_weak": "L’évaluation doit mieux expliciter le critère de réussite, le feedback et la décision pédagogique.",
            "misconception_weak": "Le diagnostic et la correction des conceptions erronées doivent être plus explicites.",
            "metacognition_weak": "Le résumé devrait inclure une réflexion ou une prochaine stratégie d’étude.",
            "representation_weak": "Le brouillon utilise presque un seul mode de représentation; ajoutez une alternative pertinente.",
        },
        "en": {
            "missing_lesson_section": "A required lesson section is missing.",
            "block_validation_error": "A lesson section has a structural or technical validation error.",
            "unsafe_html_detected": "Unsafe HTML appears in generated content.",
            "outcomes_missing": "No explicit learning outcomes are linked to this lesson.",
            "source_traceability_weak": "Approved sources exist but in-draft traceability is weak.",
            "activation_weak": "Prior-knowledge activation needs a clearer retrieval or diagnostic prompt.",
            "scaffolding_weak": "The worked → guided → independent support progression needs strengthening.",
            "transfer_weak": "Add a transfer task or fresh application after modelling.",
            "assessment_weak": "Assessment needs a clearer success criterion, actionable feedback, and instructional decision rule.",
            "misconception_weak": "Misconception diagnosis, correction, and discriminating check need strengthening.",
            "metacognition_weak": "The summary needs reflection or a next-study planning prompt.",
            "representation_weak": "The draft relies on nearly one representation mode; add another relevant representation or response option.",
        },
    }
    raw = str(code)
    base = raw.split(":", 1)[0]
    label = labels[lang].get(base, raw)
    detail = raw.split(":", 1)[1] if ":" in raw else ""
    return f"{label} ({detail})" if detail and label != raw else label


def status_label(status: str, language_code: str = "ar") -> str:
    lang = _lang(language_code)
    labels = {
        "ar": {"blocked": "تحتاج إصلاحًا", "review": "تحتاج مراجعة", "ready": "جاهزة للمراجعة"},
        "fr": {"blocked": "À corriger", "review": "À réviser", "ready": "Prête à réviser"},
        "en": {"blocked": "Needs repair", "review": "Needs review", "ready": "Ready for review"},
    }
    return labels[lang].get(str(status), str(status))


def evaluate_lesson(
    lesson: Mapping[str, Any],
    assembled_rows: Iterable[Mapping[str, Any]],
    *,
    language_code: str = "ar",
) -> Dict[str, Any]:
    """Evaluate a complete lesson draft with transparent deterministic rules."""
    rows = list(assembled_rows or [])
    by_type = _row_map(rows)
    blockers: List[str] = []
    warnings: List[str] = []

    missing = [block for block in REQUIRED_BLOCKS if not by_type.get(block) or not by_type[block].get("run")]
    if missing:
        blockers.extend([f"missing_lesson_section:{block}" for block in missing])

    validation_errors: List[str] = []
    validation_warnings: List[str] = []
    cited: set[str] = set()
    all_text_parts: List[str] = []
    for block_type, row in by_type.items():
        if not row.get("run"):
            continue
        text = _text(row)
        all_text_parts.append(text)
        report = _validation(row)
        for item in report.get("errors") or []:
            validation_errors.append(f"{block_type}:{item}")
        for item in report.get("warnings") or []:
            validation_warnings.append(f"{block_type}:{item}")
        cited.update(str(item) for item in report.get("cited_source_ids") or [])
        if _unsafe_html(text):
            blockers.append(f"unsafe_html_detected:{block_type}")

    blockers.extend([f"block_validation_error:{item}" for item in validation_errors])

    outcomes = list(lesson.get("learning_outcomes") or [])
    assessments = list(lesson.get("assessments") or [])
    required_sources = {str(item) for item in lesson.get("source_ids") or [] if str(item).strip()}
    if not outcomes:
        warnings.append("outcomes_missing")
    if required_sources and not cited:
        warnings.append("source_traceability_weak")

    activation = _text(by_type.get("activation"))
    explanation = _text(by_type.get("explanation"))
    worked = _text(by_type.get("worked_example"))
    guided = _text(by_type.get("guided_practice"))
    independent = _text(by_type.get("independent_practice"))
    misconception = _text(by_type.get("misconceptions"))
    assessment = _text(by_type.get("formative_assessment"))
    summary = _text(by_type.get("summary"))
    resources = _text(by_type.get("resources"))
    full_text = "\n".join(all_text_parts)

    dim_scores: Dict[str, float] = {}
    dim_scores["alignment"] = _ratio(
        bool(outcomes),
        bool(assessments),
        (not required_sources) or bool(cited),
    )

    dim_scores["learner_activation"] = _ratio(
        bool(activation) and ("?" in activation or "؟" in activation),
        _has_any(activation, ("استرجع", "تذكر", "تذكّر", "توقع", "توقّع", "recall", "retrieve", "predict", "rappelle", "prédis")),
        _has_any(worked, ("جرّب", "حاول", "محاولة", "attempt", "try", "essayez", "tentative")),
    )

    dim_scores["scaffolding"] = _ratio(
        _has_any(worked, ("تلميح", "hint", "indice")),
        _has_any(worked, ("الحل", "solution", "réponse")),
        _has_any(guided, ("تلميح", "hint", "indice", "نقطة تحقق", "check")),
        bool(independent),
    )

    dim_scores["practice_transfer"] = _ratio(
        _has_any(worked + "\n" + independent, ("غيّر", "حالة جديدة", "تطبيق جديد", "transfer", "new case", "variation", "nouveau cas", "transfert")),
        _has_any(independent, ("معيار", "criterion", "critère", "نجاح", "success", "réussite")),
        bool(guided) and bool(independent),
    )

    dim_scores["assessment_feedback"] = _ratio(
        _has_any(assessment, ("معيار", "criterion", "critère", "نجاح", "success", "réussite")),
        _has_any(assessment, ("تغذية راجعة", "feedback", "retour")),
        _has_any(assessment, ("أعد التدريس", "مثال إضافي", "انتقل", "reteach", "another example", "progress", "réenseigner", "passer")),
        bool(assessment) and ("?" in assessment or "؟" in assessment),
    )

    dim_scores["misconception_repair"] = _ratio(
        _has_any(misconception, ("خطأ", "خاطئ", "misconception", "incorrect", "erreur", "fausse")),
        _has_any(misconception, ("الصحيح", "تصحيح", "correct", "repair", "corriger", "correction")),
        ("?" in misconception or "؟" in misconception) or _has_any(misconception, ("تحقق", "check", "diagnostic", "vérifie")),
    )

    dim_scores["metacognition"] = _ratio(
        _has_any(summary, ("تأمل", "فكّر", "قيّم", "reflect", "reflection", "evaluate", "réfléch", "évalue")),
        _has_any(summary + "\n" + resources, ("التالي", "سأراجع", "سأتدرب", "next", "review next", "practise next", "prochaine", "réviser")),
    )

    # This is an accessibility/representation *signal*, not a claim of UDL
    # compliance. We look for meaningful variety across the lesson rather than
    # requiring any single medium for every subject.
    modality_checks = (
        bool(re.search(r"```", full_text)),
        bool(re.search(r"(?m)^\s*[-*]\s+", full_text)),
        bool(re.search(r"(?m)^\s*\|.+\|\s*$", full_text)),
        ("?" in full_text or "؟" in full_text),
        _has_any(full_text, ("رسم", "مخطط", "جدول", "مثال", "simulation", "diagram", "table", "example", "schéma", "exemple")),
    )
    dim_scores["representation_access"] = sum(1 for value in modality_checks if value) / len(modality_checks)

    threshold_warnings = {
        "learner_activation": (0.66, "activation_weak"),
        "scaffolding": (0.75, "scaffolding_weak"),
        "practice_transfer": (0.66, "transfer_weak"),
        "assessment_feedback": (0.75, "assessment_weak"),
        "misconception_repair": (0.66, "misconception_weak"),
        "metacognition": (0.50, "metacognition_weak"),
        "representation_access": (0.40, "representation_weak"),
    }
    for key, (threshold, code) in threshold_warnings.items():
        if dim_scores.get(key, 0.0) < threshold:
            warnings.append(code)

    # Preserve block-level warnings as evidence, but deduplicate codes here.
    warnings.extend(validation_warnings)
    warnings = list(dict.fromkeys(warnings))
    blockers = list(dict.fromkeys(blockers))

    weighted = 0.0
    dimensions: List[Dict[str, Any]] = []
    for item in DIMENSIONS:
        key = str(item["key"])
        score = max(0.0, min(1.0, float(dim_scores.get(key, 0.0))))
        weighted += score * float(item["weight"])
        dimensions.append({
            "key": key,
            "label": dimension_label(key, language_code),
            "score": round(score, 3),
            "percent": int(round(score * 100)),
            "weight": float(item["weight"]),
        })

    quality_score = int(round(weighted * 100))
    if blockers:
        status = "blocked"
    elif quality_score >= 80 and len([w for w in warnings if ":" not in w]) <= 2:
        status = "ready"
    else:
        status = "review"

    return {
        "status": status,
        "status_label": status_label(status, language_code),
        "quality_score": quality_score,
        "can_approve": not blockers,
        "teacher_review_required": bool(warnings) or quality_score < 90,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "blockers": blockers,
        "warnings": warnings,
        "dimensions": dimensions,
        "required_source_count": len(required_sources),
        "cited_source_count": len(cited & required_sources) if required_sources else len(cited),
        "outcome_count": len(outcomes),
        "assessment_count": len(assessments),
    }
