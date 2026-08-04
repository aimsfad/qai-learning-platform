# 3alimnIA V6.18.3 — مسار موجّه لاعتماد المخطط وبناء الدروس

## الهدف

يعالج هذا الإصدار الفجوة بين إنشاء مخطط المقرر وبدء بناء الدروس. كانت الوظائف متاحة، لكن الأستاذ كان يحتاج إلى استنتاج الخطوة التالية والتنقل يدويًا بين التبويبات والكتل. أصبح المسار الآن واضحًا ومتحكمًا في تبعياته:

```text
إنشاء المخطط
→ مراجعة الوحدات والدروس والأهداف
→ اعتماد النسخة
→ الانتقال إلى بناء الدروس
→ توليد جزء واحد
→ مراجعته واعتماده
→ الانتقال تلقائيًا إلى الجزء التالي
```

## المزايا المنفذة

### 1. عقد تشغيل مركزي

أضيف الملف:

```text
workflow_runtime_contracts.py
```

ويتحقق قبل عرض الواجهة من توافر كل الدوال والخصائص المطلوبة في:

- `lesson_blueprint_engine.py`
- `lesson_block_generation_engine.py`
- `db.py`

إذا كانت إحدى الوحدات غير متوافقة، تظهر رسالة آمنة ومحددة بدل وصول المستخدم إلى `AttributeError` متأخر.

### 2. رحلة فرعية للمخطط

تعرض صفحة المخطط أربع حالات مترابطة:

1. إنشاء المخطط.
2. مراجعة البنية.
3. اعتماد النسخة.
4. الانتقال إلى بناء الدروس.

كما أصبح زر الاعتماد ظاهرًا قبل التبويبات، بدل وجوده في أسفل صفحة طويلة.

### 3. بطاقات مؤشرات موحدة

تستخدم صفحة المخطط وبناء الدروس مكونات النظام البصري المركزي لعرض:

- الجاهزية.
- عدد الوحدات.
- عدد الدروس.
- عدد أهداف التعلم.
- عدد أجزاء الدرس المولدة والمعتمدة.

### 4. خريطة أجزاء الدرس

لكل درس تظهر خريطة من تسعة أجزاء:

1. تنشيط المعارف السابقة.
2. شرح المفهوم.
3. مثال محلول.
4. تدريب موجه.
5. تدريب مستقل.
6. الأخطاء الشائعة ومعالجتها.
7. تقويم تكويني.
8. ملخص الدرس.
9. موارد ومتابعة.

وتعرض كل بطاقة حالة واضحة:

```text
معتمدة
جاهزة للمراجعة
جارٍ التوليد
في قائمة الانتظار
تعذر التوليد
لم تبدأ
تنتظر اعتماد الجزء السابق
```

### 5. تسلسل موجّه

الإعداد الافتراضي:

```toml
LESSON_BLOCK_REQUIRE_SEQUENCE = "true"
```

يمنع بدء جزء جديد قبل اعتماد الجزء السابق. تبقى الإصدارات الموجودة قابلة للمراجعة وإعادة التوليد، لكن لا يبدأ النظام جزءًا لاحقًا جديدًا خارج التسلسل.

### 6. انتقال تلقائي

بعد اعتماد الجزء الحالي، تختار المنصة تلقائيًا أول جزء غير مكتمل. وبعد اكتمال الدرس يظهر زر للانتقال إلى الدرس التالي.

## الملفات الجديدة والمعدلة

```text
workflow_runtime_contracts.py             جديد
validate_v6183_guided_blueprint_lesson_flow.py  جديد
lesson_block_generation_engine.py         معدل
teacher_studio.py                         معدل
db.py                                     معدل
.streamlit/v6_theme.css                    معدل
.streamlit/secrets_example.toml            معدل
```

كما حُدّثت اختبارات التوافق السابقة لقبول رقم الإصدار الجديد.

## قاعدة البيانات

لا توجد جداول أو أعمدة جديدة. تغيير `db.py` يحدّث رقم التطبيق فقط:

```text
v6.18.3-guided-blueprint-lesson-production
```

## إعداد Secrets

أضيفي أو اتركي القيمة الافتراضية التالية:

```toml
LESSON_BLOCK_REQUIRE_SEQUENCE = "true"
```

لتعطيل التسلسل الإلزامي:

```toml
LESSON_BLOCK_REQUIRE_SEQUENCE = "false"
```

## أوامر التطبيق عبر CMD

```cmd
set "PROJECT=C:\Users\djenb\Downloads\Qantum study\qai_platform_"
set "PATCHZIP=%USERPROFILE%\Downloads\3alimnIA_V6.18.3_GUIDED_BLUEPRINT_LESSON_PRODUCTION_PATCH.zip"
set "PATCHDIR=%TEMP%\3alimnIA_V6183_PATCH"

cd /d "%PROJECT%"
git status
git switch main
git pull origin main
git switch -c feat/v6-18-3-guided-blueprint-lessons

if exist "%PATCHDIR%" rmdir /s /q "%PATCHDIR%"
mkdir "%PATCHDIR%"

tar -xf "%PATCHZIP%" -C "%PATCHDIR%"
xcopy "%PATCHDIR%\*" "%PROJECT%\" /E /I /Y /H

cd /d "%PROJECT%"
```

## الاختبارات

```cmd
py -3 validate_v6183_guided_blueprint_lesson_flow.py
py -3 validate_v6182_blueprint_editor_runtime_ui.py
py -3 validate_v6181_blueprint_api_contract.py
py -3 validate_v618_global_design_system.py
py -3 validate_v6173_blueprint_action_feedback.py
py -3 validate_v616_lesson_block_generation.py
py -3 -m compileall .
```

النتيجة الأساسية:

```text
V6.18.3 guided blueprint and lesson production validation passed.
```

## الرفع إلى GitHub

```cmd
git add workflow_runtime_contracts.py
git add lesson_block_generation_engine.py teacher_studio.py db.py
git add .streamlit\v6_theme.css .streamlit\secrets_example.toml
git add validate_v6183_guided_blueprint_lesson_flow.py
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
git add V6_18_3_GUIDED_BLUEPRINT_LESSON_PRODUCTION_AR.md
git add README.md CHANGELOG.md

git status
git diff --cached --stat

git commit -m "feat: guide blueprint approval and sequential lesson production"
git push -u origin feat/v6-18-3-guided-blueprint-lessons
```

بعد الدمج:

```text
Manage app → Reboot app
```

ثم تحديث قوي للصفحة:

```text
Ctrl + F5
```

## الاختبار الحي

1. افتحي مخطط المقرر.
2. تحققي من ظهور شريط المراحل الأربع.
3. راجعي المخطط واعتمديه من الزر الظاهر أعلى المحتوى.
4. انتقلي إلى بناء الدروس.
5. اختاري الدرس الأول.
6. ولّدي تنشيط المعارف السابقة.
7. اعتمدي الجزء.
8. تحققي من اختيار شرح المفهوم تلقائيًا.
9. حاولي اختيار جزء لاحق قبل اعتماد السابق؛ يجب أن يظهر تنبيه القفل.
10. أكملي الأجزاء التسعة وتحققي من ظهور زر الدرس التالي.
