# 3alimnIA V6.18 — نظام تصميم احترافي شامل للمنصة

## الهدف

يوحّد هذا الإصدار التصميم البصري وتجربة الاستخدام في الصفحات العامة، وفضاء المتعلم، ولوحة المقيّم والباحث، واستوديو الأستاذ. لا يغيّر قاعدة البيانات أو منطق البحث والتوليد، بل يبني طبقة Front-end مشتركة قابلة للصيانة.

## أهم التغييرات

### 1. ترويسة موحدة لكل الصفحات

أضيفت ترويسة مشتركة تعرض العنوان والوصف وهوية الفضاء في بطاقة هادئة، مع خط لوني دقيق بدل المساحات الداكنة الكبيرة. تستعملها صفحات المتعلم والمقيّم والأستاذ.

### 2. صفحات دخول مركزية

أصبحت صفحات دخول المتعلم والمقيّم والأستاذ داخل بطاقات مركزية بعرض مقيد، مع حقول متناسقة وتسلسل بصري واضح. كما أعيد تنظيم استمارة إنشاء حساب المتعلم داخل بطاقة واسعة مناسبة لسطح المكتب والهاتف.

### 3. لوحة المقيّم

- بطاقات KPI موحدة بأرقام Midnight Blue ووزن 900.
- الصيغة الصحيحة للمؤشرات مثل `+30.0 pp`.
- بطاقات مركز الإجراءات تدعم Hover وFocus.
- الرسوم البيانية بخلفية شفافة، دون شبكة عمودية، مع شبكة أفقية منقطة وخفيفة.
- التبويبات نصية بخط سفلي للتبويب النشط بدل الكتل الممتلئة.

### 4. فضاء المتعلم

- توحيد ترويسات الصفحات.
- تحسين بطاقات التقدم الحالية وبطاقة استئناف المسار.
- تقليل ازدحام الأزرار والبطاقات.
- المحافظة على بوابات المحاولة الأولى والموافقة البحثية.

### 5. استوديو الأستاذ

- ترويسة موحدة للفضاء.
- تحسين شبكة المشاريع وبطاقاتها.
- الحفاظ على رحلة إنشاء المقرر ذات المراحل السبع.
- توحيد البطاقات والنماذج والجداول وحالات الخطأ والفراغ.

### 6. شريط التنقل

- خلفية بيضاء مسطحة.
- الروابط العادية بلا تعبئة.
- خط سفلي للصفحة النشطة وتأثير Hover خفيف.
- زر رئيسي واحد فقط ممتلئ اللون.

### 7. الوصول والاستجابة

- Focus واضح بلوحة المفاتيح.
- احترام `prefers-reduced-motion`.
- دعم RTL وLTR.
- تخطيط متجاوب لسطح المكتب والحاسوب المحمول والهاتف.

## الملفات الأساسية

```text
global_design_system.py
main_app.py
teacher_studio.py
ui_v6.py
.streamlit/v6_theme.css
db.py
validate_v618_global_design_system.py
```

## ملاحظات التوافق

- لا يوجد ترحيل جديد لقاعدة البيانات.
- لا توجد Secrets جديدة.
- لا يتغير منطق البحث أو التوليد أو التصدير.
- يعتمد التصميم على مكونات Streamlit الأصلية مع CSS مركزي.

## تطبيق التحديث عبر CMD

```cmd
set "PROJECT=C:\Users\djenb\Downloads\Qantum study\qai_platform_"
set "PATCHZIP=%USERPROFILE%\Downloads\3alimnIA_V6.18_GLOBAL_PROFESSIONAL_DESIGN_SYSTEM_PATCH.zip"
set "PATCHDIR=%TEMP%\3alimnIA_V618_PATCH"

cd /d "%PROJECT%"
git status
git switch main
git pull origin main
git switch -c feat/v6-18-global-professional-design

if exist "%PATCHDIR%" rmdir /s /q "%PATCHDIR%"
mkdir "%PATCHDIR%"
tar -xf "%PATCHZIP%" -C "%PATCHDIR%"
xcopy "%PATCHDIR%\*" "%PROJECT%\" /E /I /Y /H
cd /d "%PROJECT%"
```

## اختبارات التحقق

```cmd
py -3 validate_v618_global_design_system.py
py -3 validate_v6173_blueprint_action_feedback.py
py -3 validate_v6172_simplified_guided_research_flow.py
py -3 validate_v6171_unified_guided_production_journey.py
py -3 validate_v617_hybrid_background_production.py
py -3 validate_v6165_ui_stability_design_system.py
py -3 -m compileall .
```

## الرفع إلى GitHub

```cmd
git add global_design_system.py
git add main_app.py teacher_studio.py ui_v6.py db.py
git add .streamlit\v6_theme.css
git add validate_v618_global_design_system.py
git add validate_v6173_blueprint_action_feedback.py
git add validate_v6172_simplified_guided_research_flow.py
git add validate_v6171_unified_guided_production_journey.py
git add validate_v617_hybrid_background_production.py
git add validate_v616_lesson_block_generation.py
git add validate_v615_blueprint_editor_versioning.py
git add validate_v6101_ai_tutor_state.py
git add validate_v693_save_prompt_hotfix.py
git add validate_v694_premium_logo_prompt_state.py
git add V6_18_GLOBAL_PROFESSIONAL_DESIGN_SYSTEM_AR.md
git add README.md CHANGELOG.md

git status
git diff --cached --stat
git commit -m "feat: add V6.18 global professional design system"
git push -u origin feat/v6-18-global-professional-design
```
