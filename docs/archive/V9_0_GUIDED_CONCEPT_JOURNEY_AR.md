# V9.0 Guided Concept Journey + Professional Sequential Media

هذه النسخة تعالج مشكلة أن طريقة التعلم لم تكن واضحة للطالب، وأن الصور والفيديوهات كانت تبدو كمادة واحدة مزدحمة.

## ما تغير

- إعادة بناء طريقة عرض المفهوم داخل الدرس حول تسلسل واضح:
  1. Observe: ما الظاهرة؟
  2. Model: كيف تمثلها الدارة؟
  3. Code: أين تظهر في Qiskit؟
  4. Interpret: كيف نفسر النتيجة؟

- استبدال فكرة الصورة الواحدة المزدحمة بوسائط متسلسلة:
  - أربع صور لكل درس، كل صورة لها وظيفة واحدة فقط.
  - فيديو قصير لكل درس مبني من نفس التسلسل.
  - لا توجد أزرار مزيفة داخل الصور.
  - الشرح التفصيلي يبقى في صفحة الدرس وليس داخل الصورة.

- تطوير استعمال الذكاء التوليدي:
  - الطالب يختار الخطوة التي يعمل عليها.
  - الطالب يكتب محاولة أولًا.
  - المساعد يعطي سؤالًا سقراطيًا، تلميحًا، فحصًا للتفسير، شرحًا محدودًا للخطوة، أو تمرينًا صغيرًا.
  - الهدف هو دعم التفكير وليس تقديم الحل مباشرة.

## الملفات الجديدة

- `assets/lesson_media/sequence/*_01_observe.png`
- `assets/lesson_media/sequence/*_02_model.png`
- `assets/lesson_media/sequence/*_03_code.png`
- `assets/lesson_media/sequence/*_04_interpret.png`
- `assets/lesson_media/sequence/*_concept_sequence.mp4`

## الملفات التي لم تتغير وظيفيًا

- `db.py`
- `security.py`
- `feedback_engine.py`
- `content.py`

## اختبار سريع بعد النشر

1. Student workspace
2. Sign in
3. Learning Path
4. افتح Module 1 أو Module 2 أو Module 3
5. جرّب:
   - Guided concept journey
   - Sequential media
   - GenAI learning coach
