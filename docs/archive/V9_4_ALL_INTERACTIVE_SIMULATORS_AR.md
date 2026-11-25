# v9.4 — All Interactive Lesson Simulators + Completion Logging

هذه النسخة تدمج المحاكيات التفاعلية الستة داخل الدروس كلها، وليس درس Hadamard فقط.

## ما تغير

- إضافة مجلد:
  `assets/lesson_media/interactive/`
- إضافة 6 محاكيات HTML/SVG/JS ذاتية الاكتفاء:
  - `orientation_simulator.html`
  - `qubit_measurement_simulator.html`
  - `hadamard_superposition_simulator.html`
  - `shots_counts_simulator.html`
  - `cnot_correlation_simulator.html`
  - `qiskit_debugging_simulator.html`
- تحديث `media_utils.py` بدالة `render_simulator()`.
- جعل المحاكي التفاعلي هو العرض الأساسي داخل تبويب Sequential media.
- نقل الصور والفيديوهات القديمة إلى expander اختياري.
- إضافة self-report checkbox لتسجيل أن الطالب أكمل خطوات المحاكي.
- إضافة event بحثي جديد:
  `simulator_completed`
- تحويل event العرض إلى:
  `view_interactive_simulator`

## ملاحظات بحثية

التسجيل الحالي يعتمد على self-report لأن محاكيات HTML تعمل داخل iframe ولا ترسل أحداثًا مباشرة إلى Streamlit. هذا حل آمن وسريع لنسخة البحث الحالية. التتبع الآلي الكامل يحتاج لاحقًا custom Streamlit component أو streamlit-javascript.

## الاختبار

بعد النشر، اختبري كل درس من Learning Path وتأكدي من:

- ظهور المحاكي بدون warning.
- عمل أزرار الخطوات.
- عمل AR/EN في الدروس 1-5.
- عمل sliders في الدروس 2-5.
- تسجيل checkbox عند إكمال المحاكي.
