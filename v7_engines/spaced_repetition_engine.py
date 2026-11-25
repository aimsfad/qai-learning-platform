"""Feature 3: Adaptive Spaced Repetition & Micro-Recall Engine (SM-2)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List


@dataclass
class ReviewCard:
    card_id: str
    concept_id: str
    prompt: str
    answer_key: str
    repetitions: int = 0
    interval_days: int = 1
    ease_factor: float = 2.5
    due_at: str = ""


class SpacedRepetitionEngine:
    """SM-2 spaced repetition scheduler driven by learner misconception evidence."""

    def review(self, card: ReviewCard, quality: int, *, now: datetime | None = None) -> ReviewCard:
        if not 0 <= quality <= 5:
            raise ValueError("SM-2 quality score must be between 0 and 5.")
        ts = now or datetime.now(timezone.utc)
        ef = max(1.3, card.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
        if quality < 3:
            reps = 0
            interval = 1
        else:
            reps = card.repetitions + 1
            if reps == 1:
                interval = 1
            elif reps == 2:
                interval = 6
            else:
                interval = max(1, round(card.interval_days * ef))
        due = (ts + timedelta(days=interval)).isoformat()
        return ReviewCard(
            card_id=card.card_id,
            concept_id=card.concept_id,
            prompt=card.prompt,
            answer_key=card.answer_key,
            repetitions=reps,
            interval_days=interval,
            ease_factor=round(ef, 3),
            due_at=due,
        )

    def due_cards(self, cards: List[ReviewCard], *, now: datetime | None = None) -> List[ReviewCard]:
        ref = (now or datetime.now(timezone.utc)).isoformat()
        return [c for c in cards if not c.due_at or c.due_at <= ref]
