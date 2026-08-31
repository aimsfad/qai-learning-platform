"""Evidence-to-lesson blueprint compiler for 3alimnIA.

V6.14 converts a teacher-approved evidence bundle into an auditable course
blueprint before long-form educational content is generated.  The compiler is
provider-independent by default, so course planning remains available when
hosted LLM quotas are unavailable.  Every unit, lesson, outcome, activity, and
assessment remains linked to concept and source identifiers from the approved
evidence bundle.
"""

from __future__ import annotations

import copy
import json
import math
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import streamlit as st

import db
import lesson_identity


@dataclass
class BlueprintResult:
    blueprint: Dict[str, Any]
    quality: Dict[str, Any]
    provider: str
    model: str
    status: str
    diagnostic: str
    evidence_run_id: int
    prompt_text: str = ""
    response_text: str = ""
    latency_ms: int = 0
    used_fallback: bool = False


def _secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def _as_bool(name: str, default: bool = False) -> bool:
    raw = _secret(name, "true" if default else "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _as_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(_secret(name, str(default)) or str(default))
    except (TypeError, ValueError):
        value = int(default)
    return max(minimum, min(maximum, value))


def blueprint_status() -> Dict[str, Any]:
    return {
        "enabled": _as_bool("ENABLE_LESSON_BLUEPRINT", False),
        "require_teacher_approval": _as_bool("REQUIRE_BLUEPRINT_APPROVAL_FOR_GENERATION", False),
        "max_units": _as_int("BLUEPRINT_MAX_UNITS", 5, 1, 12),
        "max_lessons": _as_int("BLUEPRINT_MAX_LESSONS", 12, 2, 40),
        "minimum_readiness": float(_secret("BLUEPRINT_MIN_READINESS", "0.70") or "0.70"),
        "editor_enabled": _as_bool("ENABLE_BLUEPRINT_EDITOR", True),
        "max_revision_history": _as_int("BLUEPRINT_MAX_REVISION_HISTORY", 50, 5, 500),
    }


def _norm(value: str) -> str:
    text = re.sub(r"[^\w\u0600-\u06ff]+", " ", str(value or "").lower(), flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _lang(project: Mapping[str, Any]) -> str:
    code = str(project.get("primary_language_code") or "en").strip().lower()
    return code if code in {"ar", "fr", "en"} else "en"


def _title(text: str, fallback: str) -> str:
    clean = re.sub(r"\s+", " ", str(text or "")).strip(" -:;,.\n")
    return clean or fallback


def _concept_records(evidence_bundle: Mapping[str, Any]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    source_titles = lesson_identity.source_titles_from_bundle(evidence_bundle)
    for index, raw in enumerate(evidence_bundle.get("concepts") or [], start=1):
        concept_id = str(raw.get("concept_id") or f"C{index}")
        name = _title(raw.get("name") or raw.get("concept_name"), concept_id)
        if lesson_identity.looks_like_source_title(name, source_titles):
            continue
        prerequisites = [
            str(value).strip()
            for value in list(raw.get("prerequisites") or [])
            if str(value).strip() and not lesson_identity.looks_like_source_title(value, source_titles)
        ]
        records.append(
            {
                "concept_id": concept_id,
                "name": name,
                "description": str(raw.get("description") or "").strip(),
                "prerequisites": prerequisites,
                "source_ids": list(raw.get("source_ids") or []),
                "difficulty": str(raw.get("difficulty") or "introductory"),
            }
        )
    return records


def _project_fallback_concept_records(
    project: Mapping[str, Any], evidence_bundle: Mapping[str, Any]
) -> List[Dict[str, Any]]:
    source_titles = lesson_identity.source_titles_from_bundle(evidence_bundle)
    names = lesson_identity.safe_project_concept_candidates(project, source_titles)
    # Do not attach arbitrary approved source ids to a project-brief fallback.
    # If every evidence concept was rejected as source metadata, the evidence-to-
    # concept mapping is not trustworthy enough to claim traceability. The
    # provisional outline may still help the teacher see a clean structure, but
    # approval is blocked until evidence is rebuilt (see quality flag below).
    return [
        {
            "concept_id": f"P{index}",
            "name": name,
            "description": "Pedagogical fallback derived from the teacher project brief after source-title concepts were rejected.",
            "prerequisites": [],
            "source_ids": [],
            "difficulty": "introductory",
        }
        for index, name in enumerate(names[:4], start=1)
    ]


def build_concept_edges(concepts: Sequence[Mapping[str, Any]]) -> List[Dict[str, str]]:
    by_name = {_norm(item.get("name")): str(item.get("concept_id")) for item in concepts}
    by_id = {str(item.get("concept_id")): str(item.get("concept_id")) for item in concepts}
    edges: List[Dict[str, str]] = []
    seen = set()
    for concept in concepts:
        target = str(concept.get("concept_id"))
        for raw in concept.get("prerequisites") or []:
            source = by_id.get(str(raw)) or by_name.get(_norm(raw))
            if not source or source == target:
                continue
            key = (source, target, "prerequisite")
            if key in seen:
                continue
            seen.add(key)
            edges.append({"from_concept_id": source, "to_concept_id": target, "relation_type": "prerequisite"})
    return edges


def _topological_order(concepts: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]]) -> Tuple[List[str], bool]:
    ids = [str(item.get("concept_id")) for item in concepts]
    indegree = {item: 0 for item in ids}
    outgoing: Dict[str, List[str]] = {item: [] for item in ids}
    for edge in edges:
        source = str(edge.get("from_concept_id"))
        target = str(edge.get("to_concept_id"))
        if source in indegree and target in indegree:
            outgoing[source].append(target)
            indegree[target] += 1
    queue = [item for item in ids if indegree[item] == 0]
    order: List[str] = []
    while queue:
        current = queue.pop(0)
        order.append(current)
        for target in outgoing[current]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    has_cycle = len(order) != len(ids)
    if has_cycle:
        for item in ids:
            if item not in order:
                order.append(item)
    return order, has_cycle


def _bloom_profile(difficulty: str, position: int) -> Tuple[str, str, str]:
    level = str(difficulty or "introductory").lower()
    if level in {"advanced", "expert", "complex"}:
        pairs = [("analyze", "يحلّل", "analyser"), ("evaluate", "يقيّم", "évaluer"), ("create", "ينشئ", "créer")]
    elif level in {"intermediate", "moderate"}:
        pairs = [("apply", "يطبّق", "appliquer"), ("analyze", "يحلّل", "analyser"), ("explain", "يفسّر", "expliquer")]
    else:
        pairs = [("identify", "يحدّد", "identifier"), ("explain", "يفسّر", "expliquer"), ("apply", "يطبّق", "appliquer")]
    return pairs[position % len(pairs)]


def _localized_activity(lang: str, lesson_id: str, outcome_id: str, concept_names: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if lang == "ar":
        activity = {
            "activity_id": f"A-{lesson_id}-{outcome_id}",
            "title": f"تطبيق موجّه: {concept_names}",
            "type": "guided_practice",
            "instructions": "ينفذ المتعلم محاولة أولى، ثم يحصل على تلميحات تدريجية قبل عرض نموذج الحل.",
        }
        assessment = {
            "assessment_id": f"AS-{lesson_id}-{outcome_id}",
            "title": f"تقويم تكويني: {concept_names}",
            "type": "formative_task",
            "success_criterion": "تحقيق 75% على الأقل مع تفسير الاختيار أو خطوات التنفيذ.",
        }
    elif lang == "fr":
        activity = {
            "activity_id": f"A-{lesson_id}-{outcome_id}",
            "title": f"Pratique guidée : {concept_names}",
            "type": "guided_practice",
            "instructions": "L’apprenant tente d’abord la tâche puis reçoit des indices progressifs avant le modèle de solution.",
        }
        assessment = {
            "assessment_id": f"AS-{lesson_id}-{outcome_id}",
            "title": f"Évaluation formative : {concept_names}",
            "type": "formative_task",
            "success_criterion": "Atteindre au moins 75 % et justifier la réponse ou les étapes.",
        }
    else:
        activity = {
            "activity_id": f"A-{lesson_id}-{outcome_id}",
            "title": f"Guided practice: {concept_names}",
            "type": "guided_practice",
            "instructions": "The learner attempts the task first and receives progressive hints before a model solution is shown.",
        }
        assessment = {
            "assessment_id": f"AS-{lesson_id}-{outcome_id}",
            "title": f"Formative assessment: {concept_names}",
            "type": "formative_task",
            "success_criterion": "Reach at least 75% and justify the answer or implementation steps.",
        }
    return activity, assessment


def _lesson_sequence(lang: str) -> List[str]:
    # Use the same canonical id as the lesson-block engine. Older approved
    # blueprints that contain ``concept_explanation`` remain supported by the
    # runtime compatibility mapping in db.py.
    return [
        "activation",
        "explanation",
        "worked_example",
        "guided_practice",
        "independent_practice",
        "formative_assessment",
        "summary",
    ]


def _lesson_title(lang: str, names: Sequence[str], index: int) -> str:
    joined = " و ".join(names) if lang == "ar" else (" et ".join(names) if lang == "fr" else " and ".join(names))
    prefix = {"ar": "درس", "fr": "Leçon", "en": "Lesson"}[lang]
    return f"{prefix} {index}: {joined}"


def _unit_title(lang: str, first_name: str, index: int) -> str:
    prefix = {"ar": "الوحدة", "fr": "Unité", "en": "Unit"}[lang]
    return f"{prefix} {index}: {first_name}"


def _parse_duration_minutes(project: Mapping[str, Any], lesson_count: int) -> int:
    text = str(project.get("expected_duration") or "")
    numbers = [int(item) for item in re.findall(r"\d+", text)]
    total = numbers[0] if numbers else lesson_count * 45
    if "hour" in text.lower() or "ساعة" in text or "heure" in text.lower():
        total *= 60
    return max(20, int(math.ceil(total / max(1, lesson_count))))


def compile_deterministic_blueprint(
    project: Mapping[str, Any],
    evidence_bundle: Mapping[str, Any],
    *,
    max_units: Optional[int] = None,
    max_lessons: Optional[int] = None,
) -> BlueprintResult:
    cfg = blueprint_status()
    max_units = max(1, int(max_units or cfg["max_units"]))
    max_lessons = max(2, int(max_lessons or cfg["max_lessons"]))
    raw_concept_count = len(list(evidence_bundle.get("concepts") or []))
    concepts = _concept_records(evidence_bundle)
    safe_evidence_concept_count = len(concepts)
    rejected_identity_count = max(0, raw_concept_count - safe_evidence_concept_count)
    evidence_run_id = int(evidence_bundle.get("id") or 0)
    evidence_rebuild_required = bool(
        raw_concept_count > 0
        and safe_evidence_concept_count == 0
        and rejected_identity_count == raw_concept_count
    )
    if not concepts:
        concepts = _project_fallback_concept_records(project, evidence_bundle)
    if not concepts:
        raise ValueError(
            "The approved evidence bundle does not contain safe teachable concepts. "
            "Review the target concept or regenerate evidence synthesis."
        )

    edges = build_concept_edges(concepts)
    order, has_cycle = _topological_order(concepts, edges)
    by_id = {str(item["concept_id"]): item for item in concepts}
    ordered = [by_id[item] for item in order if item in by_id]

    # Two related concepts per lesson produces a compact but editable scaffold.
    concepts_per_lesson = 2 if len(ordered) > 2 else 1
    chunks = [ordered[i : i + concepts_per_lesson] for i in range(0, len(ordered), concepts_per_lesson)]
    chunks = chunks[:max_lessons]
    lesson_count = len(chunks)
    unit_count = min(max_units, max(1, int(math.ceil(lesson_count / 3))))
    lessons_per_unit = int(math.ceil(lesson_count / unit_count))
    duration = _parse_duration_minutes(project, lesson_count)
    lang = _lang(project)

    units: List[Dict[str, Any]] = []
    lessons: List[Dict[str, Any]] = []
    outcomes: List[Dict[str, Any]] = []
    alignments: List[Dict[str, Any]] = []
    all_sources = set()
    covered_concepts = set()

    for lesson_index, chunk in enumerate(chunks, start=1):
        unit_index = min(unit_count, int(math.ceil(lesson_index / lessons_per_unit)))
        unit_id = f"U{unit_index}"
        lesson_id = f"L{lesson_index}"
        concept_ids = [str(item["concept_id"]) for item in chunk]
        concept_names = [str(item["name"]) for item in chunk]
        source_ids = sorted({sid for item in chunk for sid in item.get("source_ids") or []})
        all_sources.update(source_ids)
        covered_concepts.update(concept_ids)
        prerequisites = sorted(
            {
                str(value)
                for item in chunk
                for value in item.get("prerequisites") or []
                if str(value).strip()
            }
        )
        misconceptions = []
        for card in evidence_bundle.get("evidence_cards") or []:
            uses = {str(item).lower() for item in card.get("intended_use") or []}
            if "misconception" in uses:
                misconceptions.append(str(card.get("claim") or card.get("claim_text") or ""))
        misconceptions = [item for item in misconceptions if item][:3]

        lesson_outcomes: List[Dict[str, Any]] = []
        activities: List[Dict[str, Any]] = []
        assessments: List[Dict[str, Any]] = []
        for outcome_position in range(2):
            outcome_id = f"LO{lesson_index}.{outcome_position + 1}"
            en_verb, ar_verb, fr_verb = _bloom_profile(chunk[-1].get("difficulty"), outcome_position)
            verb = {"ar": ar_verb, "fr": fr_verb, "en": en_verb}[lang]
            object_text = (
                "العلاقة بين " + " و".join(concept_names)
                if lang == "ar"
                else ("la relation entre " + " et ".join(concept_names) if lang == "fr" else "the relationship between " + " and ".join(concept_names))
            )
            activity, assessment = _localized_activity(lang, lesson_id, outcome_id, ", ".join(concept_names))
            outcome = {
                "outcome_id": outcome_id,
                "lesson_id": lesson_id,
                "bloom_level": en_verb,
                "verb": verb,
                "object": object_text,
                "condition": {"ar": "بعد دراسة الشرح وتنفيذ المثال الموجّه", "fr": "après l’explication et l’exemple guidé", "en": "after the explanation and guided example"}[lang],
                "success_criterion": assessment["success_criterion"],
                "activity_id": activity["activity_id"],
                "assessment_id": assessment["assessment_id"],
            }
            lesson_outcomes.append(outcome)
            outcomes.append(outcome)
            activities.append(activity)
            assessments.append(assessment)
            alignments.append(
                {
                    "outcome_id": outcome_id,
                    "lesson_id": lesson_id,
                    "activity_id": activity["activity_id"],
                    "assessment_id": assessment["assessment_id"],
                    "aligned": True,
                }
            )

        lesson = {
            "lesson_id": lesson_id,
            "unit_id": unit_id,
            "title": _lesson_title(lang, concept_names, lesson_index),
            "sequence_order": lesson_index,
            "estimated_duration_minutes": duration,
            "prerequisites": prerequisites,
            "concept_ids": concept_ids,
            "source_ids": source_ids,
            "learning_outcomes": lesson_outcomes,
            "misconceptions": misconceptions,
            "lesson_sequence": _lesson_sequence(lang),
            "activities": activities,
            "assessments": assessments,
            "status": "teacher_review",
        }
        lessons.append(lesson)

    for unit_index in range(1, unit_count + 1):
        unit_lessons = [item for item in lessons if item["unit_id"] == f"U{unit_index}"]
        unit_concepts = [cid for item in unit_lessons for cid in item["concept_ids"]]
        first_name = by_id.get(unit_concepts[0], {}).get("name", str(project.get("unit_title") or "Course")) if unit_concepts else str(project.get("unit_title") or "Course")
        units.append(
            {
                "unit_id": f"U{unit_index}",
                "title": _unit_title(lang, str(first_name), unit_index),
                "description": _title(project.get("target_concept"), str(project.get("unit_title") or "")),
                "sequence_order": unit_index,
                "lesson_ids": [item["lesson_id"] for item in unit_lessons],
                "concept_ids": sorted(set(unit_concepts)),
                "source_ids": sorted({sid for item in unit_lessons for sid in item["source_ids"]}),
            }
        )

    coverage = len(covered_concepts) / max(1, len(concepts))
    aligned_count = sum(1 for item in alignments if item.get("aligned"))
    alignment_rate = aligned_count / max(1, len(outcomes))
    source_traceability = sum(1 for item in lessons if item.get("source_ids")) / max(1, len(lessons))
    orphan_concepts = [item["concept_id"] for item in concepts if item["concept_id"] not in covered_concepts]
    warnings: List[str] = []
    if has_cycle:
        warnings.append("The concept prerequisite graph contains a cycle and requires teacher review.")
    if orphan_concepts:
        warnings.append("Some concepts were not allocated to lessons: " + ", ".join(orphan_concepts))
    if source_traceability < 1.0:
        warnings.append("At least one lesson has no linked source identifier.")
    if not all_sources:
        warnings.append("The blueprint contains no traceable source identifiers.")
    if rejected_identity_count:
        warnings.append(
            f"Rejected {rejected_identity_count} source-like concept name(s) before blueprint construction."
        )
    if evidence_rebuild_required:
        warnings.append(
            "All evidence concepts were rejected as source/reference metadata. Rebuild evidence before blueprint approval."
        )

    readiness = 0.35 * coverage + 0.35 * alignment_rate + 0.20 * source_traceability + 0.10 * (0.0 if has_cycle else 1.0)
    readiness = round(max(0.0, min(1.0, readiness)), 3)
    minimum = float(cfg.get("minimum_readiness") or 0.70)
    status = (
        "completed"
        if readiness >= minimum and not has_cycle and not evidence_rebuild_required
        else "needs_review"
    )
    quality = {
        "readiness_score": readiness,
        "concept_coverage": round(coverage, 3),
        "alignment_rate": round(alignment_rate, 3),
        "source_traceability": round(source_traceability, 3),
        "unit_count": len(units),
        "lesson_count": len(lessons),
        "outcome_count": len(outcomes),
        "edge_count": len(edges),
        "has_prerequisite_cycle": has_cycle,
        "orphan_concepts": orphan_concepts,
        "identity_error_count": 0,
        "rejected_source_like_concepts": rejected_identity_count,
        "safe_evidence_concept_count": safe_evidence_concept_count,
        "evidence_rebuild_required": evidence_rebuild_required,
        "warnings": warnings,
    }
    blueprint = {
        "schema_version": "3alimnia.lesson-blueprint.v1",
        "project_id": int(project.get("id") or 0),
        "course_title": _title(project.get("project_name"), str(project.get("program_name") or "Course")),
        "program_name": str(project.get("program_name") or ""),
        "primary_language_code": lang,
        "target_learners": str(project.get("target_learners") or ""),
        "learner_level": str(project.get("learner_level") or ""),
        "evidence_run_id": evidence_run_id,
        "concepts": concepts,
        "concept_edges": edges,
        "units": units,
        "lessons": lessons,
        "outcomes": outcomes,
        "alignments": alignments,
        "status": "teacher_review",
    }
    return BlueprintResult(
        blueprint=blueprint,
        quality=quality,
        provider="deterministic",
        model="evidence-blueprint-compiler-v1",
        status=status,
        diagnostic="Deterministic blueprint compiled from teacher-approved concepts and sources.",
        evidence_run_id=evidence_run_id,
    )


def generate_and_persist(
    project: Mapping[str, Any],
    teacher_username: str,
    *,
    evidence_bundle: Optional[Mapping[str, Any]] = None,
    max_units: Optional[int] = None,
    max_lessons: Optional[int] = None,
) -> Dict[str, Any]:
    project_id = int(project.get("id") or 0)
    if project_id <= 0:
        raise ValueError("A saved teacher project is required before building a lesson blueprint.")
    owner = str(teacher_username or "").strip()
    saved = db.get_teacher_project(project_id, owner)
    if not saved:
        raise ValueError("Teacher project not found or access denied.")
    bundle = dict(evidence_bundle or db.latest_teacher_evidence_for_project(project_id, approved_only=True) or {})
    if not bundle or not bool(int(bundle.get("approved_by_teacher") or 0)):
        raise ValueError("Approve an evidence bundle before building the lesson blueprint.")
    result = compile_deterministic_blueprint(saved, bundle, max_units=max_units, max_lessons=max_lessons)
    run_id = db.save_teacher_blueprint_bundle(
        project_id=project_id,
        evidence_run_id=result.evidence_run_id,
        blueprint=result.blueprint,
        quality=result.quality,
        prompt_text=result.prompt_text,
        response_text=result.response_text,
        provider=result.provider,
        model=result.model,
        status=result.status,
        diagnostic=result.diagnostic,
        latency_ms=result.latency_ms,
        is_fallback_used=result.used_fallback,
        version_number=1,
        change_summary="Generated from the approved evidence bundle.",
        edited_by=owner,
        revision_type="generated",
    )
    db.record_teacher_blueprint_audit(
        project_id=project_id,
        blueprint_run_id=run_id,
        parent_run_id=None,
        action="generate",
        actor_username=owner,
        summary="Generated from the approved evidence bundle.",
        details={
            "entity_type": "blueprint",
            "entity_id": str(run_id),
            "before": {},
            "after": result.blueprint,
        },
    )
    return db.teacher_blueprint_bundle(run_id) or {"id": run_id, **result.blueprint, "quality": result.quality}



def _split_values(value: Any) -> List[str]:
    if isinstance(value, (list, tuple, set)):
        values = [str(item).strip() for item in value]
    else:
        values = [item.strip() for item in re.split(r"[,;\n]+", str(value or ""))]
    return [item for item in values if item]


def _next_identifier(prefix: str, used: set[str]) -> str:
    index = 1
    while f"{prefix}{index}" in used:
        index += 1
    value = f"{prefix}{index}"
    used.add(value)
    return value


def editor_tables_from_blueprint(blueprint: Mapping[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    concepts = []
    for item in blueprint.get("concepts") or []:
        concepts.append({
            "concept_id": item.get("concept_id"),
            "name": item.get("name"),
            "description": item.get("description"),
            "difficulty": item.get("difficulty"),
            "prerequisites": ", ".join(item.get("prerequisites") or []),
            "source_ids": ", ".join(item.get("source_ids") or []),
        })
    units = []
    for item in blueprint.get("units") or []:
        units.append({
            "unit_id": item.get("unit_id"),
            "sequence_order": item.get("sequence_order"),
            "title": item.get("title"),
            "description": item.get("description"),
        })
    lessons = []
    for item in blueprint.get("lessons") or []:
        lessons.append({
            "lesson_id": item.get("lesson_id"),
            "unit_id": item.get("unit_id"),
            "sequence_order": item.get("sequence_order"),
            "title": item.get("title"),
            "duration_minutes": item.get("estimated_duration_minutes"),
            "concept_ids": ", ".join(item.get("concept_ids") or []),
            "source_ids": ", ".join(item.get("source_ids") or []),
            "prerequisites": ", ".join(item.get("prerequisites") or []),
            "misconceptions": " | ".join(item.get("misconceptions") or []),
        })
    outcomes = []
    for item in blueprint.get("outcomes") or []:
        outcomes.append({
            "outcome_id": item.get("outcome_id"),
            "lesson_id": item.get("lesson_id"),
            "bloom_level": item.get("bloom_level"),
            "verb": item.get("verb"),
            "object": item.get("object"),
            "condition": item.get("condition"),
            "success_criterion": item.get("success_criterion"),
            "activity_id": item.get("activity_id"),
            "assessment_id": item.get("assessment_id"),
        })
    return {"concepts": concepts, "units": units, "lessons": lessons, "outcomes": outcomes}


def blueprint_from_editor_tables(
    base_blueprint: Mapping[str, Any],
    *,
    concepts: Sequence[Mapping[str, Any]],
    units: Sequence[Mapping[str, Any]],
    lessons: Sequence[Mapping[str, Any]],
    outcomes: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    draft = copy.deepcopy(dict(base_blueprint or {}))
    draft["concepts"] = [dict(item) for item in concepts]
    draft["units"] = [dict(item) for item in units]
    draft["lessons"] = [dict(item) for item in lessons]
    draft["outcomes"] = [dict(item) for item in outcomes]
    return draft




def _blueprint_payload(value: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Return a detached blueprint dictionary from a run bundle or raw payload."""

    raw = dict(value or {})
    nested = raw.get("blueprint")
    if isinstance(nested, Mapping):
        raw = dict(nested)
    return copy.deepcopy(raw)


def normalize_blueprint(value: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Normalize the mutable editor representation without requiring a project.

    This is deliberately structural. Project-aware localization and default
    learning outcomes remain the responsibility of ``normalize_manual_blueprint``
    immediately before an immutable revision is persisted.
    """

    draft = _blueprint_payload(value)
    for field in ("concepts", "concept_edges", "units", "lessons", "outcomes", "alignments"):
        items = draft.get(field)
        draft[field] = [dict(item) for item in items] if isinstance(items, list) else []

    # Concepts.
    concepts: List[Dict[str, Any]] = []
    used_concepts: set[str] = set()
    for raw in draft["concepts"]:
        concept_id = str(raw.get("concept_id") or "").strip() or _next_identifier("C", used_concepts)
        used_concepts.add(concept_id)
        item = dict(raw)
        item["concept_id"] = concept_id
        item["name"] = str(item.get("name") or concept_id).strip()
        item["prerequisites"] = _split_values(item.get("prerequisites"))
        item["source_ids"] = _split_values(item.get("source_ids"))
        concepts.append(item)
    draft["concepts"] = concepts

    # Units.
    units: List[Dict[str, Any]] = []
    used_units: set[str] = set()
    for position, raw in enumerate(draft["units"], start=1):
        unit_id = str(raw.get("unit_id") or "").strip() or _next_identifier("U", used_units)
        used_units.add(unit_id)
        item = dict(raw)
        item.update({
            "unit_id": unit_id,
            "title": str(item.get("title") or unit_id).strip(),
            "description": str(item.get("description") or "").strip(),
            "sequence_order": int(item.get("sequence_order") or position),
        })
        units.append(item)
    units.sort(key=lambda item: (int(item.get("sequence_order") or 0), str(item.get("unit_id"))))
    for position, item in enumerate(units, start=1):
        item["sequence_order"] = position
    draft["units"] = units
    unit_ids = {str(item["unit_id"]) for item in units}

    # Lessons.
    lessons: List[Dict[str, Any]] = []
    used_lessons: set[str] = set()
    fallback_unit = units[0]["unit_id"] if units else ""
    for position, raw in enumerate(draft["lessons"], start=1):
        lesson_id = str(raw.get("lesson_id") or "").strip() or _next_identifier("L", used_lessons)
        used_lessons.add(lesson_id)
        item = dict(raw)
        unit_id = str(item.get("unit_id") or fallback_unit).strip()
        item.update({
            "lesson_id": lesson_id,
            "unit_id": unit_id,
            "title": str(item.get("title") or lesson_id).strip(),
            "sequence_order": int(item.get("sequence_order") or position),
            "estimated_duration_minutes": max(5, int(item.get("estimated_duration_minutes") or item.get("duration_minutes") or 45)),
            "concept_ids": _split_values(item.get("concept_ids")),
            "source_ids": _split_values(item.get("source_ids")),
            "prerequisites": _split_values(item.get("prerequisites")),
            "misconceptions": _split_values(str(item.get("misconceptions") or "").replace("|", ",")),
            "lesson_sequence": list(item.get("lesson_sequence") or []),
            "activities": [dict(row) for row in item.get("activities") or []],
            "assessments": [dict(row) for row in item.get("assessments") or []],
            "learning_outcomes": [],
            "status": str(item.get("status") or "teacher_review"),
        })
        lessons.append(item)
    unit_order = {str(item["unit_id"]): int(item["sequence_order"]) for item in units}
    lessons.sort(key=lambda item: (unit_order.get(str(item.get("unit_id")), 999), int(item.get("sequence_order") or 0), str(item.get("lesson_id"))))
    per_unit: Dict[str, int] = {}
    for item in lessons:
        uid = str(item.get("unit_id") or "")
        per_unit[uid] = per_unit.get(uid, 0) + 1
        item["sequence_order"] = per_unit[uid]
    draft["lessons"] = lessons
    lesson_ids = {str(item["lesson_id"]) for item in lessons}

    # Outcomes and alignment references.
    outcomes: List[Dict[str, Any]] = []
    used_outcomes: set[str] = set()
    for raw in draft["outcomes"]:
        item = dict(raw)
        lesson_id = str(item.get("lesson_id") or "").strip()
        outcome_id = str(item.get("outcome_id") or "").strip() or _next_identifier("LO", used_outcomes)
        used_outcomes.add(outcome_id)
        item.update({
            "outcome_id": outcome_id,
            "lesson_id": lesson_id,
            "bloom_level": str(item.get("bloom_level") or "apply").strip(),
            "verb": str(item.get("verb") or "apply").strip(),
            "object": str(item.get("object") or item.get("object_text") or "").strip(),
            "condition": str(item.get("condition") or item.get("condition_text") or "").strip(),
            "success_criterion": str(item.get("success_criterion") or "").strip(),
            "activity_id": str(item.get("activity_id") or f"A-{lesson_id}-{outcome_id}").strip(),
            "assessment_id": str(item.get("assessment_id") or f"AS-{lesson_id}-{outcome_id}").strip(),
        })
        outcomes.append(item)
    draft["outcomes"] = outcomes

    lesson_map = {str(item["lesson_id"]): item for item in lessons}
    alignments: List[Dict[str, Any]] = []
    for outcome in outcomes:
        lesson = lesson_map.get(str(outcome.get("lesson_id") or ""))
        if lesson is not None:
            lesson["learning_outcomes"].append(outcome)
        alignments.append({
            "outcome_id": outcome["outcome_id"],
            "lesson_id": outcome["lesson_id"],
            "activity_id": outcome["activity_id"],
            "assessment_id": outcome["assessment_id"],
            "aligned": bool(outcome.get("lesson_id") in lesson_ids),
        })
    draft["alignments"] = alignments

    # Rebuild unit aggregates after every edit.
    for unit in units:
        linked = [lesson for lesson in lessons if str(lesson.get("unit_id")) == str(unit.get("unit_id"))]
        unit["lesson_ids"] = [str(lesson["lesson_id"]) for lesson in linked]
        unit["concept_ids"] = sorted({cid for lesson in linked for cid in lesson.get("concept_ids") or []})
        unit["source_ids"] = sorted({sid for lesson in linked for sid in lesson.get("source_ids") or []})

    # Keep only structurally valid prerequisite edges; quality reporting still
    # exposes any dangling lesson/outcome references to the teacher.
    draft["concept_edges"] = [dict(edge) for edge in draft.get("concept_edges") or []]
    return draft


def prepare_editor_draft(bundle_or_blueprint: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Create an isolated, mutable session draft for the blueprint editor."""

    return normalize_blueprint(bundle_or_blueprint)


def recompute_blueprint_quality(draft: Mapping[str, Any]) -> Dict[str, Any]:
    quality = assess_blueprint_quality(normalize_blueprint(draft))
    structural_errors = (
        bool(quality.get("dangling_lessons"))
        or bool(quality.get("dangling_outcomes"))
        or bool(quality.get("duplicate_ids"))
        or bool(quality.get("has_prerequisite_cycle"))
    )
    quality["integrity_score"] = 0.0 if structural_errors else 1.0
    quality["status"] = "completed" if quality.get("readiness_score", 0) >= blueprint_status()["minimum_readiness"] and not structural_errors else "needs_review"
    return quality


def compare_blueprints(before: Mapping[str, Any], after: Mapping[str, Any]) -> Dict[str, Any]:
    left = normalize_blueprint(before)
    right = normalize_blueprint(after)
    specs = (("concepts", "concept_id"), ("units", "unit_id"), ("lessons", "lesson_id"), ("outcomes", "outcome_id"))
    result: Dict[str, Any] = {"changed": False, "changes": _diff_entity_sets(left, right)}
    for field, key in specs:
        old = _entity_map(left.get(field) or [], key)
        new = _entity_map(right.get(field) or [], key)
        added = sorted(set(new) - set(old))
        removed = sorted(set(old) - set(new))
        updated = sorted(identifier for identifier in set(old) & set(new) if old[identifier] != new[identifier])
        result[field] = {"added": added, "removed": removed, "updated": updated}
        result["changed"] = result["changed"] or bool(added or removed or updated)
    if left.get("concept_edges") != right.get("concept_edges"):
        result["changed"] = True
        result["concept_edges"] = {"updated": True}
    return result


def add_unit(draft: Mapping[str, Any], title: str, description: str = "") -> Dict[str, Any]:
    data = prepare_editor_draft(draft)
    clean_title = str(title or "").strip()
    if not clean_title:
        raise ValueError("Unit title is required.")
    used = {str(item.get("unit_id")) for item in data.get("units") or []}
    unit_id = _next_identifier("U", used)
    data["units"].append({
        "unit_id": unit_id,
        "title": clean_title,
        "description": str(description or "").strip(),
        "sequence_order": len(data["units"]) + 1,
        "lesson_ids": [], "concept_ids": [], "source_ids": [],
    })
    return normalize_blueprint(data)


def update_unit(draft: Mapping[str, Any], unit_id: str, *, title: str, description: str = "") -> Dict[str, Any]:
    data = prepare_editor_draft(draft)
    target = next((item for item in data["units"] if str(item.get("unit_id")) == str(unit_id)), None)
    if target is None:
        raise ValueError("Unit not found.")
    if not str(title or "").strip():
        raise ValueError("Unit title is required.")
    target["title"] = str(title).strip()
    target["description"] = str(description or "").strip()
    return normalize_blueprint(data)


def move_unit(draft: Mapping[str, Any], unit_id: str, offset: int) -> Dict[str, Any]:
    data = prepare_editor_draft(draft)
    units = data["units"]
    index = next((idx for idx, item in enumerate(units) if str(item.get("unit_id")) == str(unit_id)), -1)
    if index < 0:
        raise ValueError("Unit not found.")
    target = max(0, min(len(units) - 1, index + int(offset)))
    if target != index:
        units[index], units[target] = units[target], units[index]
    for position, item in enumerate(units, start=1):
        item["sequence_order"] = position
    return normalize_blueprint(data)


def delete_unit(draft: Mapping[str, Any], unit_id: str, *, cascade: bool = False) -> Dict[str, Any]:
    data = prepare_editor_draft(draft)
    if not any(str(item.get("unit_id")) == str(unit_id) for item in data["units"]):
        raise ValueError("Unit not found.")
    linked_lessons = {str(item.get("lesson_id")) for item in data["lessons"] if str(item.get("unit_id")) == str(unit_id)}
    if linked_lessons and not cascade:
        raise ValueError("The unit contains lessons. Confirm cascade deletion first.")
    data["units"] = [item for item in data["units"] if str(item.get("unit_id")) != str(unit_id)]
    if cascade:
        data["lessons"] = [item for item in data["lessons"] if str(item.get("lesson_id")) not in linked_lessons]
        data["outcomes"] = [item for item in data["outcomes"] if str(item.get("lesson_id")) not in linked_lessons]
    return normalize_blueprint(data)


def add_lesson(
    draft: Mapping[str, Any], *, unit_id: str, title: str, duration_minutes: int = 45,
    concept_ids: Any = None, source_ids: Any = None,
) -> Dict[str, Any]:
    data = prepare_editor_draft(draft)
    if str(unit_id) not in {str(item.get("unit_id")) for item in data["units"]}:
        raise ValueError("Select a valid unit before adding a lesson.")
    clean_title = str(title or "").strip()
    if not clean_title:
        raise ValueError("Lesson title is required.")
    used = {str(item.get("lesson_id")) for item in data["lessons"]}
    lesson_id = _next_identifier("L", used)
    order = 1 + sum(1 for item in data["lessons"] if str(item.get("unit_id")) == str(unit_id))
    data["lessons"].append({
        "lesson_id": lesson_id, "unit_id": str(unit_id), "title": clean_title,
        "sequence_order": order, "estimated_duration_minutes": max(5, int(duration_minutes or 45)),
        "prerequisites": [], "concept_ids": _split_values(concept_ids), "source_ids": _split_values(source_ids),
        "learning_outcomes": [], "misconceptions": [], "lesson_sequence": [],
        "activities": [], "assessments": [], "status": "teacher_review",
    })
    return normalize_blueprint(data)


def update_lesson(
    draft: Mapping[str, Any], lesson_id: str, *, unit_id: str, title: str,
    duration_minutes: int = 45, concept_ids: Any = None, source_ids: Any = None,
    prerequisites: Any = None, misconceptions: Any = None,
) -> Dict[str, Any]:
    data = prepare_editor_draft(draft)
    target = next((item for item in data["lessons"] if str(item.get("lesson_id")) == str(lesson_id)), None)
    if target is None:
        raise ValueError("Lesson not found.")
    if str(unit_id) not in {str(item.get("unit_id")) for item in data["units"]}:
        raise ValueError("Select a valid unit.")
    if not str(title or "").strip():
        raise ValueError("Lesson title is required.")
    target.update({
        "unit_id": str(unit_id), "title": str(title).strip(),
        "estimated_duration_minutes": max(5, int(duration_minutes or 45)),
        "concept_ids": _split_values(concept_ids), "source_ids": _split_values(source_ids),
        "prerequisites": _split_values(prerequisites),
        "misconceptions": _split_values(str(misconceptions or "").replace("|", ",")),
    })
    return normalize_blueprint(data)


def move_lesson(draft: Mapping[str, Any], lesson_id: str, offset: int) -> Dict[str, Any]:
    data = prepare_editor_draft(draft)
    lesson = next((item for item in data["lessons"] if str(item.get("lesson_id")) == str(lesson_id)), None)
    if lesson is None:
        raise ValueError("Lesson not found.")
    unit_id = str(lesson.get("unit_id"))
    siblings = [item for item in data["lessons"] if str(item.get("unit_id")) == unit_id]
    index = next(idx for idx, item in enumerate(siblings) if str(item.get("lesson_id")) == str(lesson_id))
    target = max(0, min(len(siblings) - 1, index + int(offset)))
    if target != index:
        siblings[index], siblings[target] = siblings[target], siblings[index]
    for position, item in enumerate(siblings, start=1):
        item["sequence_order"] = position
    return normalize_blueprint(data)


def delete_lesson(draft: Mapping[str, Any], lesson_id: str) -> Dict[str, Any]:
    data = prepare_editor_draft(draft)
    if not any(str(item.get("lesson_id")) == str(lesson_id) for item in data["lessons"]):
        raise ValueError("Lesson not found.")
    data["lessons"] = [item for item in data["lessons"] if str(item.get("lesson_id")) != str(lesson_id)]
    data["outcomes"] = [item for item in data["outcomes"] if str(item.get("lesson_id")) != str(lesson_id)]
    return normalize_blueprint(data)


def add_outcome(
    draft: Mapping[str, Any], *, lesson_id: str, bloom_level: str, verb: str,
    object_text: str, condition: str = "", success_criterion: str = "",
) -> Dict[str, Any]:
    data = prepare_editor_draft(draft)
    if str(lesson_id) not in {str(item.get("lesson_id")) for item in data["lessons"]}:
        raise ValueError("Select a valid lesson before adding an outcome.")
    if not str(verb or "").strip() or not str(object_text or "").strip():
        raise ValueError("A measurable verb and outcome object are required.")
    used = {str(item.get("outcome_id")) for item in data["outcomes"]}
    lesson_count = 1 + sum(1 for item in data["outcomes"] if str(item.get("lesson_id")) == str(lesson_id))
    suffix = str(lesson_id)[1:] if str(lesson_id).startswith("L") else str(lesson_id)
    candidate = f"LO{suffix}.{lesson_count}"
    outcome_id = candidate if candidate not in used else _next_identifier("LO", used)
    data["outcomes"].append({
        "outcome_id": outcome_id, "lesson_id": str(lesson_id),
        "bloom_level": str(bloom_level or "apply"), "verb": str(verb).strip(),
        "object": str(object_text).strip(), "condition": str(condition or "").strip(),
        "success_criterion": str(success_criterion or "").strip(),
        "activity_id": f"A-{lesson_id}-{outcome_id}",
        "assessment_id": f"AS-{lesson_id}-{outcome_id}",
    })
    return normalize_blueprint(data)


def update_outcome(
    draft: Mapping[str, Any], outcome_id: str, *, bloom_level: str, verb: str,
    object_text: str, condition: str = "", success_criterion: str = "",
) -> Dict[str, Any]:
    data = prepare_editor_draft(draft)
    target = next((item for item in data["outcomes"] if str(item.get("outcome_id")) == str(outcome_id)), None)
    if target is None:
        raise ValueError("Learning outcome not found.")
    target.update({
        "bloom_level": str(bloom_level or "apply"), "verb": str(verb or "").strip(),
        "object": str(object_text or "").strip(), "condition": str(condition or "").strip(),
        "success_criterion": str(success_criterion or "").strip(),
    })
    return normalize_blueprint(data)


def delete_outcome(draft: Mapping[str, Any], outcome_id: str) -> Dict[str, Any]:
    data = prepare_editor_draft(draft)
    if not any(str(item.get("outcome_id")) == str(outcome_id) for item in data["outcomes"]):
        raise ValueError("Learning outcome not found.")
    data["outcomes"] = [item for item in data["outcomes"] if str(item.get("outcome_id")) != str(outcome_id)]
    return normalize_blueprint(data)


def _entity_map(items: Sequence[Mapping[str, Any]], key: str) -> Dict[str, Dict[str, Any]]:
    return {str(item.get(key)): dict(item) for item in items if str(item.get(key) or "").strip()}


def _diff_entity_sets(before: Mapping[str, Any], after: Mapping[str, Any]) -> List[Dict[str, Any]]:
    specs = [
        ("concept", "concepts", "concept_id"),
        ("unit", "units", "unit_id"),
        ("lesson", "lessons", "lesson_id"),
        ("outcome", "outcomes", "outcome_id"),
    ]
    changes: List[Dict[str, Any]] = []
    for entity_type, field, key in specs:
        old = _entity_map(before.get(field) or [], key)
        new = _entity_map(after.get(field) or [], key)
        for entity_id in sorted(set(old) | set(new)):
            if entity_id not in old:
                action = "added"
            elif entity_id not in new:
                action = "removed"
            elif old[entity_id] != new[entity_id]:
                action = "updated"
            else:
                continue
            changes.append({
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "before": old.get(entity_id) or {},
                "after": new.get(entity_id) or {},
            })
    old_edges = {json.dumps(item, ensure_ascii=False, sort_keys=True) for item in before.get("concept_edges") or []}
    new_edges = {json.dumps(item, ensure_ascii=False, sort_keys=True) for item in after.get("concept_edges") or []}
    if old_edges != new_edges:
        changes.append({"action": "updated", "entity_type": "concept_graph", "entity_id": "edges", "before": {"edges": sorted(old_edges)}, "after": {"edges": sorted(new_edges)}})
    return changes


def normalize_manual_blueprint(project: Mapping[str, Any], draft: Mapping[str, Any]) -> BlueprintResult:
    cfg = blueprint_status()
    data = copy.deepcopy(dict(draft or {}))
    lang = _lang(project)

    # Concepts: preserve stable identifiers; allocate identifiers for new rows.
    concept_rows = [dict(item) for item in data.get("concepts") or [] if str(item.get("name") or "").strip()]
    used_concepts = {str(item.get("concept_id")) for item in concept_rows if str(item.get("concept_id") or "").strip()}
    concepts: List[Dict[str, Any]] = []
    seen_names = set()
    for row in concept_rows:
        name = _title(row.get("name"), "Concept")
        name_key = _norm(name)
        if name_key in seen_names:
            continue
        seen_names.add(name_key)
        concept_id = str(row.get("concept_id") or "").strip() or _next_identifier("C", used_concepts)
        concepts.append({
            "concept_id": concept_id,
            "name": name,
            "description": str(row.get("description") or "").strip(),
            "prerequisites": _split_values(row.get("prerequisites")),
            "source_ids": _split_values(row.get("source_ids")),
            "difficulty": str(row.get("difficulty") or "introductory").strip(),
        })
    concept_ids = {item["concept_id"] for item in concepts}
    by_name = {_norm(item["name"]): item["concept_id"] for item in concepts}
    for item in concepts:
        resolved = []
        for raw in item.get("prerequisites") or []:
            value = raw if raw in concept_ids else by_name.get(_norm(raw), "")
            if value and value != item["concept_id"] and value not in resolved:
                resolved.append(value)
        item["prerequisites"] = resolved
    edges = build_concept_edges(concepts)

    # Units.
    unit_rows = [dict(item) for item in data.get("units") or [] if str(item.get("title") or "").strip()]
    used_units = {str(item.get("unit_id")) for item in unit_rows if str(item.get("unit_id") or "").strip()}
    units: List[Dict[str, Any]] = []
    for position, row in enumerate(unit_rows, start=1):
        unit_id = str(row.get("unit_id") or "").strip() or _next_identifier("U", used_units)
        units.append({
            "unit_id": unit_id,
            "title": _title(row.get("title"), _unit_title(lang, str(project.get("program_name") or "Course"), position)),
            "description": str(row.get("description") or "").strip(),
            "sequence_order": int(row.get("sequence_order") or position),
            "lesson_ids": [], "concept_ids": [], "source_ids": [],
        })
    units.sort(key=lambda item: (int(item.get("sequence_order") or 0), str(item.get("unit_id"))))
    for index, item in enumerate(units, start=1):
        item["sequence_order"] = index
    if not units:
        units = [{"unit_id": "U1", "title": _unit_title(lang, str(project.get("program_name") or "Course"), 1), "description": "", "sequence_order": 1, "lesson_ids": [], "concept_ids": [], "source_ids": []}]
    unit_ids = {item["unit_id"] for item in units}

    # Lessons.
    base_lessons = _entity_map(data.get("lessons") or [], "lesson_id")
    lesson_rows = [dict(item) for item in data.get("lessons") or [] if str(item.get("title") or "").strip()]
    used_lessons = {str(item.get("lesson_id")) for item in lesson_rows if str(item.get("lesson_id") or "").strip()}
    lessons: List[Dict[str, Any]] = []
    for position, row in enumerate(lesson_rows, start=1):
        lesson_id = str(row.get("lesson_id") or "").strip() or _next_identifier("L", used_lessons)
        unit_id = str(row.get("unit_id") or "").strip()
        if unit_id not in unit_ids:
            unit_id = units[0]["unit_id"]
        cids = []
        for raw in _split_values(row.get("concept_ids")):
            value = raw if raw in concept_ids else by_name.get(_norm(raw), "")
            if value and value not in cids:
                cids.append(value)
        previous = base_lessons.get(lesson_id, {})
        lessons.append({
            "lesson_id": lesson_id,
            "unit_id": unit_id,
            "title": _title(row.get("title"), _lesson_title(lang, ["Concept"], position)),
            "sequence_order": int(row.get("sequence_order") or position),
            "estimated_duration_minutes": max(5, int(row.get("duration_minutes") or row.get("estimated_duration_minutes") or 45)),
            "prerequisites": _split_values(row.get("prerequisites")),
            "concept_ids": cids,
            "source_ids": _split_values(row.get("source_ids")),
            "learning_outcomes": [],
            "misconceptions": _split_values(str(row.get("misconceptions") or "").replace("|", ",")),
            "lesson_sequence": list(previous.get("lesson_sequence") or _lesson_sequence(lang)),
            "activities": list(previous.get("activities") or []),
            "assessments": list(previous.get("assessments") or []),
            "status": "teacher_review",
        })
    unit_order = {item["unit_id"]: int(item["sequence_order"]) for item in units}
    lessons.sort(key=lambda item: (unit_order.get(item["unit_id"], 999), int(item.get("sequence_order") or 0), str(item["lesson_id"])))
    per_unit: Dict[str, int] = {}
    for item in lessons:
        per_unit[item["unit_id"]] = per_unit.get(item["unit_id"], 0) + 1
        item["sequence_order"] = per_unit[item["unit_id"]]
    lesson_ids = {item["lesson_id"] for item in lessons}

    # Outcomes and alignment artifacts.
    outcome_rows = [dict(item) for item in data.get("outcomes") or [] if str(item.get("verb") or item.get("object") or "").strip()]
    used_outcomes = {str(item.get("outcome_id")) for item in outcome_rows if str(item.get("outcome_id") or "").strip()}
    outcomes: List[Dict[str, Any]] = []
    lesson_outcome_count: Dict[str, int] = {}
    for row in outcome_rows:
        lesson_id = str(row.get("lesson_id") or "").strip()
        if lesson_id not in lesson_ids:
            continue
        lesson_outcome_count[lesson_id] = lesson_outcome_count.get(lesson_id, 0) + 1
        outcome_id = str(row.get("outcome_id") or "").strip()
        if not outcome_id:
            suffix = lesson_id[1:] if lesson_id.startswith("L") else lesson_id
            candidate = f"LO{suffix}.{lesson_outcome_count[lesson_id]}"
            outcome_id = candidate if candidate not in used_outcomes else _next_identifier("LO", used_outcomes)
            used_outcomes.add(outcome_id)
        activity_id = str(row.get("activity_id") or f"A-{lesson_id}-{outcome_id}").strip()
        assessment_id = str(row.get("assessment_id") or f"AS-{lesson_id}-{outcome_id}").strip()
        outcomes.append({
            "outcome_id": outcome_id,
            "lesson_id": lesson_id,
            "bloom_level": str(row.get("bloom_level") or "apply").strip(),
            "verb": str(row.get("verb") or "apply").strip(),
            "object": str(row.get("object") or row.get("object_text") or "the lesson concepts").strip(),
            "condition": str(row.get("condition") or row.get("condition_text") or "after guided practice").strip(),
            "success_criterion": str(row.get("success_criterion") or "Achieve at least 75%.").strip(),
            "activity_id": activity_id,
            "assessment_id": assessment_id,
        })

    # New lessons can be created before the teacher adds explicit outcomes.
    # Give them one measurable default outcome so the draft remains aligned and editable.
    for lesson in lessons:
        if any(item.get("lesson_id") == lesson["lesson_id"] for item in outcomes):
            continue
        lesson_outcome_count[lesson["lesson_id"]] = 1
        suffix = lesson["lesson_id"][1:] if lesson["lesson_id"].startswith("L") else lesson["lesson_id"]
        outcome_id = f"LO{suffix}.1"
        if outcome_id in used_outcomes:
            outcome_id = _next_identifier("LO", used_outcomes)
        else:
            used_outcomes.add(outcome_id)
        names = [next((item["name"] for item in concepts if item["concept_id"] == cid), cid) for cid in lesson.get("concept_ids") or []]
        object_text = ", ".join(names) or lesson["title"]
        activity, assessment = _localized_activity(lang, lesson["lesson_id"], outcome_id, object_text)
        outcomes.append({
            "outcome_id": outcome_id, "lesson_id": lesson["lesson_id"], "bloom_level": "apply",
            "verb": {"ar": "يطبّق", "fr": "appliquer", "en": "apply"}[lang],
            "object": object_text,
            "condition": {"ar": "بعد الشرح والتطبيق الموجّه", "fr": "après l’explication et la pratique guidée", "en": "after explanation and guided practice"}[lang],
            "success_criterion": assessment["success_criterion"],
            "activity_id": activity["activity_id"], "assessment_id": assessment["assessment_id"],
        })

    lesson_map = {item["lesson_id"]: item for item in lessons}
    alignments = []
    for outcome in outcomes:
        lesson = lesson_map[outcome["lesson_id"]]
        lesson["learning_outcomes"].append(outcome)
        old_activity = next((item for item in lesson.get("activities") or [] if item.get("activity_id") == outcome["activity_id"]), None)
        old_assessment = next((item for item in lesson.get("assessments") or [] if item.get("assessment_id") == outcome["assessment_id"]), None)
        if not old_activity:
            old_activity = {"activity_id": outcome["activity_id"], "title": outcome["activity_id"], "type": "guided_practice", "instructions": outcome["condition"]}
        if not old_assessment:
            old_assessment = {"assessment_id": outcome["assessment_id"], "title": outcome["assessment_id"], "type": "formative_task", "success_criterion": outcome["success_criterion"]}
        lesson["activities"] = [item for item in lesson.get("activities") or [] if item.get("activity_id") != outcome["activity_id"]] + [old_activity]
        lesson["assessments"] = [item for item in lesson.get("assessments") or [] if item.get("assessment_id") != outcome["assessment_id"]] + [old_assessment]
        alignments.append({"outcome_id": outcome["outcome_id"], "lesson_id": outcome["lesson_id"], "activity_id": outcome["activity_id"], "assessment_id": outcome["assessment_id"], "aligned": True})

    for unit in units:
        linked = [item for item in lessons if item["unit_id"] == unit["unit_id"]]
        unit["lesson_ids"] = [item["lesson_id"] for item in linked]
        unit["concept_ids"] = sorted({cid for item in linked for cid in item.get("concept_ids") or []})
        unit["source_ids"] = sorted({sid for item in linked for sid in item.get("source_ids") or []})

    blueprint = {
        **{key: value for key, value in data.items() if key not in {"concepts", "concept_edges", "units", "lessons", "outcomes", "alignments"}},
        "schema_version": "3alimnia.lesson-blueprint.v1.1",
        "project_id": int(project.get("id") or data.get("project_id") or 0),
        "course_title": _title(data.get("course_title"), str(project.get("project_name") or project.get("program_name") or "Course")),
        "program_name": str(project.get("program_name") or data.get("program_name") or ""),
        "primary_language_code": lang,
        "concepts": concepts,
        "concept_edges": edges,
        "units": units,
        "lessons": lessons,
        "outcomes": outcomes,
        "alignments": alignments,
        "status": "teacher_review",
    }
    quality = assess_blueprint_quality(blueprint)
    status = "completed" if quality["readiness_score"] >= float(cfg.get("minimum_readiness") or 0.70) and not quality["has_prerequisite_cycle"] else "needs_review"
    return BlueprintResult(
        blueprint=blueprint, quality=quality, provider="manual", model="blueprint-editor-v1",
        status=status, diagnostic="Teacher-edited blueprint normalized and validated.",
        evidence_run_id=int(data.get("evidence_run_id") or 0),
    )


def assess_blueprint_quality(blueprint: Mapping[str, Any]) -> Dict[str, Any]:
    concepts = list(blueprint.get("concepts") or [])
    units = list(blueprint.get("units") or [])
    lessons = list(blueprint.get("lessons") or [])
    outcomes = list(blueprint.get("outcomes") or [])
    edges = list(blueprint.get("concept_edges") or [])
    concept_ids = {str(item.get("concept_id")) for item in concepts}
    unit_ids = {str(item.get("unit_id")) for item in units}
    lesson_ids = {str(item.get("lesson_id")) for item in lessons}
    covered = {str(cid) for item in lessons for cid in item.get("concept_ids") or [] if str(cid) in concept_ids}
    coverage = len(covered) / max(1, len(concept_ids))
    aligned = [item for item in outcomes if item.get("activity_id") and item.get("assessment_id") and str(item.get("lesson_id")) in lesson_ids]
    alignment = len(aligned) / max(1, len(outcomes))
    traceability = sum(1 for item in lessons if item.get("source_ids")) / max(1, len(lessons))
    _, has_cycle = _topological_order(concepts, edges)
    warnings: List[str] = []
    orphan = sorted(concept_ids - covered)
    dangling_lessons = [str(item.get("lesson_id")) for item in lessons if str(item.get("unit_id")) not in unit_ids]
    dangling_outcomes = [str(item.get("outcome_id")) for item in outcomes if str(item.get("lesson_id")) not in lesson_ids]
    duplicate_ids = []
    for field, key in ((concepts, "concept_id"), (units, "unit_id"), (lessons, "lesson_id"), (outcomes, "outcome_id")):
        values = [str(item.get(key)) for item in field]
        duplicate_ids.extend(sorted({value for value in values if value and values.count(value) > 1}))
    if has_cycle: warnings.append("The concept prerequisite graph contains a cycle.")
    if orphan: warnings.append("Unallocated concepts: " + ", ".join(orphan))
    if dangling_lessons: warnings.append("Lessons reference missing units: " + ", ".join(dangling_lessons))
    if dangling_outcomes: warnings.append("Outcomes reference missing lessons: " + ", ".join(dangling_outcomes))
    if duplicate_ids: warnings.append("Duplicate identifiers: " + ", ".join(sorted(set(duplicate_ids))))
    if traceability < 1.0: warnings.append("At least one lesson has no linked source identifier.")
    identity_errors: List[str] = []
    for item in concepts:
        name = str(item.get("name") or "").strip()
        if lesson_identity.is_reference_document_title(name):
            identity_errors.append(f"source_like_concept:{item.get('concept_id')}:{name[:120]}")
    for item in lessons:
        title = str(item.get("title") or "").strip()
        if lesson_identity.is_reference_document_title(title):
            identity_errors.append(f"source_like_lesson_title:{item.get('lesson_id')}:{title[:120]}")
    if identity_errors:
        warnings.append("Blueprint identity contains publication/source metadata instead of teachable concepts.")
    readiness = 0.35 * coverage + 0.35 * alignment + 0.20 * traceability + 0.10 * (0.0 if has_cycle else 1.0)
    if dangling_lessons or dangling_outcomes or duplicate_ids:
        readiness *= 0.75
    if identity_errors:
        readiness *= 0.55
    return {
        "readiness_score": round(max(0.0, min(1.0, readiness)), 3),
        "concept_coverage": round(coverage, 3),
        "alignment_rate": round(alignment, 3),
        "source_traceability": round(traceability, 3),
        "unit_count": len(units), "lesson_count": len(lessons), "outcome_count": len(outcomes), "edge_count": len(edges),
        "has_prerequisite_cycle": has_cycle, "orphan_concepts": orphan,
        "dangling_lessons": dangling_lessons, "dangling_outcomes": dangling_outcomes,
        "duplicate_ids": sorted(set(duplicate_ids)),
        "identity_error_count": len(identity_errors),
        "identity_errors": identity_errors,
        "warnings": warnings,
    }


def save_manual_revision(
    project: Mapping[str, Any] | int,
    teacher_username: str | int,
    *legacy_args: Any,
    base_run_id: Optional[int] = None,
    edited_blueprint: Optional[Mapping[str, Any]] = None,
    change_summary: str = "",
) -> Dict[str, Any]:
    """Persist a teacher-edited immutable blueprint revision.

    The V6.15 UI originally called this function with five positional values
    ``(project_id, base_run_id, username, draft, summary)``. Newer code passes
    the project mapping and keyword-only revision data. Supporting both forms
    keeps existing deployments and saved sessions functional during upgrades.
    """

    if isinstance(project, Mapping):
        project_data = dict(project)
        actor = str(teacher_username or "").strip()
        if base_run_id is None or edited_blueprint is None:
            raise TypeError("base_run_id and edited_blueprint are required.")
    else:
        project_id = int(project)
        legacy_base_run_id = int(teacher_username)
        if len(legacy_args) < 2:
            raise TypeError("Legacy save_manual_revision requires username and draft.")
        actor = str(legacy_args[0] or "").strip()
        project_data = db.get_teacher_project(project_id, actor) or {}
        base_run_id = legacy_base_run_id
        edited_blueprint = legacy_args[1]
        if len(legacy_args) >= 3 and not change_summary:
            change_summary = str(legacy_args[2] or "")

    project_id = int(project_data.get("id") or 0)
    if not project_id or not actor:
        raise ValueError("Teacher project not found or access denied.")
    base = db.teacher_blueprint_bundle(int(base_run_id))
    if not base or int(base.get("project_id") or 0) != project_id:
        raise ValueError("The selected blueprint revision does not belong to this project.")

    result = normalize_manual_blueprint(project_data, edited_blueprint or {})
    db.invalidate_teacher_blueprint_approvals(project_id)
    run_id = db.save_teacher_blueprint_bundle(
        project_id=project_id,
        evidence_run_id=int(base.get("evidence_run_id") or result.evidence_run_id or 0),
        blueprint=result.blueprint,
        quality=result.quality,
        provider=result.provider,
        model=result.model,
        status=result.status,
        diagnostic=result.diagnostic,
        parent_run_id=int(base_run_id),
        change_summary=str(change_summary or "Manual blueprint revision"),
        edited_by=actor,
        revision_type="manual_edit",
    )
    changes = _diff_entity_sets(base.get("blueprint") or {}, result.blueprint)
    db.record_teacher_blueprint_audit(
        project_id=project_id,
        blueprint_run_id=run_id,
        parent_run_id=int(base_run_id),
        action="manual_edit",
        actor_username=actor,
        summary=str(change_summary or "Manual blueprint revision"),
        details={
            "entity_type": "blueprint",
            "entity_id": str(run_id),
            "before": base.get("blueprint") or {},
            "after": result.blueprint,
        },
    )
    for change in changes:
        db.record_teacher_blueprint_audit(
            project_id=project_id,
            blueprint_run_id=run_id,
            parent_run_id=int(base_run_id),
            action=change["action"],
            actor_username=actor,
            summary=str(change_summary or ""),
            details={
                "entity_type": change["entity_type"],
                "entity_id": change["entity_id"],
                "before": change["before"],
                "after": change["after"],
            },
        )
    return db.teacher_blueprint_bundle(run_id) or {"id": run_id, "blueprint": result.blueprint, "quality": result.quality}


def restore_blueprint_as_revision(
    project: Mapping[str, Any], teacher_username: str, *, source_run_id: int, parent_run_id: int,
) -> Dict[str, Any]:
    project_id = int(project.get("id") or 0)
    source = db.teacher_blueprint_bundle(int(source_run_id))
    if not source or int(source.get("project_id") or 0) != project_id:
        raise ValueError("Historical blueprint revision not found.")
    return save_manual_revision(
        project, teacher_username, base_run_id=int(parent_run_id),
        edited_blueprint=source.get("blueprint") or {},
        change_summary=f"Restored blueprint revision #{source.get('version_number') or source_run_id} as a new draft.",
    )

def build_blueprint_packet(bundle: Mapping[str, Any], max_chars: int = 16000) -> str:
    if not bundle:
        return ""
    blueprint = bundle.get("blueprint") or bundle.get("blueprint_json_data") or {}
    units = blueprint.get("units") or bundle.get("units") or []
    lessons = blueprint.get("lessons") or bundle.get("lessons") or []
    outcomes = blueprint.get("outcomes") or bundle.get("outcomes") or []
    edges = blueprint.get("concept_edges") or bundle.get("concept_edges") or []
    lines = [
        "<teacher_approved_lesson_blueprint>",
        f"- Blueprint run: {bundle.get('id') or 'unknown'}",
        f"- Evidence run: {bundle.get('evidence_run_id') or blueprint.get('evidence_run_id') or 'unknown'}",
        f"- Status: {bundle.get('status') or blueprint.get('status') or 'unknown'}",
        "- This blueprint is a teacher-approved planning constraint. Preserve identifiers and alignment.",
    ]
    if edges:
        lines.append("## Concept prerequisite edges")
        for edge in edges[:30]:
            lines.append(f"- {edge.get('from_concept_id')} -> {edge.get('to_concept_id')} ({edge.get('relation_type') or 'prerequisite'})")
    lines.append("## Units and lessons")
    by_lesson = {str(item.get("lesson_id")): item for item in lessons}
    for unit in units[:12]:
        lines.append(f"- {unit.get('unit_id')}: {unit.get('title')} | concepts={','.join(unit.get('concept_ids') or [])}")
        for lesson_id in unit.get("lesson_ids") or []:
            lesson = by_lesson.get(str(lesson_id), {})
            lines.append(
                f"  - {lesson.get('lesson_id')}: {lesson.get('title')} | duration={lesson.get('estimated_duration_minutes')} | "
                f"concepts={','.join(lesson.get('concept_ids') or [])} | sources={','.join(lesson.get('source_ids') or [])}"
            )
    lines.append("## Learning-outcome alignment")
    for outcome in outcomes[:80]:
        lines.append(
            f"- {outcome.get('outcome_id')} ({outcome.get('lesson_id')}): {outcome.get('verb')} {outcome.get('object')} | "
            f"activity={outcome.get('activity_id')} | assessment={outcome.get('assessment_id')} | criterion={outcome.get('success_criterion')}"
        )
    lines.append("</teacher_approved_lesson_blueprint>")
    packet = "\n".join(lines)
    return packet[: max(1000, int(max_chars))]
