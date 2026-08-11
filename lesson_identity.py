"""Lesson identity and content-hygiene helpers for 3alimnIA.

This module keeps bibliographic/source metadata separate from teachable concepts.
It is intentionally dependency-light so it can be reused by evidence synthesis,
blueprint compilation, and teacher-facing rendering without importing Streamlit.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

_PLACEHOLDERS = {"", "none", "null", "undefined", "untitled", "n/a", "na", "-", "—"}

# Strong indicators that a title names a document/resource rather than a
# teachable concept. Keep this list conservative: it is used for blocking only
# when combined with a source-registry match or other strong evidence.
_DOCUMENT_HINT_RE = re.compile(
    r"(?:\b(?:catalogue|catalog|handbook|prospectus|regulations?|policy|policies|"
    r"curriculum\s+guide|programme\s+specification|program\s+specification|"
    r"degree\s+requirements|course\s+catalog|admissions?\s+guide|annual\s+report|"
    r"study\s+guide|student\s+guide)\b|"
    r"(?:اللائحة|لائحة\s+داخلية|دليل\s+(?:الطالب|الدراسات|البرنامج)|"
    r"متطلبات\s+التخرج|شروط\s+(?:التسجيل|القبول)|وثيقة\s+رسمية|قرار\s+وزاري|"
    r"البرنامج\s+الرسمي))",
    re.IGNORECASE,
)
_URL_OR_FILE_RE = re.compile(
    r"(?:https?://|www\.|doi\s*:\s*|\.(?:pdf|docx?|pptx?|xlsx?|html?)\b)",
    re.IGNORECASE,
)
_SOURCE_MARKER_RE = re.compile(r"\[(?:S|R)\d+\]", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_LESSON_PREFIX_RE = re.compile(
    r"^\s*(?:(?:ال?درس)|(?:lesson)|(?:le[çc]on))\s*\d+\s*[:：\-–—]?\s*",
    re.IGNORECASE,
)


def compact_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" \t\r\n-–—,:؛|.")


def normalized_identity(value: Any) -> str:
    text = compact_text(value).lower()
    text = re.sub(r"[^\w\u0600-\u06ff]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def is_placeholder(value: Any) -> bool:
    return compact_text(value).lower() in _PLACEHOLDERS


def source_titles_from_bundle(evidence_bundle: Optional[Mapping[str, Any]]) -> List[str]:
    bundle = dict(evidence_bundle or {})
    titles: List[str] = []
    for row in bundle.get("sources") or []:
        title = compact_text((row or {}).get("title"))
        if title and title.lower() not in _PLACEHOLDERS:
            titles.append(title)
    return titles


def is_reference_document_title(value: Any) -> bool:
    """Return True for strong document/bibliographic title signals."""
    text = compact_text(value)
    if not text:
        return False
    if _URL_OR_FILE_RE.search(text) or _SOURCE_MARKER_RE.search(text):
        return True
    if _DOCUMENT_HINT_RE.search(text):
        return True
    # A long title containing a publication-like year is suspicious, but a
    # year alone is not enough to reject a concept.
    return bool(len(text) >= 55 and _YEAR_RE.search(text))


def _token_set(value: Any) -> set[str]:
    return {token for token in normalized_identity(value).split() if len(token) > 1}


def registered_source_matches(value: Any, source_titles: Sequence[str]) -> List[str]:
    """Return source titles that substantially match or are embedded in value."""
    candidate = normalized_identity(_LESSON_PREFIX_RE.sub("", compact_text(value)))
    if not candidate:
        return []
    candidate_tokens = _token_set(candidate)
    matches: List[str] = []
    for source_title in source_titles:
        source = normalized_identity(source_title)
        if not source:
            continue
        if candidate == source:
            matches.append(source_title)
            continue
        if len(source) >= 12 and source in candidate:
            matches.append(source_title)
            continue
        source_tokens = _token_set(source)
        if len(source_tokens) >= 3 and candidate_tokens:
            overlap = len(candidate_tokens & source_tokens) / max(1, len(source_tokens))
            if overlap >= 0.86 and len(candidate_tokens) <= len(source_tokens) + 6:
                matches.append(source_title)
    return matches


def looks_like_source_title(value: Any, source_titles: Sequence[str] = ()) -> bool:
    text = compact_text(value)
    if not text or is_placeholder(text):
        return False
    if registered_source_matches(text, source_titles):
        return True
    return is_reference_document_title(text)


def blocking_source_identity(value: Any, source_titles: Sequence[str]) -> bool:
    """Conservative blocking rule for lesson/concept identity.

    Registry overlap alone can be legitimate (a source may be named after the
    concept), so blocking requires a document-like matched source or multiple
    source-title matches in the same generated identity.
    """
    matches = registered_source_matches(value, source_titles)
    if len(matches) >= 2:
        return True
    return any(is_reference_document_title(item) for item in matches)


def linked_concept_rows(lesson: Mapping[str, Any], blueprint: Mapping[str, Any]) -> List[Dict[str, Any]]:
    by_id = {
        str(item.get("concept_id")): dict(item)
        for item in (blueprint.get("concepts") or [])
        if item.get("concept_id")
    }
    return [
        by_id[str(cid)]
        for cid in (lesson.get("concept_ids") or [])
        if str(cid) in by_id
    ]


def safe_concept_names(
    lesson: Mapping[str, Any],
    blueprint: Mapping[str, Any],
    source_titles: Sequence[str] = (),
) -> List[str]:
    names: List[str] = []
    seen = set()
    for row in linked_concept_rows(lesson, blueprint):
        name = compact_text(row.get("name") or row.get("title"))
        key = normalized_identity(name)
        if not key or is_placeholder(name) or looks_like_source_title(name, source_titles):
            continue
        if key not in seen:
            seen.add(key)
            names.append(name)
    return names


def _localized_prefix(index: int, lang: str) -> str:
    language = str(lang or "en").lower()
    if language.startswith("ar"):
        return f"درس {index}:"
    if language.startswith("fr"):
        return f"Leçon {index} :"
    return f"Lesson {index}:"


def _join_names(names: Sequence[str], lang: str) -> str:
    language = str(lang or "en").lower()
    joiner = " و " if language.startswith("ar") else (" et " if language.startswith("fr") else " and ")
    return joiner.join([compact_text(item) for item in names if compact_text(item)])


def teacher_facing_lesson_title(
    value: Any,
    *,
    index: int,
    lang: str,
    lesson: Optional[Mapping[str, Any]] = None,
    blueprint: Optional[Mapping[str, Any]] = None,
    project: Optional[Mapping[str, Any]] = None,
    source_titles: Sequence[str] = (),
) -> str:
    """Return a safe display identity without mutating persisted history."""
    raw = compact_text(value)
    raw = re.sub(
        r"(?i)(?:\s+(?:و|and|et)\s+)?\b(?:untitled|undefined|null|none|n/?a)\b",
        "",
        raw,
    )
    raw = compact_text(raw)

    # Keep a teacher-edited/good title verbatim when it is not polluted by
    # source-document identity.
    if raw and not is_placeholder(raw) and not looks_like_source_title(raw, source_titles):
        return raw

    lesson_row = dict(lesson or {})
    blueprint_data = dict(blueprint or {})
    names = safe_concept_names(lesson_row, blueprint_data, source_titles)
    if names:
        return f"{_localized_prefix(index, lang)} {_join_names(names[:2], lang)}"

    project_data = dict(project or {})
    fallback_candidates = [
        project_data.get("target_concept"),
        project_data.get("unit_title"),
        project_data.get("domain"),
    ]
    units = {
        str(item.get("unit_id")): dict(item)
        for item in (blueprint_data.get("units") or [])
        if item.get("unit_id")
    }
    unit = units.get(str(lesson_row.get("unit_id") or ""), {})
    fallback_candidates.extend([unit.get("description"), unit.get("title")])

    for candidate in fallback_candidates:
        clean = compact_text(candidate)
        clean = _LESSON_PREFIX_RE.sub("", clean)
        if clean and not is_placeholder(clean) and not looks_like_source_title(clean, source_titles):
            return f"{_localized_prefix(index, lang)} {clean}"

    # Last resort: never surface a source title; use a neutral lesson identity.
    language = str(lang or "en").lower()
    if language.startswith("ar"):
        return f"الدرس {index}"
    if language.startswith("fr"):
        return f"Leçon {index}"
    return f"Lesson {index}"


def inspect_lesson_identity(
    *,
    lesson: Mapping[str, Any],
    blueprint: Mapping[str, Any],
    project: Optional[Mapping[str, Any]] = None,
    source_titles: Sequence[str] = (),
    index: int = 1,
    lang: str = "ar",
) -> Dict[str, Any]:
    raw_title = compact_text(lesson.get("title"))
    concept_rows = linked_concept_rows(lesson, blueprint)
    concept_names = [compact_text(row.get("name") or row.get("title")) for row in concept_rows]
    source_like_concepts = [name for name in concept_names if looks_like_source_title(name, source_titles)]
    blocking_concepts = [name for name in concept_names if blocking_source_identity(name, source_titles)]
    title_matches = registered_source_matches(raw_title, source_titles)
    title_blocking = blocking_source_identity(raw_title, source_titles)

    reasons: List[str] = []
    if title_blocking:
        reasons.append("lesson_title_matches_reference_source")
    if concept_names and len(blocking_concepts) == len(concept_names):
        reasons.append("all_lesson_concepts_are_reference_sources")

    warnings: List[str] = []
    if source_like_concepts and not reasons:
        warnings.append("lesson_contains_source_like_concept_names")
    if title_matches and not title_blocking:
        warnings.append("lesson_title_overlaps_source_registry")

    return {
        "valid": not reasons,
        "reasons": reasons,
        "warnings": warnings,
        "source_like_concepts": source_like_concepts,
        "source_title_matches": title_matches,
        "display_title": teacher_facing_lesson_title(
            raw_title,
            index=index,
            lang=lang,
            lesson=lesson,
            blueprint=blueprint,
            project=project,
            source_titles=source_titles,
        ),
    }


def safe_project_concept_candidates(project: Mapping[str, Any], source_titles: Sequence[str] = ()) -> List[str]:
    """Deterministic fallback concepts that never come from source titles."""
    candidates: List[str] = [
        compact_text(project.get("target_concept")),
        compact_text(project.get("unit_title")),
        compact_text(project.get("domain")),
    ]
    prereq = str(project.get("prerequisites") or "")
    candidates.extend(compact_text(item) for item in re.split(r"[,;،;\n]+", prereq))
    result: List[str] = []
    seen = set()
    for candidate in candidates:
        key = normalized_identity(candidate)
        if not key or is_placeholder(candidate) or looks_like_source_title(candidate, source_titles):
            continue
        if key in seen:
            continue
        seen.add(key)
        result.append(candidate)
    return result
