# 3alimnIA V6.18.6 — دمج التصميم الاحترافي الموحد داخل المشروع الحقيقي

## الهدف

هذا الإصدار لا يستبدل المشروع ولا ينشئ تطبيق Streamlit منفصلًا. تم استخراج أفضل عناصر الـPremium SaaS shell ودمجها داخل طبقات الواجهة الموجودة فعلًا في 3alimnIA مع الحفاظ على منطق الأعمال، قاعدة البيانات، البحث، الأدلة، مخطط المقرر، توليد الدروس، AI Coach، LPQS، والتصدير البحثي.

## مبدأ الدمج

- **Design System واحد** لجميع الأدوار.
- **لا تغيير في محركات التوليد أو مخطط قاعدة البيانات**.
- الحفاظ على الـcallbacks، مفاتيح `session_state`، ومسارات Streamlit الحالية.
- استخدام CSS scoped عبر role markers بدل إعادة كتابة الصفحات.
- إبقاء الأزرار والعناصر التفاعلية Native Streamlit لضمان الاعتمادية.

## نظام التصميم

- الخط الأساسي: Tajawal، مع إبقاء الكود بخط monospace.
- Primary: `#1D4ED8`.
- Midnight: `#0F172A`.
- Workspace background: `#F8FAFC`.
- Success: `#10B981`.
- Muted/disabled: `#94A3B8`.
- Border: `#E2E8F0`.
- Radius: 10–16px للعناصر التشغيلية والبطاقات.
- ظلال منخفضة الكثافة، مع Hover بارتفاع 2px للعناصر التفاعلية.
- الأزرار الأساسية مستطيلة ناعمة، ولا تستخدم Pill shape إلا شارات الحالة.

## ما تغير حسب الدور

### الواجهة العامة

- Navbar أكثر تسطحًا وهدوءًا.
- الروابط الثانوية بدون تعبئة لونية ثقيلة.
- إجراء أساسي واحد فقط يحتفظ باللون الممتلئ.
- خلفية موحدة وبطاقات أكثر هدوءًا.

### الطالب

- الحفاظ على Split-pane الحالي بين مساحة التعلم وAI Coach.
- توحيد الحواف والظلال والمسافات.
- الحفاظ على Attempt-First Gate وكل سجلات البحث والتعلم.
- لم يتم تغيير محرك Qiskit أو AI Coach.

### الأستاذ

- الحفاظ على الرحلة المبسطة ذات الخمس خطوات.
- تحويل أزرار المراحل إلى Workflow cards واضحة بدل مظهر Radio/Pill.
- المرحلة الحالية هي العنصر البصري الأقوى، والمراحل المقفلة أكثر هدوءًا.
- Premium Lesson Workspace وPedagogical Orchestrator من V6.18.5 بقيا كما هما وظيفيًا.

### الباحث/لوحة التحليل

- توحيد KPI cards وألوانها وطباعة الأرقام.
- استخدام Tajawal داخل Plotly.
- خلفيات المخططات شفافة وشبكات أفقية خفيفة وفق النظام الموجود منذ V6.18.

### المقيّم

- إعادة ترتيب تقييم استجابة AI إلى واجهة Side-by-side فعلية:
  - الاستجابة والسياق في عمود.
  - Rubric وLPQS في عمود موازٍ وثابت على سطح المكتب.
- لم تتغير معايير LPQS أو طريقة الحفظ في قاعدة البيانات.

## الملفات التي تم تعديلها

- `global_design_system.py`
- `.streamlit/v6_theme.css`
- `app.py`
- `main_app.py`
- `teacher_studio.py`
- `db.py` — رقم الإصدار فقط
- Validators السابقة لقبول الإصدار الجديد

## الملفات التي لم يتم تغيير منطقها

- `lesson_block_generation_engine.py`
- `lesson_blueprint_engine.py`
- `pedagogical_orchestrator.py`
- `production_pipeline.py`
- `evidence_synthesis_engine.py`
- `web_research_engine.py`
- `content_generation_engine.py`

وبالتالي لا يوجد فقدان للعمل السابق أو إعادة بناء للمحركات.

## الاختبار

```cmd
py -3 validate_v6186_unified_premium_platform_design.py
py -3 validate_v6185_premium_lesson_workspace.py
py -3 validate_v6184_simple_teacher_journey.py
py -3 validate_v6183_guided_blueprint_lesson_flow.py
py -3 validate_v6182_blueprint_editor_runtime_ui.py
py -3 validate_v6181_blueprint_api_contract.py
py -3 validate_v618_global_design_system.py
py -3 -m compileall .
```

## التحقق الحي بعد النشر

1. الصفحة الرئيسية وNavbar.
2. تسجيل دخول الطالب والأستاذ والمقيّم.
3. Learning Module: Split-pane + AI Coach.
4. Teacher Studio: رحلة 5 خطوات + Premium Lesson Workspace.
5. Research Dashboard: KPIs + Plotly.
6. Evaluator: Side-by-side response + LPQS rubric.
7. العربية RTL، الفرنسية والإنجليزية، ثم الهاتف.

## ملاحظة تشغيلية

هذا إصدار Front-End integration. لا توجد Secrets جديدة ولا Migration جديدة لقاعدة البيانات.
