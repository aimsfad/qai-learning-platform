"""Feature 4: Multilingual Voice AI Coach Engine (AR / FR / EN)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class VoiceTurn:
    locale: str
    bcp47: str
    spoken_prompt: str
    expected_keywords: tuple[str, ...]
    max_seconds: int = 90


class VoiceCoachEngine:
    """Builds localized oral micro-coaching turns and evaluates learner transcripts."""

    _LOCALE_MAP: Dict[str, str] = {"ar": "ar-SA", "fr": "fr-FR", "en": "en-US"}

    def build_oral_check(self, concept_title: str, keywords: tuple[str, ...], locale: str = "ar") -> VoiceTurn:
        lang = locale[:2].lower() if locale else "ar"
        bcp47 = self._LOCALE_MAP.get(lang, "ar-SA")
        prompts = {
            "ar": f"اشرح بصوتك خلال دقيقة واحدة فكرة «{concept_title}» مع مثال عملي واحد.",
            "fr": f"Expliquez à voix haute en une minute le concept « {concept_title} » avec un exemple concret.",
            "en": f"Explain '{concept_title}' aloud in one minute using one concrete example.",
        }
        return VoiceTurn(
            locale=lang,
            bcp47=bcp47,
            spoken_prompt=prompts.get(lang, prompts["en"]),
            expected_keywords=keywords,
        )

    def score_transcript(self, transcript: str, turn: VoiceTurn) -> Dict[str, object]:
        lowered = str(transcript or "").lower()
        matched = [kw for kw in turn.expected_keywords if kw.lower() in lowered]
        total = max(1, len(turn.expected_keywords))
        coverage = round(len(matched) / total, 3)
        return {
            "coverage": coverage,
            "matched_keywords": matched,
            "missing_keywords": [kw for kw in turn.expected_keywords if kw not in matched],
            "passed": coverage >= 0.6,
        }
