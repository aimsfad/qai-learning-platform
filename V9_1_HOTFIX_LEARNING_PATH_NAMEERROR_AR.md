# V9.1 Hotfix: Learning Path NameError

## المشكلة
ظهرت رسالة خطأ في Streamlit Cloud عند فتح Learning Path بعد تحديث v9.0:

`NameError` داخل `render_learning_module` بسبب استدعاء الدالة:

`render_learning_path_cards(...)`

بينما لم تكن الدالة موجودة في `main_app.py` بعد إضافة Guided Concept Journey.

## الإصلاح
- أُعيدت دالة `render_learning_path_cards` داخل `main_app.py`.
- الدالة تعرض بطاقات الدروس الستة وتسمح باختيار الدرس الحالي.
- لم يتم تعديل قاعدة البيانات أو التسجيل أو AI Tutor أو الاختبارات.
- تم التحقق من الكود باستخدام `py_compile`.

## الاختبار المطلوب
بعد النشر وإعادة التشغيل:

1. تسجيل الدخول كطالب.
2. فتح Learning Path.
3. تجربة فتح Module 1 و Module 2 و Module 3.
4. التأكد من ظهور تبويبات Guided Concept Journey و Sequential media و GenAI learning coach.
