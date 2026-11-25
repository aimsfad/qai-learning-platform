# 3alimnIA V6.18.2
## إصلاح تشغيل محرر المخطط وصقل واجهة الأستاذ

## 1. سبب التحديث

أظهرت التجربة الحية مشكلتين منفصلتين:

1. ظهور وسم HTML خام `</div>` داخل بطاقة عنوان فضاء الأستاذ.
2. توقف محرر المخطط برسالة:

```text
module 'lesson_blueprint_engine' has no attribute 'prepare_editor_draft'
```

الخطأ الثاني لم يكن دالة واحدة فقط؛ واجهة الأستاذ كانت تستدعي مجموعة كاملة من وظائف التحرير غير الموجودة في المحرك، كما أن حفظ النسخة اليدوية كان يستخدم توقيعًا قديمًا لا يتوافق مع عقد قاعدة البيانات الحالي.

## 2. الإصلاحات البرمجية

### 2.1 استعادة واجهة محرر المخطط كاملة

أضيفت الوظائف التالية إلى `lesson_blueprint_engine.py`:

```text
prepare_editor_draft
normalize_blueprint
recompute_blueprint_quality
compare_blueprints
add_unit / update_unit / move_unit / delete_unit
add_lesson / update_lesson / move_lesson / delete_lesson
add_outcome / update_outcome / delete_outcome
```

تدعم هذه الوظائف:

- إنشاء مسودة مستقلة عن النسخة المحفوظة.
- الحفاظ على المعرفات المستقرة للوحدات والدروس والأهداف.
- إعادة ترتيب الوحدات والدروس.
- حذف العلاقات التابعة بأمان.
- إعادة بناء روابط الوحدة بالدروس والمفاهيم والمصادر.
- إعادة حساب التغطية والمحاذاة وسلامة البنية بعد كل تعديل.

### 2.2 إصلاح حفظ الإصدارات اليدوية

أصبح الحفظ يستخدم العقد الحالي:

```python
save_manual_revision(
    project,
    teacher_username,
    base_run_id=...,
    edited_blueprint=...,
    change_summary=...,
)
```

مع دعم استدعاء V6.15 القديم بصورة توافقية حتى لا تتعطل الجلسات أو الاختبارات السابقة.

عند حفظ إصدار جديد:

- يلغى اعتماد الإصدار السابق.
- ينشأ رقم إصدار جديد.
- تحفظ حالة الجودة.
- تسجل عملية `manual_edit`.
- تسجل التغييرات التفصيلية على الوحدات والدروس والأهداف.

### 2.3 منع أخطاء API غير المكتملة

قبل فتح المحرر تتحقق الواجهة من وجود جميع وظائف التحرير المطلوبة. عند نقص أي وظيفة، تظهر بطاقة خطأ آمنة بدل انهيار الصفحة.

### 2.4 إصلاح وسم `</div>` الظاهر

أصبح رأس الصفحة يُرسل إلى Streamlit كشجرة HTML واحدة متوازنة ومن دون مسافات بادئة قد يحولها Markdown إلى كتلة كود. بذلك لا يظهر الوسم الخام بعد إعادة التشغيل أو تغيير اللغة.

## 3. التحسينات البصرية

- ترويسة أكثر اختصارًا لفضاء الأستاذ.
- شارة واضحة باسم `Content Studio`.
- وسوم صغيرة توضح رحلة العمل من سبع مراحل والمراجعة البشرية.
- تحويل اختيار أقسام الاستوديو إلى شريط تنقل بصري أكثر وضوحًا.
- تحسين حالة Hover والصفحة النشطة.
- إبراز أرقام مؤشرات المخطط بلون Midnight Blue ووزن خط أقوى.
- تمرير أفقي آمن لشريط الأقسام على الهاتف.
- توحيد الحواف والظلال والمسافات مع نظام V6.18 العام.

## 4. الملفات المعدلة

```text
global_design_system.py
lesson_blueprint_engine.py
teacher_studio.py
db.py
.streamlit/v6_theme.css
README.md
CHANGELOG.md
```

وأضيف:

```text
validate_v6182_blueprint_editor_runtime_ui.py
V6_18_2_BLUEPRINT_EDITOR_RUNTIME_UI_POLISH_AR.md
```

كما حُدثت اختبارات التوافق التي تتحقق من رقم الإصدار.

## 5. قاعدة البيانات وSecrets

- لا توجد جداول جديدة.
- لا يوجد ترحيل SQL جديد.
- لا توجد مفاتيح Secrets جديدة.
- لا تعاد عملية البحث أو تركيب الأدلة أو إنشاء المخطط الأساسي.

## 6. تطبيق التحديث عبر CMD

```cmd
set "PROJECT=C:\Users\djenb\Downloads\Qantum study\qai_platform_"
set "PATCHZIP=%USERPROFILE%\Downloads\3alimnIA_V6.18.2_BLUEPRINT_EDITOR_RUNTIME_UI_POLISH_PATCH.zip"
set "PATCHDIR=%TEMP%\3alimnIA_V6182_PATCH"

cd /d "%PROJECT%"
git status
git switch main
git pull origin main
git switch -c fix/v6-18-2-blueprint-editor-ui

if exist "%PATCHDIR%" rmdir /s /q "%PATCHDIR%"
mkdir "%PATCHDIR%"
tar -xf "%PATCHZIP%" -C "%PATCHDIR%"
xcopy "%PATCHDIR%\*" "%PROJECT%\" /E /I /Y /H

cd /d "%PROJECT%"
```

## 7. الاختبارات

```cmd
py -3 validate_v6182_blueprint_editor_runtime_ui.py
py -3 validate_v6181_blueprint_api_contract.py
py -3 validate_v618_global_design_system.py
py -3 validate_v6173_blueprint_action_feedback.py
py -3 validate_v615_blueprint_editor_versioning.py
py -3 -m compileall .
```

النتيجة الأساسية:

```text
V6.18.2 blueprint editor runtime and UI validation passed.
```

## 8. رفع التحديث

```cmd
git add global_design_system.py lesson_blueprint_engine.py teacher_studio.py db.py
git add .streamlit\v6_theme.css
git add validate_v6182_blueprint_editor_runtime_ui.py
git add validate_v6181_blueprint_api_contract.py
git add validate_v618_global_design_system.py
git add validate_v6173_blueprint_action_feedback.py
git add validate_v6172_simplified_guided_research_flow.py
git add validate_v6171_unified_guided_production_journey.py
git add validate_v616_lesson_block_generation.py
git add validate_v615_blueprint_editor_versioning.py
git add validate_v6101_ai_tutor_state.py
git add validate_v693_save_prompt_hotfix.py
git add validate_v694_premium_logo_prompt_state.py
git add V6_18_2_BLUEPRINT_EDITOR_RUNTIME_UI_POLISH_AR.md README.md CHANGELOG.md

git status
git diff --cached --stat

git commit -m "fix: restore blueprint editor runtime and polish teacher UI"
git push -u origin fix/v6-18-2-blueprint-editor-ui
```

بعد الدمج:

```text
Manage app → Reboot app
Ctrl + F5
```

## 9. اختبار الواجهة بعد النشر

1. افتح فضاء الأستاذ وتأكد من اختفاء `</div>`.
2. افتح مشروعًا ثم مرحلة مخطط المقرر.
3. افتح تبويب محرر المخطط.
4. عدل عنوان وحدة ثم احفظ التعديل في المسودة.
5. أضف درسًا وهدف تعلم.
6. أدخل ملخص التعديل واضغط حفظ إصدار جديد.
7. تحقق من ظهور الإصدار الجديد في تبويب الإصدارات والسجل.
8. أعد اعتماد الإصدار الجديد قبل الانتقال إلى بناء الدروس.
