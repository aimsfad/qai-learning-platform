"""Interactive Streamlit Hub for all 10 3alimnIA V7.1 Enterprise Engines."""

from __future__ import annotations

import streamlit as st
import safe_html
from v7_engines import (
    ABExperimentEngine,
    CitationAuditorEngine,
    CoCreationEngine,
    ConceptNode,
    CredentialEngine,
    InteractiveLabGenerator,
    KnowledgeGraphEngine,
    LTIIntegrationEngine,
    LabSpec,
    OfflinePackEngine,
    ReviewCard,
    SpacedRepetitionEngine,
    VoiceCoachEngine,
)


def render_v7_hub() -> None:
    """Render the interactive V7.1 Liquid Glass Enterprise Suite inside Streamlit."""
    st.markdown(
        safe_html.glass_hero(
            "مركز ميزات 3alimnIA V7.1 — Ultra Liquid Glass",
            "جرّب جميع المحركات العشرة الجديدة مباشرةً من هنا بواجهة زجاجية سائلة متجاوبة مع الهاتف والتابلت والحاسوب.",
            badges=["V7.1 Live", "10 محركات جديدة", "متجاوب 100%"],
        ),
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "خريطة الإتقان",
        "مدقق الاستشهاد",
        "المراجعة SM-2",
        "مولّد المختبرات",
        "التجارب A/B",
        "الشهادات وLTI وOffline",
    ])

    with tabs[0]:
        kg = KnowledgeGraphEngine([
            ConceptNode("q1", "الكيوبت والقياس", ()),
            ConceptNode("q2", "بوابة Hadamard", ("q1",)),
            ConceptNode("q3", "التشابك CNOT", ("q2",)),
            ConceptNode("q4", "دوائر Bell", ("q3",)),
        ])
        c1, c2 = st.columns(2)
        m1 = c1.slider("إتقان الكيوبت والقياس", 0.0, 1.0, 0.92, 0.02, key="v7_m1")
        m2 = c2.slider("إتقان بوابة Hadamard", 0.0, 1.0, 0.80, 0.02, key="v7_m2")
        m3 = c1.slider("إتقان التشابك CNOT", 0.0, 1.0, 0.45, 0.02, key="v7_m3")
        m4 = c2.slider("إتقان دوائر Bell", 0.0, 1.0, 0.10, 0.02, key="v7_m4")
        scores = {"q1": m1, "q2": m2, "q3": m3, "q4": m4}
        st.markdown(kg.render_svg(scores), unsafe_allow_html=True)
        recs = kg.recommend_next(scores)
        if recs:
            st.success(f"الخطوة التالية المقترحة: **{recs[0]['title']}** (الإتقان الحالي {int(float(recs[0]['current_mastery'])*100)}%)")

    with tabs[1]:
        src_text = st.text_area(
            "نص مرجع الأستاذ المعتمد (RAG)",
            "تحول بوابة هادامارد الكيوبت من الحالة الأساسية إلى تراكب متساوي الاحتمال قبل القياس.",
            key="v7_rag_src",
        )
        gen_text = st.text_area(
            "النص المولّد المطلوب تدقيقه",
            "تحول بوابة هادامارد الكيوبت إلى تراكب متساوي الاحتمال. كما يمكنها تشغيل محرك صاروخي في الفضاء.",
            key="v7_rag_gen",
        )
        res = CitationAuditorEngine().audit_text(gen_text, [{"source_id": "TEACHER-SRC-01", "body": src_text}])
        st.metric("نسبة الإسناد الكلية للمصادر المعتمدة", f"{int(res['overall_grounding_ratio'] * 100)}%")
        for s in res["sentences"]:
            badge = "موثّق" if s.grounded else "غير مسنود"
            tone = "emerald" if s.grounded else "rose"
            st.markdown(
                safe_html.glass_card(
                    s.sentence,
                    f"درجة التطابق: {s.grounding_score} · المصدر: {s.best_source_id or 'لا يوجد'}",
                    badge=badge,
                    tone=tone,
                ),
                unsafe_allow_html=True,
            )

    with tabs[2]:
        quality = st.slider("قيّم تذكّرك لمفهوم التراكب الكمومي (0 = نسيته، 5 = أتقنته تمامًا)", 0, 5, 4, key="v7_sm2_q")
        card = SpacedRepetitionEngine().review(
            ReviewCard("c1", "q2", "ما دور بوابة Hadamard؟", "إنشاء تراكب متساوي الاحتمال"),
            quality=quality,
        )
        st.markdown(
            safe_html.glass_metric_row([
                {"label": "الفاصل الزمني القادم", "value": f"{card.interval_days} يوم"},
                {"label": "معامل السهولة (EF)", "value": f"{card.ease_factor}"},
                {"label": "التكرارات الناجحة", "value": f"{card.repetitions}"},
            ]),
            unsafe_allow_html=True,
        )
        vc = VoiceCoachEngine()
        turn = vc.build_oral_check("بوابة Hadamard", ("تراكب", "قياس"), locale="ar")
        st.info(f"المدرب الصوتي ({turn.bcp47}): {turn.spoken_prompt}")

    with tabs[3]:
        lab_title = st.text_input("عنوان المختبر التفاعلي", "محاكي التراكب الكمومي التفاعلي", key="v7_lab_title")
        lab_html = InteractiveLabGenerator().build_sandboxed_html(
            LabSpec("lab_v7", lab_title, "3alimnIA Interactive Lab", "الزاوية θ", 0.0, 6.28, 1.57, "f(θ)")
        )
        st.download_button("تنزيل المختبر التفاعلي (HTML معزول بـ CSP)", lab_html, file_name="interactive_lab_v7.html", mime="text/html")

    with tabs[4]:
        ab = ABExperimentEngine()
        res_ab = ab.evaluate([52, 58, 61, 55, 60], [76, 82, 79, 85, 81])
        st.markdown(
            safe_html.glass_metric_row([
                {"label": "متوسط الضابطة", "value": f"{res_ab.control_mean}"},
                {"label": "متوسط التجريبية", "value": f"{res_ab.treatment_mean}", "delta": f"+{res_ab.mean_diff}"},
                {"label": "حجم الأثر (Cohen's d)", "value": f"{res_ab.cohens_d}"},
                {"label": "قيمة Welch t", "value": f"{res_ab.welch_t}"},
            ]),
            unsafe_allow_html=True,
        )
        st.code(ab.to_latex_row("3alimnIA V7.1", res_ab), language="latex")

    with tabs[5]:
        ce = CredentialEngine("3alimnia-v7-demo-signing-key-2026")
        cred = ce.issue("CRED-V7-001", "متعلم 3alimnIA", "الحوسبة الكمومية", 48.0, 91.0, 14)
        st.markdown(
            safe_html.glass_card(
                f"شهادة موثّقة بالأدلة — {cred.course_title}",
                f"التحسن: {cred.pretest_score}% ← {cred.posttest_score}% · المحاولات الموثّقة: {cred.verified_attempts}",
                badge="HMAC-SHA256 Verified" if ce.verify(cred) else "Invalid",
                tone="emerald",
                footer=f"Signature: {cred.signature[:28]}...",
            ),
            unsafe_allow_html=True,
        )
        pack_html = OfflinePackEngine().export_html(
            "مقرر 3alimnIA دون إنترنت",
            [{"title": "الدرس الأول: التراكب", "content": "حزمة دراسة خفيفة تعمل دون اتصال."}],
        )
        scorm_xml = LTIIntegrationEngine().build_scorm_manifest("3alimnia-q101", "مقرر الحوسبة الكمومية")
        c1, c2 = st.columns(2)
        c1.download_button("تنزيل حزمة الدراسة دون إنترنت (HTML)", pack_html, file_name="3alimnia_offline_pack.html", mime="text/html")
        c2.download_button("تنزيل ملف SCORM 2004 Manifest", scorm_xml, file_name="imsmanifest.xml", mime="application/xml")
