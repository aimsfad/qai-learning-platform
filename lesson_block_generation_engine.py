"""V6.16 lesson-block generation engine for 3alimnIA.

Generates, validates, persists, edits, versions, and approves individual
lesson blocks constrained by an approved lesson blueprint.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import streamlit as st

import content_generation_engine
import db

BLOCK_SPECS: Dict[str, Dict[str, Any]] = {
    "activation": {"order": 10, "label_ar": "تنشيط المعارف السابقة", "label_en": "Prior-knowledge activation", "min_words": 45, "max_tokens": 1100},
    "explanation": {"order": 20, "label_ar": "شرح المفهوم", "label_en": "Concept explanation", "min_words": 140, "max_tokens": 2400},
    "worked_example": {"order": 30, "label_ar": "مثال محلول", "label_en": "Worked example", "min_words": 90, "max_tokens": 1800},
    "guided_practice": {"order": 40, "label_ar": "تدريب موجه", "label_en": "Guided practice", "min_words": 70, "max_tokens": 1600},
    "independent_practice": {"order": 50, "label_ar": "تدريب مستقل", "label_en": "Independent practice", "min_words": 55, "max_tokens": 1400},
    "misconceptions": {"order": 60, "label_ar": "الأخطاء الشائعة ومعالجتها", "label_en": "Misconceptions and remediation", "min_words": 55, "max_tokens": 1400},
    "formative_assessment": {"order": 70, "label_ar": "تقويم تكويني", "label_en": "Formative assessment", "min_words": 65, "max_tokens": 1600},
    "summary": {"order": 80, "label_ar": "ملخص الدرس", "label_en": "Lesson summary", "min_words": 45, "max_tokens": 1000},
    "resources": {"order": 90, "label_ar": "موارد ومتابعة", "label_en": "Resources and follow-up", "min_words": 35, "max_tokens": 900},
}


def _secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def _as_bool(name: str, default: bool = False) -> bool:
    return _secret(name, "true" if default else "false").strip().lower() in {"1", "true", "yes", "on"}


def block_generation_status() -> Dict[str, Any]:
    return {
        "enabled": _as_bool("ENABLE_LESSON_BLOCK_GENERATION", True),
        "require_approval": _as_bool("REQUIRE_BLOCK_APPROVAL_FOR_LESSON_COMPLETION", True),
        "require_sequence": _as_bool("LESSON_BLOCK_REQUIRE_SEQUENCE", True),
        "block_count": len(BLOCK_SPECS),
    }


def block_label(block_type: str, language_code: str = "ar") -> str:
    spec = BLOCK_SPECS.get(str(block_type), {})
    return str(spec.get("label_ar") if language_code == "ar" else spec.get("label_en") or block_type)


def ordered_block_types() -> List[str]:
    """Return the canonical lesson-block order used by UI and persistence."""

    return [
        key
        for key, _ in sorted(
            BLOCK_SPECS.items(),
            key=lambda item: int(item[1].get("order") or 0),
        )
    ]


def lesson_block_state(
    project_id: int,
    lesson_id: str,
    language_code: str = "ar",
) -> List[Dict[str, Any]]:
    """Build a complete state map for the nine lesson blocks.

    The UI should never infer state from the existence of a row alone: the
    latest revision can be generated, under review, failed, or approved.  This
    helper exposes one normalized state object per canonical block.
    """

    latest = db.latest_lesson_blocks_by_type(int(project_id), str(lesson_id))
    require_sequence = bool(block_generation_status().get("require_sequence"))
    rows: List[Dict[str, Any]] = []
    prior_approved = True

    for block_type in ordered_block_types():
        spec = BLOCK_SPECS[block_type]
        run = dict(latest.get(block_type) or {})
        approved = bool(int(run.get("approved_by_teacher") or 0))
        raw_status = str(run.get("status") or "").strip().lower()

        if approved:
            state = "approved"
        elif run and raw_status in {"error", "failed"}:
            state = "failed"
        elif run and raw_status in {"running", "queued", "retrying"}:
            state = raw_status
        elif run:
            state = "needs_review"
        else:
            state = "not_started"

        locked = bool(require_sequence and not prior_approved and not run)
        rows.append(
            {
                "block_type": block_type,
                "order": int(spec.get("order") or 0),
                "label": block_label(block_type, language_code),
                "state": state,
                "locked": locked,
                "approved": approved,
                "run_id": int(run.get("id") or 0) or None,
                "version_number": int(run.get("version_number") or 0) or None,
                "word_count": int(run.get("word_count") or 0),
                "updated_at": run.get("created_at"),
                "run": run,
            }
        )
        prior_approved = prior_approved and approved

    return rows


def next_incomplete_block(project_id: int, lesson_id: str) -> Optional[str]:
    for row in lesson_block_state(int(project_id), str(lesson_id), "en"):
        if not bool(row.get("approved")):
            return str(row.get("block_type"))
    return None


def can_generate_block(project_id: int, lesson_id: str, block_type: str) -> Dict[str, Any]:
    """Return whether a block can be generated under the guided sequence."""

    requested = str(block_type)
    rows = lesson_block_state(int(project_id), str(lesson_id), "en")
    target = next((row for row in rows if row.get("block_type") == requested), None)
    if target is None:
        return {"allowed": False, "reason": "unsupported_block_type"}
    if not block_generation_status().get("require_sequence"):
        return {"allowed": True, "reason": "sequence_disabled"}
    if target.get("approved") or target.get("run"):
        return {"allowed": True, "reason": "existing_block_revision"}
    if target.get("locked"):
        previous = next((row for row in reversed(rows[: rows.index(target)]) if not row.get("approved")), None)
        return {
            "allowed": False,
            "reason": "previous_block_requires_approval",
            "required_block_type": (previous or {}).get("block_type"),
        }
    return {"allowed": True, "reason": "next_block"}


def _index_by(items: List[Dict[str, Any]], key: str) -> Dict[str, Dict[str, Any]]:
    return {str(item.get(key)): item for item in items if item.get(key)}


def lesson_context(blueprint_bundle: Dict[str, Any], lesson_id: str) -> Dict[str, Any]:
    blueprint = dict(blueprint_bundle.get("blueprint") or {})
    lessons = _index_by(list(blueprint.get("lessons") or []), "lesson_id")
    outcomes = [item for item in list(blueprint.get("outcomes") or []) if str(item.get("lesson_id")) == str(lesson_id)]
    concepts = _index_by(list(blueprint.get("concepts") or []), "concept_id")
    lesson = lessons.get(str(lesson_id))
    if not lesson:
        raise ValueError("Lesson not found in the approved blueprint.")
    concept_rows = [concepts[cid] for cid in lesson.get("concept_ids") or [] if cid in concepts]
    return {"lesson": lesson, "outcomes": outcomes, "concepts": concept_rows}


def build_block_prompt(
    project: Dict[str, Any],
    blueprint_bundle: Dict[str, Any],
    lesson_id: str,
    block_type: str,
    *,
    previous_blocks: Optional[List[Dict[str, Any]]] = None,
) -> str:
    if block_type not in BLOCK_SPECS:
        raise ValueError(f"Unsupported block type: {block_type}")
    ctx = lesson_context(blueprint_bundle, lesson_id)
    lesson = ctx["lesson"]
    outcomes = ctx["outcomes"]
    concepts = ctx["concepts"]
    language = str(project.get("primary_language") or project.get("primary_language_code") or "Arabic")
    previous = previous_blocks or []
    previous_summary = "\n".join(
        f"- {item.get('block_type')}: {str(item.get('content_text') or '')[:500]}" for item in previous[-3:]
    ) or "[No earlier approved blocks]"
    source_ids = list(lesson.get("source_ids") or [])
    outcome_lines = "\n".join(
        f"- {o.get('outcome_id')}: {o.get('verb')} {o.get('object_text')} | criterion: {o.get('success_criterion')}"
        for o in outcomes
    ) or "- No explicit outcome was supplied; flag this limitation."
    concept_lines = "\n".join(
        f"- {c.get('concept_id')}: {c.get('name')} | difficulty={c.get('difficulty')} | sources={','.join(c.get('source_ids') or [])}"
        for c in concepts
    ) or "- No concept metadata available."
    label = BLOCK_SPECS[block_type]["label_en"]
    return f"""# 3alimnIA lesson-block production request

Generate ONE lesson block only. Do not generate the whole lesson.

<project>
- Project: {project.get('project_name')}
- Domain: {project.get('domain')}
- Course: {project.get('program_name')}
- Learners: {project.get('target_learners')}
- Level: {project.get('learner_level')}
- Output language: {language}
- Teaching preferences: {project.get('teaching_preferences')}
- Assessment preferences: {project.get('assessment_preferences')}
</project>

<approved_blueprint>
- Blueprint run: {blueprint_bundle.get('id')}
- Lesson ID: {lesson.get('lesson_id')}
- Lesson title: {lesson.get('title')}
- Duration: {lesson.get('estimated_duration_minutes')} minutes
- Prerequisites: {', '.join(lesson.get('prerequisites') or [])}
- Misconceptions: {', '.join(lesson.get('misconceptions') or [])}
- Required source IDs: {', '.join(source_ids) or '[none]'}

Learning outcomes:
{outcome_lines}

Concepts:
{concept_lines}
</approved_blueprint>

<previous_approved_blocks>
{previous_summary}
</previous_approved_blocks>

# Requested block
- Type: {block_type}
- Label: {label}
- Sequence order: {BLOCK_SPECS[block_type]['order']}

# Mandatory rules
1. Produce only this block, in polished Markdown.
2. Respect the approved lesson, concepts, outcomes, duration, and prerequisites.
3. Use source markers only from this allowed set: {', '.join(source_ids) or '[no source markers available]'}.
4. Never invent a source ID, quotation, fact, tool, or external result.
5. Keep the activity cognitively appropriate for the learner level.
6. Preserve attempt-first pedagogy: prompts and hints precede complete solutions.
7. Include teacher-facing implementation notes only under a final heading named "Teacher implementation note".
8. Do not repeat content from earlier approved blocks.
9. If evidence is insufficient, state the gap explicitly rather than guessing.
10. Return the block itself; do not wrap it in JSON.
""".strip()


def validate_block_content(block_type: str, text: str, allowed_source_ids: List[str]) -> Dict[str, Any]:
    clean = str(text or "").strip()
    spec = BLOCK_SPECS.get(block_type, {})
    errors: List[str] = []
    warnings: List[str] = []
    words = len(re.findall(r"\S+", clean))
    if not clean:
        errors.append("empty_content")
    if words < int(spec.get("min_words") or 25):
        warnings.append("content_is_short")
    if clean.lower().startswith("generation failed") or "no content-generation provider" in clean.lower():
        errors.append("provider_failure_text")
    cited = sorted(set(re.findall(r"\[(S\d+)\]", clean)))
    allowed = set(str(x) for x in allowed_source_ids)
    invalid = [item for item in cited if item not in allowed]
    if invalid:
        errors.append("invalid_source_ids:" + ",".join(invalid))
    headings = len(re.findall(r"(?m)^#{1,4}\s+", clean))
    if headings == 0:
        warnings.append("missing_markdown_heading")
    status = "error" if errors else ("needs_review" if warnings else "completed")
    return {
        "status": status,
        "word_count": words,
        "cited_source_ids": cited,
        "errors": errors,
        "warnings": warnings,
        "completeness_score": 0.0 if errors else min(1.0, words / max(int(spec.get("min_words") or 25), 1)),
    }


def generate_and_persist(
    project: Dict[str, Any],
    teacher_username: str,
    blueprint_bundle: Dict[str, Any],
    lesson_id: str,
    block_type: str,
    *,
    context_blocks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    if not block_generation_status()["enabled"]:
        raise RuntimeError("Lesson block generation is disabled.")
    if not bool(int(blueprint_bundle.get("approved_by_teacher") or 0)):
        raise ValueError("Approve the blueprint before generating lesson blocks.")
    project_id = int(project["id"])
    previous = list(context_blocks) if context_blocks is not None else db.latest_approved_lesson_blocks(project_id, str(lesson_id))
    prompt = build_block_prompt(project, blueprint_bundle, lesson_id, block_type, previous_blocks=previous)
    ctx = lesson_context(blueprint_bundle, lesson_id)
    allowed_sources = list(ctx["lesson"].get("source_ids") or [])
    result = content_generation_engine.generate_content(
        prompt,
        str(project.get("primary_language") or project.get("primary_language_code") or "Arabic"),
        max_tokens=int(BLOCK_SPECS[block_type]["max_tokens"]),
        phase_number=3,
        research_grounded=True,
    )
    validation = validate_block_content(block_type, result.response, allowed_sources)
    status = result.status if result.status != "completed" else validation["status"]
    run_id = db.save_teacher_lesson_block(
        project_id=project_id,
        blueprint_run_id=int(blueprint_bundle["id"]),
        lesson_id=str(lesson_id),
        block_type=str(block_type),
        sequence_order=int(BLOCK_SPECS[block_type]["order"]),
        prompt_text=prompt,
        content_text=result.response,
        provider=result.provider,
        model=result.model,
        status=status,
        diagnostic=result.diagnostic,
        validation=validation,
        latency_ms=int(result.latency_ms or 0),
        is_fallback_used=bool(result.used_fallback),
        revision_type="generated",
        edited_by=str(teacher_username),
    )
    return db.teacher_lesson_block_bundle(run_id) or {}


def save_teacher_revision(
    *,
    project_id: int,
    base_run_id: int,
    teacher_username: str,
    content_text: str,
    change_summary: str,
) -> Dict[str, Any]:
    base = db.teacher_lesson_block_bundle(int(base_run_id))
    if not base or int(base.get("project_id") or 0) != int(project_id):
        raise ValueError("Lesson block version not found.")
    blueprint = db.teacher_blueprint_bundle(int(base["blueprint_run_id"])) or {}
    ctx = lesson_context(blueprint, str(base["lesson_id"]))
    validation = validate_block_content(str(base["block_type"]), content_text, list(ctx["lesson"].get("source_ids") or []))
    run_id = db.save_teacher_lesson_block(
        project_id=int(project_id),
        blueprint_run_id=int(base["blueprint_run_id"]),
        lesson_id=str(base["lesson_id"]),
        block_type=str(base["block_type"]),
        sequence_order=int(base.get("sequence_order") or 0),
        prompt_text=str(base.get("prompt_text") or ""),
        content_text=str(content_text),
        provider="teacher",
        model="manual-block-editor-v1",
        status=validation["status"],
        diagnostic="Teacher-authored immutable lesson-block revision.",
        validation=validation,
        parent_run_id=int(base_run_id),
        revision_type="manual_edit",
        change_summary=str(change_summary or "Teacher edited lesson block."),
        edited_by=str(teacher_username),
    )
    return db.teacher_lesson_block_bundle(run_id) or {}


def lesson_completion(project_id: int, lesson_id: str) -> Dict[str, Any]:
    rows = lesson_block_state(int(project_id), str(lesson_id), "en")
    approved = sum(1 for item in rows if bool(item.get("approved")))
    available = sum(1 for item in rows if bool(item.get("run")))
    return {
        "required": len(rows),
        "available": available,
        "approved": approved,
        "complete": bool(rows) and approved == len(rows),
        "next_block_type": next((str(item.get("block_type")) for item in rows if not item.get("approved")), None),
    }


def generate_full_lesson(
    project: Dict[str, Any],
    teacher_username: str,
    blueprint_bundle: Dict[str, Any],
    lesson_id: str,
    *,
    overwrite: bool = False,
    progress_callback: Optional[Any] = None,
) -> Dict[str, Any]:
    """Generate every missing section of one lesson in canonical order.

    The simple teacher journey uses one action to create a complete draft.
    Existing valid sections are preserved unless ``overwrite`` is requested.
    Generated sections are not approved automatically; the teacher reviews the
    assembled lesson and approves it with a separate explicit action.
    """
    if not block_generation_status()["enabled"]:
        raise RuntimeError("Lesson block generation is disabled.")
    if not bool(int(blueprint_bundle.get("approved_by_teacher") or 0)):
        raise ValueError("Approve the blueprint before generating lessons.")

    project_id = int(project["id"])
    ordered = ordered_block_types()
    context = db.latest_approved_lesson_blocks(project_id, str(lesson_id))
    results: List[Dict[str, Any]] = []
    generated = 0
    skipped = 0

    for index, block_type in enumerate(ordered, start=1):
        existing = db.latest_teacher_lesson_block(project_id, str(lesson_id), block_type, approved_only=False)
        existing_status = str((existing or {}).get("status") or "").lower()
        usable_existing = bool(existing and existing_status not in {"error", "failed"})
        if usable_existing and not overwrite:
            results.append(existing)
            context.append(existing)
            skipped += 1
            if progress_callback:
                progress_callback(index, len(ordered), block_type, "skipped")
            continue

        if progress_callback:
            progress_callback(index, len(ordered), block_type, "generating")
        created = generate_and_persist(
            project,
            teacher_username,
            blueprint_bundle,
            str(lesson_id),
            block_type,
            context_blocks=context,
        )
        results.append(created)
        context.append(created)
        generated += 1
        if progress_callback:
            progress_callback(index, len(ordered), block_type, "generated")

    state = lesson_block_state(project_id, str(lesson_id), "en")
    errors = [row for row in state if str(row.get("state") or "") == "failed"]
    return {
        "lesson_id": str(lesson_id),
        "generated": generated,
        "skipped": skipped,
        "results": results,
        "ready_for_review": len(results) == len(ordered) and not errors,
        "error_blocks": [row.get("block_type") for row in errors],
    }


def approve_full_lesson(project_id: int, lesson_id: str, teacher_username: str) -> Dict[str, Any]:
    """Approve the latest valid version of every required lesson section."""
    missing: List[str] = []
    invalid: List[str] = []
    latest_rows: List[Dict[str, Any]] = []
    for block_type in ordered_block_types():
        run = db.latest_teacher_lesson_block(int(project_id), str(lesson_id), block_type, approved_only=False)
        if not run:
            missing.append(block_type)
            continue
        if str(run.get("status") or "").lower() in {"error", "failed"}:
            invalid.append(block_type)
            continue
        latest_rows.append(run)
    if missing:
        raise ValueError("Generate all lesson sections before approval: " + ", ".join(missing))
    if invalid:
        raise ValueError("Resolve validation errors before approval: " + ", ".join(invalid))
    for run in latest_rows:
        db.approve_teacher_lesson_block(int(run["id"]), int(project_id), str(teacher_username))
    return lesson_completion(int(project_id), str(lesson_id))


def assembled_lesson(project_id: int, lesson_id: str, language_code: str = "ar") -> List[Dict[str, Any]]:
    """Return the latest lesson sections in pedagogical display order."""
    rows: List[Dict[str, Any]] = []
    for index, block_type in enumerate(ordered_block_types(), start=1):
        run = db.latest_teacher_lesson_block(int(project_id), str(lesson_id), block_type, approved_only=False)
        rows.append({
            "index": index,
            "block_type": block_type,
            "label": block_label(block_type, language_code),
            "run": run,
            "content_text": str((run or {}).get("content_text") or ""),
            "approved": bool(int((run or {}).get("approved_by_teacher") or 0)),
            "status": str((run or {}).get("status") or "not_started"),
        })
    return rows
