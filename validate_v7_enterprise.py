"""Comprehensive verification suite for 3alimnIA V7.0 Enterprise Engines & Liquid Glass UI."""

from __future__ import annotations

from pathlib import Path

import safe_html
from v7_engines import (
    ABExperimentEngine,
    AIObservabilityTracker,
    AppSessionState,
    CitationAuditorEngine,
    CoCreationEngine,
    ConceptNode,
    CredentialEngine,
    InteractiveLabGenerator,
    KnowledgeGraphEngine,
    LTIIntegrationEngine,
    LabSpec,
    OfflinePackEngine,
    Permission,
    ProviderTelemetry,
    RBACEngine,
    ReviewCard,
    Role,
    SpacedRepetitionEngine,
    VoiceCoachEngine,
)

ROOT = Path(__file__).resolve().parent


def main() -> None:
    # 1. Liquid Glass CSS & XSS-safe HTML layer
    css = (ROOT / ".streamlit" / "app.css").read_text(encoding="utf-8")
    assert "backdrop-filter" in css and "Liquid Glass" in css
    assert "&lt;script&gt;" in safe_html.esc("<script>alert(1)</script>")
    assert safe_html.safe_url("javascript:alert(1)") == "#"
    assert safe_html.safe_url("https://example.org/course") == "https://example.org/course"
    assert "lg-hero" in safe_html.glass_hero("3alimnIA", "Liquid Glass", badges=["V7.1"])
    assert "@media (max-width: 1024px)" in css and "@media (max-width: 768px)" in css and "@media (max-width: 480px)" in css
    assert "prefers-color-scheme: dark" in css and "safe-area-inset-bottom" in css
    assert "lg-mobile-dock" in safe_html.glass_mobile_dock([{"label": "Home", "href": "/", "active": True}])
    assert "<svg" in safe_html.glass_progress_ring(88, "Mastery")

    # 2. Knowledge Graph Engine
    kg = KnowledgeGraphEngine([
        ConceptNode("c1", "الكيوبت", ()),
        ConceptNode("c2", "Hadamard", ("c1",)),
        ConceptNode("c3", "التشابك", ("c2",)),
    ])
    assert kg.topological_order() == ["c1", "c2", "c3"]
    recs = kg.recommend_next({"c1": 0.9, "c2": 0.4})
    assert recs[0]["concept_id"] == "c2"
    assert "<svg" in kg.render_svg({"c1": 0.9, "c2": 0.4})

    # 3. Sandboxed Interactive Lab Generator
    lab_html = InteractiveLabGenerator().build_sandboxed_html(
        LabSpec("lab1", "تجربة التراكب", "الفيزياء الكمومية", "الزاوية", 0.0, 3.14, 1.5, "f(x)")
    )
    assert "Content-Security-Policy" in lab_html and "default-src 'none'" in lab_html

    # 4. Spaced Repetition (SM-2)
    sr = SpacedRepetitionEngine()
    card = sr.review(ReviewCard("k1", "c2", "ما دور Hadamard؟", "توليد تراكب"), quality=5)
    assert card.repetitions == 1 and card.interval_days == 1
    card2 = sr.review(card, quality=5)
    assert card2.interval_days == 6

    # 5. Multilingual Voice Coach
    vc = VoiceCoachEngine()
    turn = vc.build_oral_check("بوابة Hadamard", ("تراكب", "قياس"), locale="ar")
    score = vc.score_transcript("تنشئ بوابة هادامارد حالة تراكب متساوٍ قبل القياس", turn)
    assert score["passed"] is True

    # 6. Co-Creation Multi-Signature Workflow
    cc = CoCreationEngine(required_signatures=2)
    cc.sign_off("prof_a", "author", True)
    assert not cc.can_publish()
    cc.sign_off("prof_b", "reviewer", True)
    assert cc.can_publish()

    # 7. Evidence-Backed Verifiable Credentials
    ce = CredentialEngine("super-strong-signing-secret-v7")
    cred = ce.issue("CRED-001", "أحمد", "الحوسبة الكمومية", 45.0, 88.0, 12)
    assert ce.verify(cred) is True

    # 8. LTI 1.3 & SCORM 2004
    lti = LTIIntegrationEngine()
    assert lti.build_ags_score_payload("u1", 91.5)["gradingProgress"] == "FullyGraded"
    assert "ADL SCORM" in lti.build_scorm_manifest("q101", "مقدمة الكم")

    # 9. Live Citation Auditor
    ca = CitationAuditorEngine()
    audit = ca.audit_text(
        "تحول بوابة هادامارد الكيوبت إلى تراكب متساوٍ.",
        [{"source_id": "SRC-1", "body": "تحول بوابة هادامارد الكيوبت إلى حالة تراكب متساوٍ عند التطبيق."}],
    )
    assert audit["overall_grounding_ratio"] == 1.0

    # 10. Offline Study Pack
    pack = OfflinePackEngine().export_html("مقرر الكم", [{"title": "الدرس 1", "content": "محتوى معتمد"}])
    assert "<!DOCTYPE html>" in pack and 'dir="rtl"' in pack

    # 11. A/B Experiment Suite
    ab = ABExperimentEngine()
    assert ab.assign_cohort("exp1", "stu1") in {"control", "treatment"}
    res = ab.evaluate([50, 55, 60, 52], [75, 80, 78, 82])
    assert res.cohens_d > 1.0 and "&" in ab.to_latex_row("Qiskit", res)

    # 12. RBAC, AI Observability & Typed Session State
    rbac = RBACEngine()
    assert rbac.can(Role.TEACHER, Permission.PUBLISH_COURSE)
    assert not rbac.can(Role.STUDENT, Permission.PUBLISH_COURSE)

    obs = AIObservabilityTracker()
    obs.record(ProviderTelemetry("groq", "llama-3.3", 420.0, 300, 180, True))
    assert obs.summary()["calls"] == 1

    st_state = AppSessionState()
    assert st_state.theme_mode == "liquid_glass_light"

    print("PASS validate_v7_enterprise.py — All 10 new engines + RBAC + Observability + Liquid Glass UI verified.")


if __name__ == "__main__":
    main()
