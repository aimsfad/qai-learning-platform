"""Transparent learner-evidence model for 3alimnIA.

This module intentionally does *not* claim to estimate true learner mastery.
It summarizes observable evidence (assessment responses, attempts, reflection,
transfer items, and support context) and recommends the next pedagogical move.

Design goals:
- interpretable evidence over opaque prediction;
- separate evidence coverage from observed performance;
- treat AI support as context, not as a penalty;
- trace explicit misconception tags only when assessment metadata supports them;
- label repeated wrong answers without explicit tags as error patterns that still
  need diagnosis, never as confirmed misconceptions.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


TRANSFER_LEVELS = {
    "application", "applying", "analysis", "analyzing", "analyse", "analyze",
    "evaluation", "evaluating", "create", "creating", "transfer",
}

STAGE_COPY: Dict[str, Dict[str, str]] = {
    "insufficient": {
        "ar": "الأدلة ما تزال محدودة",
        "fr": "Données encore limitées",
        "en": "Evidence is still limited",
    },
    "starting": {
        "ar": "بداية تشخيصية",
        "fr": "Point de départ diagnostique",
        "en": "Diagnostic starting point",
    },
    "developing": {
        "ar": "أدلة تعلم نامية",
        "fr": "Indices d'apprentissage en développement",
        "en": "Developing learning evidence",
    },
    "supported": {
        "ar": "تقدم ظاهر مع دعم",
        "fr": "Progrès observé avec soutien",
        "en": "Progress observed with support",
    },
    "demonstrated": {
        "ar": "فهم ظاهر في الأدلة",
        "fr": "Compréhension visible dans les données",
        "en": "Understanding visible in the evidence",
    },
    "transfer_signal": {
        "ar": "إشارة إيجابية إلى نقل التعلم",
        "fr": "Signal positif de transfert",
        "en": "Positive transfer signal",
    },
}

NEXT_MOVE_COPY: Dict[str, Dict[str, str]] = {
    "diagnose": {
        "ar": "ابدأ بسؤال تشخيصي قصير ومحاولة مستقلة.",
        "fr": "Commencer par une courte question diagnostique et une tentative autonome.",
        "en": "Start with a short diagnostic question and an independent attempt.",
    },
    "retrieve": {
        "ar": "استخدم استرجاعًا قصيرًا للمعرفة السابقة قبل إضافة شرح جديد.",
        "fr": "Utiliser un bref rappel actif avant d'ajouter une nouvelle explication.",
        "en": "Use brief retrieval of prior knowledge before adding new explanation.",
    },
    "guided_practice": {
        "ar": "قدّم مثالًا قريبًا ثم تدريبًا موجّهًا مع نقطة تحقق.",
        "fr": "Proposer un exemple proche puis une pratique guidée avec vérification.",
        "en": "Use a nearby example followed by guided practice and a check point.",
    },
    "fade_scaffold": {
        "ar": "خفّف السقالات تدريجيًا واطلب محاولة جديدة أكثر استقلالًا.",
        "fr": "Réduire progressivement l'étayage et demander une nouvelle tentative plus autonome.",
        "en": "Fade scaffolding and request a more independent retry.",
    },
    "independent_retrieval": {
        "ar": "اختبر الفهم باسترجاع أو تطبيق مستقل قصير قبل الانتقال.",
        "fr": "Vérifier la compréhension par un bref rappel ou une application autonome.",
        "en": "Check understanding with a short independent retrieval or application task.",
    },
    "transfer": {
        "ar": "قدّم مهمة نقل جديدة أو مراجعة متباعدة بدل إعادة الشرح نفسه.",
        "fr": "Proposer une nouvelle tâche de transfert ou une révision espacée plutôt que répéter la même explication.",
        "en": "Use a new transfer task or spaced review rather than repeating the same explanation.",
    },
    "misconception_diagnosis": {
        "ar": "اختبر الفكرة البديلة بسؤال تمييز أو مثالين متقابلين قبل التصحيح المباشر.",
        "fr": "Tester l'idée alternative avec une question de discrimination ou deux exemples contrastés avant de corriger.",
        "en": "Test the alternative idea with a discrimination question or contrasting examples before direct correction.",
    },
}


def _lang(language_code: str) -> str:
    value = str(language_code or "en").lower()
    if value.startswith("ar"):
        return "ar"
    if value.startswith("fr"):
        return "fr"
    return "en"


def _records(items: Any) -> List[Dict[str, Any]]:
    if items is None:
        return []
    if isinstance(items, list):
        return [dict(item) for item in items if isinstance(item, Mapping)]
    if isinstance(items, tuple):
        return [dict(item) for item in items if isinstance(item, Mapping)]
    if hasattr(items, "to_dict"):
        try:
            return [dict(item) for item in items.to_dict("records")]
        except Exception:
            return []
    if isinstance(items, Mapping):
        return [dict(items)]
    return []


def _norm(value: Any) -> str:
    return " ".join(str(value or "").casefold().strip().split())


def _concept_match(value: Any, targets: Sequence[str]) -> bool:
    if not targets:
        return True
    candidate = _norm(value)
    if not candidate:
        return False
    for target in targets:
        t = _norm(target)
        if t and (candidate == t or candidate in t or t in candidate):
            return True
    return False


def _ratio(rows: Sequence[Mapping[str, Any]]) -> Optional[float]:
    if not rows:
        return None
    observed = [int(row.get("is_correct") or 0) for row in rows]
    return sum(observed) / len(observed) if observed else None


def _assessment_summary(
    question_responses: Any,
    assessment_concepts: Sequence[str],
) -> Dict[str, Any]:
    rows = [
        row for row in _records(question_responses)
        if _concept_match(row.get("concept"), assessment_concepts)
    ]
    pre = [row for row in rows if _norm(row.get("attempt_type")) == "pre"]
    post = [row for row in rows if _norm(row.get("attempt_type")) == "post"]
    transfer = [
        row for row in rows
        if _norm(row.get("cognitive_level")) in TRANSFER_LEVELS
    ]
    transfer_post = [
        row for row in transfer if _norm(row.get("attempt_type")) == "post"
    ]
    return {
        "rows": rows,
        "pre_ratio": _ratio(pre),
        "post_ratio": _ratio(post),
        "overall_ratio": _ratio(rows),
        "pre_items": len(pre),
        "post_items": len(post),
        "transfer_items": len(transfer),
        "transfer_post_items": len(transfer_post),
        "transfer_post_correct": sum(int(row.get("is_correct") or 0) for row in transfer_post),
        "transfer_post_ratio": _ratio(transfer_post),
    }


def _attempt_summary(learner_attempt: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    attempt = dict(learner_attempt or {})
    status = str(attempt.get("validation_status") or "")
    valid = status in {"valid_draft", "submitted_for_support", "opened_full_tutor"}
    words = max(0, int(attempt.get("word_count") or 0))
    return {
        "present": bool(attempt.get("attempt_text")),
        "valid": valid,
        "pre_support": status in {"valid_draft", "submitted_for_support"},
        "word_count": words,
        "status": status,
    }


def _progress_summary(progress: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    row = dict(progress or {})
    reflection = str(row.get("reflection_text") or "").strip()
    return {
        "completed": bool(int(row.get("completed") or 0)),
        "reflection_present": len(reflection) >= 20,
        "reflection_chars": len(reflection),
    }


def _support_summary(ai_interactions: Any) -> Dict[str, Any]:
    rows = _records(ai_interactions)
    levels: List[int] = []
    for row in rows:
        value = row.get("adaptive_support_level")
        try:
            levels.append(int(value))
        except Exception:
            continue
    return {
        "count": len(rows),
        "adaptive_count": len(levels),
        "max_level": max(levels) if levels else None,
        "mean_level": (sum(levels) / len(levels)) if levels else None,
    }


def trace_misconception_evidence(
    question_responses: Any,
    assessment_concepts: Sequence[str] = (),
    language_code: str = "ar",
) -> List[Dict[str, Any]]:
    """Return conservative misconception hypotheses and recurring error patterns.

    A confirmed misconception is never inferred from a generic wrong answer.
    Explicit hypotheses require assessment metadata (misconception_code/label).
    Repeated untagged errors are labelled only as patterns that need diagnosis.
    """
    lang = _lang(language_code)
    rows = [
        row for row in _records(question_responses)
        if _concept_match(row.get("concept"), assessment_concepts)
    ]
    wrong = [row for row in rows if int(row.get("is_correct") or 0) == 0]
    by_code: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in wrong:
        code = str(row.get("misconception_code") or "").strip()
        if code:
            by_code[code].append(row)

    output: List[Dict[str, Any]] = []
    for code, group in by_code.items():
        label = next((str(row.get("misconception_label") or "").strip() for row in group if str(row.get("misconception_label") or "").strip()), code)
        attempts = sorted({_norm(row.get("attempt_type")) for row in group if _norm(row.get("attempt_type"))})
        status = "persistent_hypothesis" if "pre" in attempts and "post" in attempts else "candidate_hypothesis"
        output.append({
            "kind": "explicit_misconception_hypothesis",
            "code": code,
            "label": label,
            "status": status,
            "evidence_count": len(group),
            "attempt_types": attempts,
            "is_confirmed": False,
            "requires_human_review": True,
            "reason": {
                "ar": "يرتبط هذا النمط بوسم تشخيصي صريح في أداة التقويم، لكنه يبقى فرضية تحتاج تحققًا تربويًا.",
                "fr": "Ce motif est lié à une balise diagnostique explicite de l'évaluation, mais reste une hypothèse à vérifier pédagogiquement.",
                "en": "This pattern is linked to an explicit diagnostic tag in the assessment, but remains a hypothesis requiring pedagogical verification.",
            }[lang],
        })

    # Untagged repeated wrong answers are useful evidence, but we deliberately
    # avoid naming them misconceptions.
    tagged_ids = {str(row.get("question_id") or "") for group in by_code.values() for row in group}
    untagged = [row for row in wrong if str(row.get("question_id") or "") not in tagged_ids]
    by_concept: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in untagged:
        by_concept[str(row.get("concept") or "Unknown concept")].append(row)
    for concept, group in by_concept.items():
        if len(group) < 2:
            continue
        attempts = sorted({_norm(row.get("attempt_type")) for row in group if _norm(row.get("attempt_type"))})
        label = {
            "ar": f"نمط خطأ متكرر في: {concept}",
            "fr": f"Motif d'erreur répété : {concept}",
            "en": f"Recurring error pattern in: {concept}",
        }[lang]
        output.append({
            "kind": "recurring_error_pattern",
            "code": "",
            "label": label,
            "status": "needs_diagnosis",
            "evidence_count": len(group),
            "attempt_types": attempts,
            "is_confirmed": False,
            "requires_human_review": True,
            "reason": {
                "ar": "الإجابات الخاطئة المتكررة تستحق سؤالًا تشخيصيًا، لكنها لا تكفي وحدها لإثبات تصور خاطئ محدد.",
                "fr": "Des erreurs répétées justifient une question diagnostique, mais ne prouvent pas à elles seules une conception erronée précise.",
                "en": "Repeated wrong answers justify diagnostic follow-up but do not by themselves prove a specific misconception.",
            }[lang],
        })

    output.sort(key=lambda item: (-int(item.get("evidence_count") or 0), item.get("kind") or ""))
    return output


def _evidence_coverage(assessment: Mapping[str, Any], attempt: Mapping[str, Any], progress: Mapping[str, Any]) -> float:
    coverage = 0.0
    if assessment.get("pre_items"):
        coverage += 0.20
    if assessment.get("post_items"):
        coverage += 0.30
    if attempt.get("valid"):
        coverage += 0.20
    if progress.get("reflection_present"):
        coverage += 0.15
    if assessment.get("transfer_post_items"):
        coverage += 0.15
    return round(min(1.0, coverage), 2)


def _stage(
    assessment: Mapping[str, Any],
    attempt: Mapping[str, Any],
    progress: Mapping[str, Any],
    support: Mapping[str, Any],
    coverage: float,
) -> str:
    if coverage < 0.25 and not attempt.get("valid"):
        return "insufficient"

    post = assessment.get("post_ratio")
    pre = assessment.get("pre_ratio")
    observed = post if post is not None else pre
    transfer_items = int(assessment.get("transfer_post_items") or 0)
    transfer_correct = int(assessment.get("transfer_post_correct") or 0)

    if (
        post is not None
        and post >= 0.80
        and transfer_items > 0
        and transfer_correct >= 1
        and attempt.get("valid")
    ):
        return "transfer_signal"

    if observed is not None and observed >= 0.70 and (attempt.get("valid") or progress.get("completed")):
        if (support.get("mean_level") is not None and float(support.get("mean_level")) >= 2.0) or int(support.get("count") or 0) >= 3:
            return "supported"
        return "demonstrated"

    if attempt.get("valid") or (observed is not None and observed >= 0.40):
        return "developing"
    return "starting"


def _next_move(stage: str, hypotheses: Sequence[Mapping[str, Any]]) -> str:
    if any(item.get("kind") == "explicit_misconception_hypothesis" for item in hypotheses):
        return "misconception_diagnosis"
    if any(item.get("kind") == "recurring_error_pattern" for item in hypotheses):
        return "diagnose"
    return {
        "insufficient": "diagnose",
        "starting": "retrieve",
        "developing": "guided_practice",
        "supported": "fade_scaffold",
        "demonstrated": "independent_retrieval",
        "transfer_signal": "transfer",
    }.get(stage, "diagnose")


def build_learner_evidence_profile(
    *,
    question_responses: Any = (),
    assessment_concepts: Sequence[str] = (),
    learner_attempt: Optional[Mapping[str, Any]] = None,
    lesson_progress: Optional[Mapping[str, Any]] = None,
    ai_interactions: Any = (),
    evidence_events: Any = (),
    language_code: str = "ar",
    enable_misconception_tracing: bool = True,
) -> Dict[str, Any]:
    """Build an interpretable learner-evidence profile for one concept/lesson.

    ``evidence_coverage`` tells us how much relevant evidence is available.
    ``observed_performance`` reports observed assessment correctness only.
    Neither field is a mastery probability or a high-stakes learner score.
    """
    lang = _lang(language_code)
    assessment = _assessment_summary(question_responses, assessment_concepts)
    attempt = _attempt_summary(learner_attempt)
    progress = _progress_summary(lesson_progress)
    support = _support_summary(ai_interactions)
    events = _records(evidence_events)
    hypotheses = (
        trace_misconception_evidence(
            question_responses,
            assessment_concepts=assessment_concepts,
            language_code=lang,
        )
        if enable_misconception_tracing
        else []
    )
    coverage = _evidence_coverage(assessment, attempt, progress)
    stage = _stage(assessment, attempt, progress, support, coverage)
    next_move = _next_move(stage, hypotheses)
    observed = assessment.get("post_ratio")
    observed_source = "post" if observed is not None else "pre"
    if observed is None:
        observed = assessment.get("pre_ratio")
    if observed is None:
        observed_source = "none"

    evidence_flags = {
        "assessment": bool(assessment.get("pre_items") or assessment.get("post_items")),
        "attempt_before_support": bool(attempt.get("valid") and attempt.get("pre_support")),
        "reflection": bool(progress.get("reflection_present")),
        "lesson_completion": bool(progress.get("completed")),
        "transfer_item": bool(assessment.get("transfer_post_items")),
        "support_context": bool(support.get("count")),
        "instrumented_events": bool(events),
    }

    return {
        "stage": stage,
        "stage_label": STAGE_COPY[stage][lang],
        "evidence_coverage": coverage,
        "observed_performance": None if observed is None else round(float(observed), 3),
        "observed_performance_source": observed_source,
        "assessment": assessment,
        "attempt": attempt,
        "progress": progress,
        "support_context": support,
        "evidence_flags": evidence_flags,
        "evidence_event_count": len(events),
        "misconception_hypotheses": hypotheses,
        "next_move": next_move,
        "next_move_label": NEXT_MOVE_COPY[next_move][lang],
        "guardrail": {
            "ar": "هذا ملخص لأدلة تعلم مرصودة، وليس حكمًا آليًا نهائيًا على إتقان المتعلم أو قدرته.",
            "fr": "Ceci résume des indices d'apprentissage observés; ce n'est pas un jugement automatisé définitif de maîtrise ou de capacité.",
            "en": "This summarizes observed learning evidence; it is not an automated final judgement of learner mastery or ability.",
        }[lang],
    }


def research_summary_rows(
    profiles: Iterable[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    """Convert profile dictionaries to flat, research-friendly rows."""
    rows: List[Dict[str, Any]] = []
    for item in profiles:
        rows.append({
            "student_id": item.get("student_id"),
            "lesson_id": item.get("lesson_id"),
            "stage": item.get("stage"),
            "evidence_coverage": item.get("evidence_coverage"),
            "observed_performance": item.get("observed_performance"),
            "observed_performance_source": item.get("observed_performance_source"),
            "support_count": (item.get("support_context") or {}).get("count"),
            "mean_support_level": (item.get("support_context") or {}).get("mean_level"),
            "misconception_hypotheses": len(item.get("misconception_hypotheses") or []),
            "next_move": item.get("next_move"),
        })
    return rows
