"""Pure validation/parsing contract for generated 3alimnIA course pre-tests.

This module deliberately depends only on the Python standard library so release
validators can exercise the assessment contract even outside the full
Streamlit runtime environment.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

SCHEMA_VERSION = "3alimnia.course_pretest.v1"
REQUIRED_QUESTION_COUNT = 6
REQUIRED_OPTIONS_COUNT = 4

QUESTION_TYPES = {
    "prerequisite",
    "core_concept",
    "misconception",
    "application",
    "interpretation",
    "transfer",
}

INVALID_PLACEHOLDERS = {
    "untitled",
    "title",
    "tbd",
    "to be defined",
    "none",
    "null",
    "n a",
    "course concept",
    "course concept 1",
    "course concept 2",
    "course concept 3",
    "sans titre",
    "بدون عنوان",
    "غير معنون",
    "غير معنونة",
}

SELF_REPORT_PATTERNS = (
    r"ما\s+مستوى\s+معرفتك",
    r"مدى\s+معرفتك",
    r"how\s+familiar\s+are\s+you",
    r"how\s+well\s+do\s+you\s+know",
    r"quel\s+est\s+votre\s+niveau",
    r"à\s+quel\s+point\s+connaissez",
)


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def semantic_key(value: Any) -> str:
    clean = clean_text(value).casefold()
    clean = re.sub(r"[^\w\u0600-\u06FF]+", " ", clean, flags=re.UNICODE)
    stop = {
        "تعلم", "تعليم", "أساسيات", "اساسيات", "لغة", "مقرر", "المقرر", "دورة", "الدورة",
        "learn", "learning", "teach", "teaching", "basic", "basics", "language", "course", "intro", "introduction",
        "apprendre", "apprentissage", "bases", "base", "langage", "langue", "cours", "introduction",
    }
    return " ".join(token for token in clean.split() if token not in stop)


def is_placeholder(value: Any) -> bool:
    clean = clean_text(value)
    if not clean:
        return True
    if clean.lstrip().startswith("$"):
        return True
    key = re.sub(r"[^\w\u0600-\u06FF]+", " ", clean.casefold(), flags=re.UNICODE).strip()
    return " ".join(key.split()) in INVALID_PLACEHOLDERS


def is_self_report_question(value: Any) -> bool:
    clean = clean_text(value).casefold()
    return any(re.search(pattern, clean, flags=re.I) for pattern in SELF_REPORT_PATTERNS)


def _balanced_json_candidates(text: str) -> Iterable[str]:
    """Yield plausible JSON objects/arrays without assuming fenced output."""
    raw = str(text or "")
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", raw, flags=re.I | re.S)
    for item in fenced:
        yield item

    decoder = json.JSONDecoder()
    for match in re.finditer(r"[\[{]", raw):
        try:
            _, end = decoder.raw_decode(raw[match.start():])
        except Exception:
            continue
        yield raw[match.start(): match.start() + end]


def extract_payload(text: str) -> List[Dict[str, Any]]:
    """Extract a course_pretest list from provider output."""
    seen = set()
    for candidate in _balanced_json_candidates(text):
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            payload = json.loads(candidate)
        except Exception:
            continue
        if isinstance(payload, Mapping):
            values = payload.get("course_pretest") or payload.get("diagnostic_questions") or payload.get("questions")
        else:
            values = payload
        if isinstance(values, list):
            return [dict(row) for row in values if isinstance(row, Mapping)]
    return []


def _correct_index(row: Mapping[str, Any], options: Sequence[str]) -> Any:
    value = row.get("correct_index")
    if value is not None:
        try:
            return int(value)
        except Exception:
            return None
    answer = clean_text(row.get("correct_answer"))
    if not answer:
        return None
    letter = answer[:1].upper()
    if letter in "ABCD":
        return ord(letter) - ord("A")
    for idx, option in enumerate(options):
        if clean_text(option).casefold() == answer.casefold():
            return idx
    return None


def validate_generated_pretest(
    rows: Sequence[Mapping[str, Any]],
    *,
    blocked_titles: Sequence[str] | None = None,
    expected_count: int = REQUIRED_QUESTION_COUNT,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Normalize and quality-gate one generated pre-test package.

    The result is suitable for immutable per-course-version persistence.
    Invalid questions are excluded and reasons are returned in ``quality``.
    """
    blocked_keys = {semantic_key(item) for item in (blocked_titles or []) if semantic_key(item)}
    normalized: List[Dict[str, Any]] = []
    errors: List[str] = []
    seen_questions = set()
    seen_concepts = set()
    type_counts: Dict[str, int] = {}

    for index, raw in enumerate(rows, start=1):
        row = dict(raw or {})
        question = clean_text(row.get("question") or row.get("prompt"))
        concept = clean_text(row.get("concept") or row.get("learning_objective") or row.get("objective"))
        qtype = clean_text(row.get("question_type") or row.get("type") or "core_concept").casefold().replace(" ", "_")
        difficulty = clean_text(row.get("difficulty") or "medium").casefold()
        cognitive = clean_text(row.get("cognitive_level") or row.get("bloom_level") or "understand").casefold()
        explanation = clean_text(row.get("explanation") or row.get("rationale"))
        options = [clean_text(item) for item in (row.get("options") or []) if clean_text(item)]
        correct_index = _correct_index(row, options)

        tag = f"Q{index}"
        if is_placeholder(question) or len(question) < 8:
            errors.append(f"{tag}: invalid_or_placeholder_question")
            continue
        if is_self_report_question(question):
            errors.append(f"{tag}: self_report_not_objective")
            continue
        if is_placeholder(concept) or len(concept) < 2:
            errors.append(f"{tag}: invalid_concept")
            continue
        concept_key = semantic_key(concept) or concept.casefold()
        if concept_key in blocked_keys:
            errors.append(f"{tag}: concept_is_course_title")
            continue
        question_key = semantic_key(question) or question.casefold()
        if question_key in seen_questions:
            errors.append(f"{tag}: duplicate_question")
            continue
        if len(options) != REQUIRED_OPTIONS_COUNT:
            errors.append(f"{tag}: requires_{REQUIRED_OPTIONS_COUNT}_options")
            continue
        option_keys = [clean_text(item).casefold() for item in options]
        if len(set(option_keys)) != len(option_keys):
            errors.append(f"{tag}: duplicate_options")
            continue
        if correct_index is None or not 0 <= int(correct_index) < len(options):
            errors.append(f"{tag}: invalid_correct_index")
            continue
        if not explanation:
            errors.append(f"{tag}: missing_explanation")
            continue
        if qtype not in QUESTION_TYPES:
            qtype = "core_concept"
        if difficulty not in {"easy", "medium", "hard"}:
            difficulty = "medium"

        seen_questions.add(question_key)
        seen_concepts.add(concept_key)
        type_counts[qtype] = type_counts.get(qtype, 0) + 1
        normalized.append(
            {
                "id": f"Q{len(normalized)+1}",
                "question_type": qtype,
                "concept": concept,
                "question": question,
                "options": options,
                "correct_index": int(correct_index),
                "explanation": explanation,
                "difficulty": difficulty,
                "cognitive_level": cognitive or "understand",
            }
        )

    if len(normalized) != int(expected_count):
        errors.append(f"question_count={len(normalized)} expected={int(expected_count)}")
    if len(seen_concepts) < 4:
        errors.append(f"concept_diversity={len(seen_concepts)} expected>=4")
    if not any(item.get("question_type") == "prerequisite" for item in normalized):
        errors.append("missing_prerequisite_question")
    if not any(item.get("question_type") == "misconception" for item in normalized):
        errors.append("missing_misconception_question")
    if not any(item.get("question_type") in {"application", "interpretation", "transfer"} for item in normalized):
        errors.append("missing_application_or_transfer_question")

    ready = not errors and len(normalized) == int(expected_count)
    score = 1.0
    if errors:
        score = max(0.0, 1.0 - min(1.0, len(errors) / 10.0))
    quality = {
        "schema_version": SCHEMA_VERSION,
        "ready": bool(ready),
        "question_count": len(normalized),
        "concept_count": len(seen_concepts),
        "question_type_counts": type_counts,
        "quality_score": round(score, 3),
        "errors": errors,
    }
    return normalized[: int(expected_count)], quality
