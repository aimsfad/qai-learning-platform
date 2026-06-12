# تحديث v6: إعادة تصميم الواجهة والمواد التعليمية

## الفكرة العامة
هذا التحديث يعيد بناء تجربة الطالب والمقيّم بطريقة أكثر احترافية:

- لوحة طالب أوضح مع مؤشرات تقدم مختصرة.
- Learning Path من 6 وحدات كبطاقات تعليمية واضحة.
- كل وحدة تحتوي على: هدف، big idea، شرح مبسط، مثال Qiskit، رسم تعليمي احترافي، mini task، سؤال تحقق، ودعم AI داخل الوحدة.
- استبدال الصور العامة بصور تفسيرية مخصصة للمنصة.
- تقوية لوحة المقيّم بملخصات، completion funnel، AI usage، وlearning observer.

## مصادر التصميم التي ألهمت التحديث
- IBM Quantum Learning: تنظيم التعلم في courses/modules ودعم classroom-oriented learning.
- Qiskit visualization documentation: استعمال circuit/state/counts visualizations بدلاً من صور زخرفية عامة.
- Microsoft Quantum Katas: التركيز على التمارين التفاعلية والممارسة.
- Khanmigo: دعم AI داخل صفحات المحتوى نفسها.
- Duolingo: progress indicator واضح وبسيط.
- Brilliant: مفهوم visual and interactive sessions.

## التغييرات التقنية
- `app.py`: CSS احترافي، Student Dashboard جديد، Learning Path جديد، Module view جديد، Evaluator Dashboard محسن.
- `content.py`: إعادة كتابة محتوى الوحدات الستة ببنية تعليمية غنية.
- `assets/lesson_media`: ست صور تعليمية جديدة عالية الدقة.

## ملاحظة
هذا التحديث لا يغير قواعد البيانات الأساسية أو نظام تسجيل الدخول، لذلك هو أقل خطورة من إعادة بناء كاملة للباك اند.
