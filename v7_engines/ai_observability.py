"""Provider Latency, Token Budget & Fallback Observability for model_router.py."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ProviderTelemetry:
    provider: str
    model: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    succeeded: bool
    fallback_used: bool = False


class AIObservabilityTracker:
    def __init__(self) -> None:
        self._events: List[ProviderTelemetry] = []

    def record(self, event: ProviderTelemetry) -> None:
        self._events.append(event)

    def summary(self) -> Dict[str, object]:
        total = len(self._events)
        if total == 0:
            return {"calls": 0, "success_rate": 1.0, "avg_latency_ms": 0.0, "total_tokens": 0}
        ok = sum(1 for e in self._events if e.succeeded)
        avg_lat = sum(e.latency_ms for e in self._events) / total
        toks = sum(e.prompt_tokens + e.completion_tokens for e in self._events)
        return {
            "calls": total,
            "success_rate": round(ok / total, 3),
            "avg_latency_ms": round(avg_lat, 1),
            "total_tokens": toks,
            "fallbacks": sum(1 for e in self._events if e.fallback_used),
        }
