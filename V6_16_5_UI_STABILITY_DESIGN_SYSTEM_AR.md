# 3alimnIA V6.16.5 — تثبيت الواجهة ونظام التصميم الموحد

## 1. الهدف

يحوّل هذا الإصدار التحسينات البصرية المتراكمة إلى طبقة واجهة أكثر ثباتًا وقابلية للصيانة قبل إضافة خط الإنتاج الخلفي في V6.17. لا يضيف جداول جديدة ولا يغيّر محركات البحث أو التوليد أو تركيب الأدلة.

## 2. المشكلة التي يعالجها

أظهرت الإصدارات السابقة أن التعديل المباشر في عدة صفحات قد يؤدي إلى اختلافات في المسافات والحالات أو أخطاء تشغيلية مثل قيم تخطيط غير مدعومة في Streamlit. لذلك يضيف V6.16.5 طبقة مشتركة تتحكم في:

- خيارات الأعمدة والمحاذاة المدعومة.
- عرض الأخطاء بصورة مبسطة وآمنة.
- أسماء حالات المراحل وألوانها.
- رموز التصميم الأساسية: الألوان، الحواف، المسافات والظلال.
- وضوح التركيز بلوحة المفاتيح وتقليل الحركة عند طلب المستخدم.

## 3. الملفات الجديدة والمعدلة

### ملف جديد

```text
ui_stability.py
```

يوفر:

- `columns(...)`: ينظف قيم `gap` و`vertical_alignment` ويستعمل بديلًا متوافقًا إذا كان إصدار Streamlit لا يدعم المحاذاة الرأسية.
- `status_semantics(...)`: يوحد الحالات مثل `completed`, `needs_review`, `queued`, `failed`.
- `status_badge_html(...)`: ينشئ شارة حالة موحدة.
- `friendly_error(...)`: يحول أخطاء المزود أو العرض إلى رسالة مناسبة للأستاذ.
- `render_error_card(...)`: يعرض رسالة آمنة مع رمز حادثة وتفاصيل تقنية مغلقة.

### ملفات معدلة

```text
teacher_studio.py
ui_v6.py
main_app.py
.streamlit/v6_theme.css
README.md
CHANGELOG.md
```

## 4. تحسينات الثبات

### 4.1 الأعمدة الآمنة

بدل تمرير قيمة غير مدعومة مباشرة إلى `st.columns`، تمر المكونات الأساسية عبر:

```python
ui_stability.columns(
    [2.25, 1],
    gap="large",
    vertical_alignment="top",
)
```

القيم المسموحة للمحاذاة هي:

```text
top
center
bottom
```

وأي قيمة أخرى تتحول إلى `top` بدل إسقاط التطبيق.

### 4.2 أخطاء آمنة للمستخدم

لم تعد أخطاء مساحة الأستاذ تظهر كرسالة مزود طويلة. تظهر بطاقة مبسطة تحتوي على:

- وصف مفهوم للمشكلة.
- تأكيد حفظ بيانات المشروع.
- رمز حادثة قصير.
- زر إعادة المحاولة عند الحاجة.
- تفاصيل تقنية داخل قسم مغلق.

### 4.3 حالات موحدة

يوحد النظام الحالات التالية:

```text
معتمدة
جاهزة
تحتاج مراجعة
جارٍ التنفيذ
في قائمة الانتظار
تنتظر مرحلة سابقة
تعذر التنفيذ
لم تبدأ
```

ويستعمل نص الحالة بالإضافة إلى اللون، حتى لا تعتمد الواجهة على اللون وحده.

## 5. نظام التصميم

أضيفت متغيرات مركزية من نوع:

```css
--qai-primary
--qai-success
--qai-warning
--qai-danger
--qai-radius-md
--qai-space-4
--qai-shadow-md
```

كما أضيفت مكونات مشتركة:

```text
.qai-status-badge
.qai-ui-error-card
.qai-ui-empty-state
```

## 6. الوصول والاستجابة

يتضمن الإصدار:

- `focus-visible` للأزرار والحقول والروابط.
- تباينًا واضحًا للحالات.
- نصًا مصاحبًا للنقاط اللونية.
- دعم `prefers-reduced-motion`.
- ضبط بطاقات الأخطاء والحالات على الهاتف.
- المحافظة على العربية RTL والفرنسية والإنجليزية LTR.

## 7. اختبار الإصدار

شغّل:

```cmd
py -3 validate_v6165_ui_stability_design_system.py
py -3 validate_v6164_research_export_analytics.py
py -3 validate_v61631_frontend_runtime_hotfix.py
py -3 validate_v6163_professional_layout_polish.py
py -3 -m compileall .
```

النتيجة الأساسية المتوقعة:

```text
V6.16.5 UI stability and design-system validation passed.
```

## 8. تطبيق التحديث عبر CMD

بعد تنزيل ملف PATCH:

```cmd
set "PROJECT=C:\Users\djenb\Downloads\Qantum study\qai_platform_"
set "PATCHZIP=%USERPROFILE%\Downloads\3alimnIA_V6.16.5_UI_STABILITY_DESIGN_SYSTEM_PATCH.zip"
set "PATCHDIR=%TEMP%\3alimnIA_V6165_PATCH"

cd /d "%PROJECT%"
git status
git switch main
git pull origin main
git switch -c feat/v6-16-5-ui-stability

if exist "%PATCHDIR%" rmdir /s /q "%PATCHDIR%"
mkdir "%PATCHDIR%"
tar -xf "%PATCHZIP%" -C "%PATCHDIR%"
xcopy "%PATCHDIR%\*" "%PROJECT%\" /E /I /Y /H

cd /d "%PROJECT%"
```

ثم الاختبارات والرفع:

```cmd
py -3 validate_v6165_ui_stability_design_system.py
py -3 validate_v6164_research_export_analytics.py
py -3 validate_v61631_frontend_runtime_hotfix.py
py -3 -m compileall .

git add ui_stability.py teacher_studio.py ui_v6.py main_app.py
git add .streamlit\v6_theme.css
git add validate_v6165_ui_stability_design_system.py
git add V6_16_5_UI_STABILITY_DESIGN_SYSTEM_AR.md
git add README.md CHANGELOG.md

git status
git diff --cached --stat

git commit -m "fix: add V6.16.5 UI stability and shared design system"
git push -u origin feat/v6-16-5-ui-stability
```

## 9. اختبار Streamlit بعد الدمج

اختبر بالترتيب:

1. الصفحة العامة وشريط التنقل.
2. تسجيل دخول الأستاذ.
3. شبكة المشاريع.
4. رحلة إنشاء المقرر.
5. خريطة مراحل الإنتاج.
6. رسالة خطأ تجريبية أو فشل مزود.
7. العربية والفرنسية والإنجليزية.
8. عرض مكتبي وعرض هاتف.

## 10. حدود الإصدار

- لا يضيف RQ أو Redis.
- لا يشغّل المراحل 04–09 في الخلفية.
- لا يغيّر قاعدة البيانات.
- لا يغيّر مخرجات النماذج.

المرحلة التالية بعد اجتياز الاختبار الحي هي V6.17: خط الإنتاج الخلفي الهجين.
