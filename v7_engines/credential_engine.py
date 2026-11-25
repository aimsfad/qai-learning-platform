"""Feature 6: Evidence-Backed Verifiable Credentials (HMAC-SHA256)."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class EvidenceCredential:
    credential_id: str
    learner_name: str
    course_title: str
    pretest_score: float
    posttest_score: float
    verified_attempts: int
    issued_at: str
    signature: str


class CredentialEngine:
    """Issues and verifies tamper-evident learning credentials backed by real evidence."""

    def __init__(self, signing_secret: str) -> None:
        if len(signing_secret) < 16:
            raise ValueError("Signing secret must be at least 16 characters.")
        self._secret = signing_secret.encode("utf-8")

    def _sign(self, payload: str) -> str:
        return hmac.new(self._secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    def issue(
        self,
        credential_id: str,
        learner_name: str,
        course_title: str,
        pretest_score: float,
        posttest_score: float,
        verified_attempts: int,
    ) -> EvidenceCredential:
        issued_at = datetime.now(timezone.utc).isoformat()
        payload = f"{credential_id}|{learner_name}|{course_title}|{pretest_score:.2f}|{posttest_score:.2f}|{verified_attempts}|{issued_at}"
        return EvidenceCredential(
            credential_id=credential_id,
            learner_name=learner_name,
            course_title=course_title,
            pretest_score=pretest_score,
            posttest_score=posttest_score,
            verified_attempts=verified_attempts,
            issued_at=issued_at,
            signature=self._sign(payload),
        )

    def verify(self, cred: EvidenceCredential) -> bool:
        payload = f"{cred.credential_id}|{cred.learner_name}|{cred.course_title}|{cred.pretest_score:.2f}|{cred.posttest_score:.2f}|{cred.verified_attempts}|{cred.issued_at}"
        expected = self._sign(payload)
        return hmac.compare_digest(expected, cred.signature)
