"""Feature 1: Dynamic Knowledge Graph & Mastery Map for 3alimnIA V7.0."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Set


@dataclass(frozen=True)
class ConceptNode:
    concept_id: str
    title: str
    prerequisites: tuple[str, ...] = ()
    mastery_threshold: float = 0.75


class KnowledgeGraphEngine:
    """Builds a concept prerequisite DAG, computes learner readiness, and renders SVG."""

    def __init__(self, nodes: Sequence[ConceptNode]) -> None:
        self._nodes: Dict[str, ConceptNode] = {n.concept_id: n for n in nodes}

    def topological_order(self) -> List[str]:
        visited: Set[str] = set()
        visiting: Set[str] = set()
        order: List[str] = []

        def dfs(cid: str) -> None:
            if cid in visited:
                return
            if cid in visiting:
                raise ValueError(f"Cycle detected in concept graph at {cid!r}")
            visiting.add(cid)
            node = self._nodes[cid]
            for prereq in node.prerequisites:
                if prereq in self._nodes:
                    dfs(prereq)
            visiting.remove(cid)
            visited.add(cid)
            order.append(cid)

        for cid in self._nodes:
            dfs(cid)
        return order

    def recommend_next(self, mastery_scores: Dict[str, float]) -> List[Dict[str, object]]:
        """Return unlocked concepts not yet mastered, ordered by prerequisite progression."""
        recs: List[Dict[str, object]] = []
        for cid in self.topological_order():
            node = self._nodes[cid]
            score = float(mastery_scores.get(cid, 0.0))
            if score >= node.mastery_threshold:
                continue
            prereqs_met = all(
                float(mastery_scores.get(p, 0.0)) >= self._nodes[p].mastery_threshold
                for p in node.prerequisites
                if p in self._nodes
            )
            if prereqs_met:
                recs.append({
                    "concept_id": cid,
                    "title": node.title,
                    "current_mastery": round(score, 3),
                    "target_mastery": node.mastery_threshold,
                    "status": "in_progress" if score > 0 else "ready",
                })
        return recs

    def render_svg(self, mastery_scores: Dict[str, float]) -> str:
        """Render a clean inline SVG mastery map."""
        order = self.topological_order()
        width = max(520, len(order) * 180 + 40)
        parts = [f'<svg viewBox="0 0 {width} 140" xmlns="http://www.w3.org/2000/svg" role="img">']
        for idx, cid in enumerate(order):
            x = 20 + idx * 180
            node = self._nodes[cid]
            score = float(mastery_scores.get(cid, 0.0))
            fill = "#059669" if score >= node.mastery_threshold else ("#2563EB" if score > 0 else "#64748B")
            if idx > 0:
                parts.append(f'<line x1="{x - 36}" y1="70" x2="{x}" y2="70" stroke="#94A3B8" stroke-width="2"/>')
            parts.append(f'<rect x="{x}" y="34" width="144" height="72" rx="16" fill="{fill}"/>')
            parts.append(f'<text x="{x + 72}" y="66" fill="#FFFFFF" font-size="13" font-weight="700" text-anchor="middle">{node.title[:18]}</text>')
            parts.append(f'<text x="{x + 72}" y="88" fill="#E2E8F0" font-size="12" text-anchor="middle">{int(score * 100)}%</text>')
        parts.append("</svg>")
        return "".join(parts)
