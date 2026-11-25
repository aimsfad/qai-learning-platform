"""Feature 5: Multi-Author Co-Creation & Peer Review Workflow Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


@dataclass(frozen=True)
class ReviewComment:
    comment_id: str
    block_id: str
    author: str
    body: str
    resolved: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class ApprovalRecord:
    reviewer: str
    role: str
    approved: bool
    note: str = ""
    signed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CoCreationEngine:
    """Manages inline peer review comments and multi-signature publish gates."""

    def __init__(self, required_signatures: int = 2) -> None:
        self.required_signatures = max(1, required_signatures)
        self.comments: List[ReviewComment] = []
        self.approvals: Dict[str, ApprovalRecord] = {}

    def add_comment(self, comment_id: str, block_id: str, author: str, body: str) -> ReviewComment:
        rec = ReviewComment(comment_id=comment_id, block_id=block_id, author=author, body=body)
        self.comments.append(rec)
        return rec

    def sign_off(self, reviewer: str, role: str, approved: bool, note: str = "") -> ApprovalRecord:
        rec = ApprovalRecord(reviewer=reviewer, role=role, approved=approved, note=note)
        self.approvals[reviewer] = rec
        return rec

    def can_publish(self) -> bool:
        unresolved = any(not c.resolved for c in self.comments)
        valid_sigs = sum(1 for a in self.approvals.values() if a.approved)
        return (not unresolved) and valid_sigs >= self.required_signatures
