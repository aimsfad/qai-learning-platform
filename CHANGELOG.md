# Changelog

## V4.0 - Premium UI & Typography Refresh
- Rebuilt the public landing page with the approved official logo rendered reliably through Streamlit.
- Added Alexandria/Tajawal typography for Arabic and Inter for French/English.
- Added premium RTL/LTR-aware visual hierarchy, responsive layout, cards, forms, tabs, metrics, and evaluator surfaces.
- Added `.streamlit/v4_theme.css`, Streamlit theme configuration, and `.gitattributes`.
- Added `validate_v4_ui.py` and multilingual static previews.
- Preserved all learning, research, database, AI, LPQS, and export behavior.

## V3.1 - Streamlit Cloud display fix

- Fixed raw HTML appearing inside the landing hero.
- Replaced the fragile embedded PNG logo with a self-contained inline SVG lockup.
- Removed the duplicate landing-page language selector.
- Replaced the narrow horizontal radio control with a sidebar-friendly language selectbox.

# سجل تعديلات 3alimnIA

## V3 - التدويل الكامل للمنصة

### اختيار اللغة

- إضافة اختيار عالمي للعربية والفرنسية والإنجليزية.
- تطبيق الاختيار على الصفحة العامة، حساب المتعلم، جميع صفحات الدراسة، والتقييم البحثي.
- إعادة تحميل الواجهة فور تغيير اللغة لتطبيق RTL/LTR بصورة صحيحة.
- حفظ `preferred_language` داخل حساب المتعلم واستعادتها عند تسجيل الدخول.

### المحتوى والتعلمات

- ترجمة الوحدات الست كاملة: الأهداف، المفاهيم، الشرح، الأهمية، الفكرة الكبرى، خطوات التصور، جسر Qiskit، سوء الفهم، المهمة، التحقق، التأمل، ومعايير الإنجاز.
- ترجمة المخططات النصية وتسلسل Observe/Model/Code/Interpret.
- ترجمة الوسائط التعليمية وتعليمات المحاكيات.
- ترجمة 36 سؤال تقييم مع الخيارات والتغذية الراجعة.
- ترجمة الاستبيان والأسئلة المفتوحة.

### الذكاء التوليدي

- مزامنة اللغة المختارة مع AI Coach وAI Tutor والخطة التكيفية.
- إضافة الفرنسية إلى Concept Builder.
- تحسين كشف لغة سؤال المتعلم ليشمل الفرنسية.
- توطين بطاقات Concept Builder والرسائل البريدية لإعادة تعيين كلمة المرور.

### سلامة البحث

- الإبقاء على مفاتيح المفاهيم والوحدات والأسئلة بالإنجليزية داخليًا.
- عدم تغيير بنية السجلات البحثية الحالية.
- إضافة ترحيل تلقائي لحقل `preferred_language` للحسابات الموجودة.

### التحقق

- اجتازت جميع ملفات Python فحص `py_compile`.
- اجتاز فحص المحتوى: 6 وحدات و18 سؤالًا قبليًا و18 سؤالًا بعديًا لكل لغة.
- اجتاز اختبار SQLite لإنشاء الحساب وحفظ اللغة وتغييرها واستعادتها عند المصادقة.

## V3.2 - Official logo restoration
- Restored the approved blue/cyan/gold horizontal 3alimnIA logo.
- Embedded the logo as a base64 data URI to prevent broken paths on Streamlit Cloud.
- Removed the replacement SVG wordmark from the visible interface.
- Added responsive sizing for hero and sidebar use.
