"""Feature 8: Live Sentence-Level Citation & Hallucination Auditor."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Sequence

_TOKEN_RE = re.compile(r"[\w\u0600-\u06FF]+")


@dataclass(frozen=True)
class SentenceAudit:
    sentence: str
    grounding_score: float
    best_source_id: str
    grounded: bool


class CitationAuditorEngine:
    """Scores every generated sentence against teacher-approved RAG chunks."""

    def _tokens(self, text: str) -> set[str]:
        return {t.lower() for t in _TOKEN_RE.findall(text or "") if len(t) > 2}

    def audit_text(
        self,
        generated_text: str,
        approved_chunks: Sequence[Dict[str, str]],
        *,
        threshold: float = 0.25,
    ) -> Dict[str, object]:
        sentences = [s.strip() for s in re.split(r"[.!؟?\n]+", generated_text or "") if s.strip()]
        chunk_tokens = [(c.get("source_id", "unknown"), self._tokens(c.get("body", ""))) for c in approved_chunks]
        results: List[SentenceAudit] = []
        for sent in sentences:
            s_toks = self._tokens(sent)
            best_score = 0.0
            best_src = ""
            if s_toks:
                for sid, c_toks in chunk_tokens:
                    overlap = len(s_toks & c_toks) / len(s_toks)
                    if overlap > best_score:
                        best_score = overlap
                        best_src = sid
            results.append(SentenceAudit(
                sentence=sent,
                grounding_score=round(best_score, 3),
                best_source_id=best_src,
                grounded=best_score >= threshold,
            ))
        ratio = round(sum(1 for r in results if r.grounded) / max(1, len(results)), 3)
        return {"overall_grounding_ratio": ratio, "sentences": results}
