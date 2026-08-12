"""Transparent adaptive-support policy for the 3alimnIA AI learning coach.

The engine estimates *how much support to offer next*; it does not claim to
measure true mastery. It combines available evidence (pre-test concept signal,
learner attempt quality, and recent support requests) and returns an inspectable
support decision. The teacher/researcher can audit the decision later because
its level, mode, confidence, and reason are logged with each AI interaction.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Mapping, Optional


SUPPORT_LEVELS: Dict[int, Dict[str, str]] = {
    0: {
        "mode": "quiz",
        "ar": "تحدٍّ ونقل التعلم",
        "fr": "Défi et transfert",
        "en": "Challenge and transfer",
        "instruction": "Ask one concise transfer or prediction question. Do not explain first and do not reveal the answer.",
    },
    1: {
        "mode": "hint",
        "ar": "سؤال موجّه",
        "fr": "Question socratique",
        "en": "Guiding question",
        "instruction": "Ask one diagnostic Socratic question that helps the learner inspect their own reasoning. Do not give the solution.",
    },
    2: {
        "mode": "hint",
        "ar": "تلميح متدرج",
        "fr": "Indice progressif",
        "en": "Graduated hint",
        "instruction": "Give one general hint, then one check question. Keep the full solution hidden unless a later pedagogical step explicitly requires it.",
    },
    3: {
        "mode": "simplify",
        "ar": "شرح مصغّر مع مثال مشابه",
        "fr": "Mini-explication avec exemple analogue",
        "en": "Micro-explanation with analogous example",
        "instruction": "Explain one difficult step with a small analogous example that is not the learner's exact task, then ask the learner to retry their own task.",
    },
}


def _lang(language_code: str) -> str:
    value = str(language_code or "en").lower()
    if value.startswith("ar"):
        return "ar"
    if value.startswith("fr"):
        return "fr"
    return "en"


def _safe_json(value: Any, default: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value or ""))
    except Exception:
        return default


def _concept_ratio(pre_attempt: Optional[Mapping[str, Any]], lesson: Mapping[str, Any]) -> Optional[float]:
    if not pre_attempt:
        return None
    per = _safe_json(pre_attempt.get("per_concept_json"), {})
    concepts = [str(item).casefold().strip() for item in lesson.get("concepts") or [] if str(item).strip()]
    ratios = []
    if isinstance(per, dict):
        for concept_name, stats in per.items():
            name = str(concept_name or "").casefold().strip()
            if concepts and not any(name == target or name in target or target in name for target in concepts):
                continue
            if isinstance(stats, Mapping):
                total = max(1, int(stats.get("total") or 0))
                ratios.append(float(stats.get("correct") or 0) / total)
    if ratios:
        return sum(ratios) / len(ratios)
    total = int(pre_attempt.get("total_count") or 0)
    correct = int(pre_attempt.get("correct_count") or 0)
    if total > 0:
        return correct / total
    score = pre_attempt.get("score")
    try:
        score_value = float(score)
        return score_value / 100.0 if score_value > 1 else score_value
    except Exception:
        return None


def _attempt_strength(attempt: Optional[Mapping[str, Any]]) -> float:
    if not attempt:
        return 0.0
    status = str(attempt.get("validation_status") or "")
    if status not in {"valid_draft", "submitted_for_support", "opened_full_tutor"}:
        return 0.0
    words = max(0, int(attempt.get("word_count") or 0))
    unique = max(0, int(attempt.get("unique_word_count") or 0))
    if words <= 0:
        return 0.5
    diversity = min(1.0, unique / max(words, 1) * 1.8)
    length = min(1.0, words / 24.0)
    return max(0.0, min(1.0, 0.55 + 0.25 * length + 0.20 * diversity))


def _interaction_count(interactions: Iterable[Mapping[str, Any]]) -> int:
    return sum(1 for _ in interactions)


def recommend_support(
    *,
    lesson: Mapping[str, Any],
    pre_attempt: Optional[Mapping[str, Any]] = None,
    learner_attempt: Optional[Mapping[str, Any]] = None,
    recent_interactions: Iterable[Mapping[str, Any]] = (),
    learner_evidence_profile: Optional[Mapping[str, Any]] = None,
    language_code: str = "ar",
) -> Dict[str, Any]:
    """Return an inspectable next-support decision.

    The returned ``confidence`` reflects evidence coverage, not certainty about
    the learner. The engine should be described as a support estimate rather
    than an automated mastery judgement.
    """
    lang = _lang(language_code)
    interactions = list(recent_interactions or [])
    concept_ratio = _concept_ratio(pre_attempt, lesson)
    attempt_strength = _attempt_strength(learner_attempt)
    help_count = _interaction_count(interactions)

    if concept_ratio is None:
        level = 1
    elif concept_ratio >= 0.80:
        level = 0
    elif concept_ratio >= 0.62:
        level = 1
    elif concept_ratio >= 0.38:
        level = 2
    else:
        level = 3

    # A substantial valid attempt is evidence that the learner can remain
    # active; reduce directness slightly unless repeated support requests point
    # to persistent difficulty.
    if attempt_strength >= 0.82 and help_count == 0:
        level = max(0, level - 1)
    if help_count >= 3:
        level = max(level, 2)
    if help_count >= 5:
        level = 3

    evidence_profile = dict(learner_evidence_profile or {})
    evidence_stage = str(evidence_profile.get("stage") or "")
    hypotheses = list(evidence_profile.get("misconception_hypotheses") or [])
    explicit_items = [item for item in hypotheses if isinstance(item, Mapping) and str(item.get("kind") or "") == "explicit_misconception_hypothesis"]
    explicit_hypothesis = bool(explicit_items)
    recurring_pattern = any(str(item.get("kind") or "") == "recurring_error_pattern" for item in hypotheses if isinstance(item, Mapping))
    diagnostic_hypothesis_label = str((explicit_items[0] if explicit_items else {}).get("label") or "")
    if explicit_hypothesis:
        level = max(level, 2)
    elif recurring_pattern:
        level = max(level, 1)
    if evidence_stage == "transfer_signal" and help_count == 0:
        level = min(level, 0)
    elif evidence_stage == "demonstrated" and help_count == 0:
        level = min(level, 1)
    elif evidence_stage == "supported":
        level = max(level, 1)

    level = int(max(0, min(3, level)))
    policy = SUPPORT_LEVELS[level]

    signal_count = int(concept_ratio is not None) + int(learner_attempt is not None) + int(help_count > 0)
    confidence = {0: 0.35, 1: 0.50, 2: 0.68, 3: 0.80}.get(signal_count, 0.50)

    reasons = []
    if concept_ratio is not None:
        reasons.append(f"pretest_concept_ratio={concept_ratio:.2f}")
    else:
        reasons.append("pretest_concept_ratio=unknown")
    reasons.append(f"attempt_strength={attempt_strength:.2f}")
    reasons.append(f"prior_support_requests={help_count}")
    if evidence_stage:
        reasons.append(f"learner_evidence_stage={evidence_stage}")
    if hypotheses:
        reasons.append(f"diagnostic_patterns={len(hypotheses)}")

    rationale = {
        "ar": {
            0: "الأدلة المتاحة تسمح بتحدٍ قصير يختبر نقل الفهم قبل تقديم شرح إضافي.",
            1: "الأفضل الآن سؤال موجّه يكشف التفكير ويترك الحل للمتعلم.",
            2: "المتعلم يحتاج تلميحًا متدرجًا مع نقطة تحقق، مع إبقاء الحل الكامل مخفيًا.",
            3: "الأدلة تشير إلى حاجة لدعم أوضح: شرح خطوة واحدة بمثال مشابه ثم إعادة المحاولة.",
        },
        "fr": {
            0: "Les indices disponibles permettent un défi bref de transfert avant toute explication supplémentaire.",
            1: "Une question guidée est préférable pour révéler le raisonnement sans donner la solution.",
            2: "Un indice progressif avec une vérification est approprié, sans révéler la solution complète.",
            3: "Un soutien plus explicite est indiqué : une étape expliquée avec un exemple analogue, puis une nouvelle tentative.",
        },
        "en": {
            0: "Available evidence supports a short transfer challenge before any additional explanation.",
            1: "A guiding question is the best next move to expose reasoning without giving the solution.",
            2: "A graduated hint plus a check is appropriate while keeping the complete solution hidden.",
            3: "More explicit support is indicated: explain one step with an analogous example, then ask for another attempt.",
        },
    }[lang][level]

    return {
        "level": level,
        "mode": policy["mode"],
        "label": policy[lang],
        "instruction": policy["instruction"],
        "rationale": rationale,
        "confidence": round(confidence, 2),
        "signals": {
            "pretest_concept_ratio": None if concept_ratio is None else round(concept_ratio, 3),
            "attempt_strength": round(attempt_strength, 3),
            "prior_support_requests": help_count,
            "learner_evidence_stage": evidence_stage or None,
            "diagnostic_patterns": len(hypotheses),
            "diagnostic_hypothesis_label": diagnostic_hypothesis_label or None,
        },
        "reason": "; ".join(reasons),
    }


def prompt_contract(decision: Mapping[str, Any], *, chosen_mode: str = "") -> str:
    level = int(decision.get("level") or 0)
    instruction = str(decision.get("instruction") or SUPPORT_LEVELS[level]["instruction"])
    chosen = str(chosen_mode or decision.get("mode") or "")
    return f"""<adaptive_support_contract>
Support level: {level}/3
Recommended mode: {decision.get('mode')}
Chosen mode: {chosen}
Instructional move: {instruction}
Learner evidence stage: {(decision.get('signals') or {}).get('learner_evidence_stage')}
Diagnostic patterns requiring follow-up: {(decision.get('signals') or {}).get('diagnostic_patterns', 0)}
Unconfirmed diagnostic hypothesis: {(decision.get('signals') or {}).get('diagnostic_hypothesis_label')}
Guardrails:
- Treat this as an estimate of needed support, not a claim of learner mastery.
- Preserve productive learner effort and never skip directly from attempt to answer dumping.
- Prefer one next instructional move at a time, then ask the learner to respond.
- If the learner's reasoning is ambiguous, diagnose before explaining more.
- If an unconfirmed diagnostic hypothesis is present, test it with a discrimination or contrast question; never state it as a fact about the learner.
- Do not reveal a complete solution unless the task explicitly requires a worked solution and the learner has already attempted it.
</adaptive_support_contract>""".strip()
