# 3alimnIA (علّمنيا) — V7.0 Liquid Glass Enterprise Edition

منصة تعليمية وبحثية متكاملة مدعومة بالذكاء الاصطناعي التربوي، تجمع بين **الحوكمة البشرية للمحتوى**، و**محرك Hybrid RAG معزول لكل أستاذ ومشروع على Neon/pgvector**، و**واجهة Liquid Glass فاخرة** تدعم العربية (RTL) والفرنسية والإنجليزية (LTR).

## أبرز ما أُنجز في الإصدار V7.0

### 1. التصليحات الحرجة العشرة (Security, Stability & Repo Hygiene)
- إزالة ملفات الأسرار الحية وتحصين `package_release.py` بمنع تلقائي لأي تسرب.
- فك ارتباط `db.py` عن الاستيراد الإلزامي لـ `streamlit` لدعم عمال الخلفية (RQ) والاختبارات المستقلة.
- إنشاء بوابة الأمان `validate_release_security.py` وتحديث `validate_current_release.py`.
- تنظيف المجلد الجذري من الملفات الطرفية العالقة والنسخ الاحتياطية وأرشفة الوثائق التاريخية في `docs/archive/` و`tests/legacy_validators/`.
- توحيد مشغّل PostgreSQL على `psycopg[binary]` وإضافة `alembic` و`requirements-dev.txt`.
- تحصين استعلامات SQL الديناميكية في `hybrid_rag.py` و`rag_postgres.py`.
- إضافة طبقة تعقيم HTML مركزية (`safe_html.py`) للحماية من XSS.
- حذف 9 ملفات CSS قديمة وتوحيد الواجهة بالكامل في `.streamlit/app.css` (8.5 KB بدل 964 KB).

### 2. الواجهة الأمامية بالنمط الزجاجي السائل (Liquid Glass UI)
- تصميم زجاجي سائل متعدد الطبقات (`backdrop-filter: blur(26px) saturate(185%)`) مع انعكاسات ضوئية ناعمة وتباين لوني متوافق مع معايير WCAG AA/AAA.
- معاينة تفاعلية حية مرفقة داخل `assets/branding/v7_liquid_glass_preview.html`.

### 3. المحركات الجديدة العشرة (`v7_engines/`)
1. `knowledge_graph_engine.py` — خريطة الإتقان المعرفي الديناميكية (DAG + SVG).
2. `interactive_lab_generator.py` — مولّد المختبرات التفاعلية المعزولة بـ CSP لأي تخصص.
3. `spaced_repetition_engine.py` — محرك المراجعة المتباعدة التكيفي (SM-2).
4. `voice_coach_engine.py` — المدرب الصوتي متعدد اللغات (AR / FR / EN).
5. `co_creation_engine.py` — استوديو التأليف الجماعي والمراجعة العلمية متعددة التوقيعات.
6. `credential_engine.py` — شهادات الإتقان الموثّقة بالأدلة وتوقيع HMAC-SHA256.
7. `lti_integration_engine.py` — التكامل القياسي مع الجامعات (LTI 1.3 & SCORM 2004).
8. `citation_auditor_engine.py` — مدقق الاستشهاد الحي وكاشف الهلوسة على مستوى الجملة.
9. `offline_pack_engine.py` — تصدير حزم الدراسة للعمل دون إنترنت.
10. `ab_experiment_engine.py` — مختبر التجارب التربوية A/B (Welch t-test & Cohen's d + LaTeX).

إضافةً إلى وحدات البنية المؤسسية: `rbac_engine.py`، `ai_observability.py`، `session_state_contracts.py`، `alembic.ini`، و`.github/workflows/ci.yml`.

## التشغيل والتحقق السريع

```bash
pip install -r requirements-dev.txt
python validate_current_release.py
streamlit run app.py
```

لتغليف إصدار نظيف وآمن للمشاركة:
```bash
python package_release.py
```
