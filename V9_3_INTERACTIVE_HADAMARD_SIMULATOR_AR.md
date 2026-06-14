# v9.3 Interactive Hadamard Simulator

تم دمج مثال Claude التفاعلي داخل المنصة بصورة آمنة.

## ما تم
- إضافة ملف HTML تفاعلي مستقل في `assets/interactive/hadamard_superposition_simulator.html`.
- جعله self-contained بإضافة CSS variables داخل iframe.
- تضمينه داخل درس `Hadamard and superposition` عبر `st.components.v1.html`.
- إضافة فيديو `Qai.mp4` كمادة عرض احترافية لدرس Hadamard.
- عدم تغيير قاعدة البيانات أو ملفات الأمان أو محرك الذكاء الاصطناعي.

## أين يظهر؟
Student workspace → Learning Path → Module 3 → Sequential media

## لماذا هو مهم تربوياً؟
يسمح للطالب بالتنقل بين ثلاث مراحل: الحالة الابتدائية، تطبيق Hadamard، ثم القياس والعدّ. كما يسمح بتغيير عدد shots ورؤية أثر ذلك على histogram.
