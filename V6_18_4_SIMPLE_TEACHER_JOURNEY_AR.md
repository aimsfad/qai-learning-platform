# 3alimnIA V6.18.4 — Simple Teacher Journey

## الهدف

يجعل هذا الإصدار واجهة الأستاذ مفهومة للمستخدم غير التقني، مع الحفاظ على جميع المحركات المتقدمة في الخلفية. الوضع المبسط هو الوضع الافتراضي، ويمكن فتح الوضع المتقدم اختياريًا.

## رحلة الأستاذ الجديدة

1. إعداد المقرر.
2. إضافة المصادر والتحقق منها.
3. مراجعة خطة المقرر واعتمادها.
4. إنشاء الدروس واعتمادها.
5. المراجعة والنشر.

تُجمع المراحل التقنية السابقة داخل هذه الخطوات الخمس، ولا تُعرض تفاصيل المزوّد والنموذج والإصدارات وسجلات التشغيل إلا داخل الوضع المتقدم.

## إنشاء الدرس بزر واحد

في الوضع المبسط يختار الأستاذ الدرس ثم يضغط «إنشاء الدرس بالكامل». تنشئ المنصة الأقسام التسعة بالترتيب وتحفظ كل قسم كنسخة مستقلة قابلة للتحرير، ثم تعرض الدرس كاملًا للمراجعة.

الأقسام هي:

- تنشيط المعارف السابقة.
- شرح المفهوم.
- مثال محلول.
- تدريب موجه.
- تدريب مستقل.
- الأخطاء الشائعة ومعالجتها.
- تقويم تكويني.
- ملخص الدرس.
- موارد ومتابعة.

لا تعتمد المنصة الدرس تلقائيًا. بعد المراجعة يضغط الأستاذ «اعتماد الدرس والانتقال إلى التالي».

## وضعا الاستخدام

### الوضع المبسط — الافتراضي

- خمس خطوات فقط.
- إجراء رئيسي واحد في كل شاشة.
- انتقال تلقائي بعد الاعتماد.
- عرض خطة المقرر كوحدات ودروس واضحة.
- عرض الدرس كاملًا بدل التعامل الإجباري مع تسع عمليات منفصلة.
- إخفاء التفاصيل التقنية.

### الوضع المتقدم

يحافظ على:

- رحلة المراحل السبع.
- بطاقات الأدلة.
- محرر المخطط والإصدارات.
- توليد كل قسم بصورة مستقلة.
- سجلات التشغيل والمزوّد والنموذج.
- المخرجات التقنية الكاملة.

## الملفات الأساسية

- `simple_teacher_journey.py`: تجميع المسار الداخلي في خمس خطوات.
- `teacher_studio.py`: واجهة الأستاذ المبسطة وخيارات الوضع المتقدم.
- `lesson_block_generation_engine.py`: إنشاء درس كامل واعتماده مع الحفاظ على نسخ الأقسام.
- `.streamlit/v6_theme.css`: تصميم الخطوات وصفحة الدرس وشريط الإجراءات.
- `validate_v6184_simple_teacher_journey.py`: اختبار المسار وعقد إنشاء الدرس.

## الإعداد الاختياري

```toml
TEACHER_SIMPLE_MODE_DEFAULT = "true"
```

حتى إذا لم يُضف الإعداد، يبقى الوضع المبسط هو الافتراضي.

## تطبيق التحديث عبر CMD

```cmd
set "PROJECT=C:\Users\djenb\Downloads\Qantum study\qai_platform_"
set "PATCHZIP=%USERPROFILE%\Downloads\3alimnIA_V6.18.4_SIMPLE_TEACHER_JOURNEY_PATCH.zip"
set "PATCHDIR=%TEMP%\3alimnIA_V6184_PATCH"

cd /d "%PROJECT%"
git status
git switch main
git pull origin main
git switch -c feat/v6-18-4-simple-teacher-journey

if exist "%PATCHDIR%" rmdir /s /q "%PATCHDIR%"
mkdir "%PATCHDIR%"
tar -xf "%PATCHZIP%" -C "%PATCHDIR%"
xcopy "%PATCHDIR%\*" "%PROJECT%\" /E /I /Y /H

cd /d "%PROJECT%"
```

## الاختبارات

```cmd
py -3 validate_v6184_simple_teacher_journey.py
py -3 validate_v6183_guided_blueprint_lesson_flow.py
py -3 validate_v6182_blueprint_editor_runtime_ui.py
py -3 validate_v6181_blueprint_api_contract.py
py -3 validate_v618_global_design_system.py
py -3 validate_v6173_blueprint_action_feedback.py
py -3 validate_v6172_simplified_guided_research_flow.py
py -3 validate_v6171_unified_guided_production_journey.py
py -3 validate_v616_lesson_block_generation.py
py -3 -m compileall .
```

## رفع التحديث

```cmd
git add simple_teacher_journey.py
git add lesson_block_generation_engine.py teacher_studio.py db.py
git add .streamlit\v6_theme.css .streamlit\secrets_example.toml
git add validate_v6184_simple_teacher_journey.py
git add validate_v6182_blueprint_editor_runtime_ui.py
git add validate_v618_global_design_system.py
git add validate_v6173_blueprint_action_feedback.py
git add validate_v6172_simplified_guided_research_flow.py
git add validate_v6171_unified_guided_production_journey.py
git add validate_v616_lesson_block_generation.py
git add validate_v615_blueprint_editor_versioning.py
git add validate_v6101_ai_tutor_state.py
git add validate_v693_save_prompt_hotfix.py
git add validate_v694_premium_logo_prompt_state.py
git add V6_18_4_SIMPLE_TEACHER_JOURNEY_AR.md README.md CHANGELOG.md

git status
git diff --cached --stat
git commit -m "feat: add V6.18.4 simple teacher journey"
git push -u origin feat/v6-18-4-simple-teacher-journey
```

بعد الدمج، أعِد تشغيل Streamlit ونفّذ تحديثًا قسريًا للصفحة.

## حدود الاختبار

اجتاز الإصدار الاختبارات السلوكية والساكنة وفحص Python. لم يُجر اختبار حي باستدعاءات Groq أو Gemini داخل حساب Streamlit الخاص بالمستخدم، لذلك يجب تجربة إنشاء درس واحد كامل بعد النشر قبل تشغيل جميع الدروس.
