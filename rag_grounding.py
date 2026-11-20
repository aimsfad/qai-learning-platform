"""Conservative citation traceability audit for RAG-generated educational text.

This does NOT assert factual truth or semantic entailment. A citation pointing
at an indexed source is only traceability, and teacher review is required.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

CITATION_PATTERN = re.compile(r"\[(RAG[A-F0-9]{12}(?:_P\d+_C\d+)?)\]")


def audit_generated_text(text: str, context: Any) -> Dict[str, Any]:
    allowed_chunks = set(getattr(context, "citation_ids", []) or [])
    allowed_docs = set(getattr(context, "source_ids", []) or [])
    cited = set(CITATION_PATTERN.findall(str(text or "")))
    unknown = sorted(cited - allowed_chunks - allowed_docs)
    document_level = sorted(cited & allowed_docs)
    detailed = sorted(cited & allowed_chunks)
    # Estimate potential uncited assertions. The algorithm is intentionally
    # conservative and cannot reliably identify scientific claims in every language.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", str(text or "")) if p.strip()]
    likely_uncited: List[str] = []
    for p in paragraphs:
        p = re.sub(r"(?m)^#{1,6}\s+", "", p).strip()
        if len(p) < 85 or p.startswith("```") or p.startswith("|"):
            continue
        if not CITATION_PATTERN.search(p):
            likely_uncited.append(p[:160])
    has_evidence = bool(getattr(context, "hits", []) or [])
    return {
        "audit_kind": "reference_traceability_only_not_entailment",
        "known_chunk_citations": detailed,
        "document_level_citations": document_level,
        "unknown_citations": unknown,
        "possible_uncited_passages": likely_uncited[:12],
        "human_verification_required": has_evidence,
        "retrieval_mode": str(getattr(context, "retrieval_mode", "off")),
        "review_reasons": (
            (["unknown_citations"] if unknown else [])
            + (["non_specific_document_citations"] if document_level else [])
            + (["possible_uncited_passages"] if likely_uncited else [])
            + (["citations_missing"] if has_evidence and not cited else [])
            + (["semantic_support_unverified"] if has_evidence else [])
        ),
    }


def summary(audit: Dict[str, Any]) -> str:
    if not audit.get("human_verification_required"):
        return "No RAG excerpts; grounding audit not applicable."
    return (
        "RAG grounding requires teacher verification (citation linkage is not entailment): "
        f"{len(audit['known_chunk_citations'])} chunk references, "
        f"{len(audit['unknown_citations'])} unknown, "
        f"{len(audit['possible_uncited_passages'])} potentially uncited passages."
    )
