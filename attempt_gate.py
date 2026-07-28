"""Attempt-first validation for the 3alimnIA learner workspace.

The module is intentionally independent from Streamlit so the validation rules can
be unit-tested and reused by other learning activities.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import FrozenSet

MIN_ATTEMPT_CHARS = 40
MIN_ATTEMPT_WORDS = 6
MIN_UNIQUE_WORDS = 4


@dataclass(frozen=True)
class AttemptValidation:
    is_valid: bool
    reason: str
    normalized_text: str
    char_count: int
    word_count: int
    unique_word_count: int
    readiness: float


def normalize_attempt(value: str) -> str:
    """Collapse whitespace while preserving the learner's wording."""
    return " ".join((value or "").strip().split())


def _comparison_text(value: str) -> str:
    text = normalize_attempt(value).lower()
    text = text.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي"}))
    text = re.sub(r"[^\wÀ-ÿ\u0600-\u06FF]+", " ", text)
    return " ".join(text.split())


def _tokens(value: str) -> list[str]:
    return re.findall(r"[\wÀ-ÿ\u0600-\u06FF]+", value.lower(), flags=re.UNICODE)


_LOW_EFFORT_RAW = {
    "ar": {"لا اعرف", "لا أعرف", "ما نعرف", "ليس لدي فكرة", "لا أدري", "لا ادري"},
    "fr": {"je ne sais pas", "aucune idée", "je sais pas"},
    "en": {"i don't know", "i do not know", "no idea", "idk"},
}
LOW_EFFORT_PATTERNS: dict[str, FrozenSet[str]] = {
    lang: frozenset(_comparison_text(item) for item in items)
    for lang, items in _LOW_EFFORT_RAW.items()
}


def validate_attempt_text(value: str, language: str = "ar") -> AttemptValidation:
    normalized = normalize_attempt(value)
    words = _tokens(normalized)
    unique_words = set(words)
    char_count = len(normalized)
    word_count = len(words)
    unique_count = len(unique_words)

    char_ratio = min(char_count / MIN_ATTEMPT_CHARS, 1.0)
    word_ratio = min(word_count / MIN_ATTEMPT_WORDS, 1.0)
    unique_ratio = min(unique_count / MIN_UNIQUE_WORDS, 1.0)
    readiness = min(char_ratio, word_ratio, unique_ratio)

    if not normalized:
        return AttemptValidation(False, "empty", normalized, 0, 0, 0, 0.0)

    comparable = _comparison_text(normalized)
    if comparable in LOW_EFFORT_PATTERNS.get(language, frozenset()):
        return AttemptValidation(False, "low_effort", normalized, char_count, word_count, unique_count, readiness)

    if char_count < MIN_ATTEMPT_CHARS:
        return AttemptValidation(False, "min_chars", normalized, char_count, word_count, unique_count, readiness)

    if word_count < MIN_ATTEMPT_WORDS:
        return AttemptValidation(False, "min_words", normalized, char_count, word_count, unique_count, readiness)

    if unique_count < MIN_UNIQUE_WORDS:
        return AttemptValidation(False, "low_diversity", normalized, char_count, word_count, unique_count, readiness)

    return AttemptValidation(True, "valid", normalized, char_count, word_count, unique_count, 1.0)


def build_attempt_key(student_id: int, lesson_id: str) -> str:
    safe_lesson = re.sub(r"[^A-Za-z0-9_-]", "_", str(lesson_id))
    return f"v682_attempt_student_{int(student_id)}_lesson_{safe_lesson}"
