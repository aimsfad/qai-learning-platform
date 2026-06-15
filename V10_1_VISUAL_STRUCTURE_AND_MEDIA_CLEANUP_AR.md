# V10.1 — Visual Structure and Media Cleanup

## الهدف
إعادة تنظيم صفحة الدرس بصرياً بحيث تصبح رحلة التعلم أوضح: خريطة تعلم، مختبر بصري، ربط بالكود، تحقق، ثم AI coach.

## ما تم تغييره
- إزالة الصور والفيديوهات القديمة من مسار الطالب الافتراضي لأنها كانت مكررة وباهتة وتضعف تركيز الدرس.
- تبويب `Visual lab` أصبح يعرض المحاكي كعنصر أساسي وحيد، ثم Code bridge ثم Learning checkpoints.
- إعادة بناء محاكي Hadamard ليكون مضغوطاً، إنجليزياً، وذاتي الاكتفاء بالألوان والخطوط داخل iframe.
- إصلاح مشكلة الاعتماد على CSS خارجي داخل المحاكي.
- تقليل الحاجة إلى السكرول أثناء التنقل بين خطوات المحاكي.
- تبويب `Learning map` أصبح يعرض مبادئ منظمة: Visual first, One change at a time, Code bridge, AI after attempt.

## ملاحظات تصميمية
تم الاستناد إلى مبادئ مستخلصة من منصات تعليمية مشابهة:
- IBM Quantum: visualizations, circuits, histograms, classroom modules.
- Microsoft Quantum Katas: interaction, task progression, feedback.
- Qiskit educational materials: circuit-state-measurement-output sequence.

## اختبار
تم تنفيذ:
python3 -m py_compile app.py main_app.py media_utils.py content.py db.py feedback_engine.py security.py

## ما لم يتم بعد
- لم يتم توليد micro-animations MP4 جديدة بعد. هذه ستكون مرحلة V10.2 بعد تثبيت التنظيم البصري.
