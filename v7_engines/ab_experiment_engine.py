"""Feature 10: Built-in Pedagogical A/B Experimentation Suite."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ABResult:
    control_n: int
    treatment_n: int
    control_mean: float
    treatment_mean: float
    mean_diff: float
    cohens_d: float
    welch_t: float


class ABExperimentEngine:
    """Deterministic cohort assignment and publication-ready A/B statistics."""

    def assign_cohort(self, experiment_id: str, learner_id: str) -> str:
        digest = hashlib.sha256(f"{experiment_id}:{learner_id}".encode("utf-8")).digest()
        return "treatment" if digest[0] % 2 == 1 else "control"

    def evaluate(self, control_scores: Sequence[float], treatment_scores: Sequence[float]) -> ABResult:
        n1, n2 = len(control_scores), len(treatment_scores)
        if n1 < 2 or n2 < 2:
            raise ValueError("Each cohort requires at least 2 observations.")
        m1 = sum(control_scores) / n1
        m2 = sum(treatment_scores) / n2
        v1 = sum((x - m1) ** 2 for x in control_scores) / (n1 - 1)
        v2 = sum((x - m2) ** 2 for x in treatment_scores) / (n2 - 1)
        pooled_sd = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / max(1, (n1 + n2 - 2)))
        d = (m2 - m1) / pooled_sd if pooled_sd > 0 else 0.0
        se = math.sqrt((v1 / n1) + (v2 / n2))
        t_stat = (m2 - m1) / se if se > 0 else 0.0
        return ABResult(
            control_n=n1,
            treatment_n=n2,
            control_mean=round(m1, 3),
            treatment_mean=round(m2, 3),
            mean_diff=round(m2 - m1, 3),
            cohens_d=round(d, 3),
            welch_t=round(t_stat, 3),
        )

    def to_latex_row(self, label: str, res: ABResult) -> str:
        return f"{label} & {res.control_mean:.2f} (n={res.control_n}) & {res.treatment_mean:.2f} (n={res.treatment_n}) & {res.cohens_d:.2f} & {res.welch_t:.2f} \\\\"
