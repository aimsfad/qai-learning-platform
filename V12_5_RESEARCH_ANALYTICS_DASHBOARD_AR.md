# V12.5 — Research Analytics Dashboard

## الهدف
تحويل سجلات المنصة الخام إلى مؤشرات بحثية قابلة للعرض والتصدير.

## ما أضيف
- لوحة جديدة داخل صفحة AI Metrics بعنوان V12.5 research interaction dashboard.
- مؤشرات إجمالية: أحداث Concept Builder، إكمال المحاكيات، إجابات Quick Check، ومتوسط الوقت قبل طلب AI.
- تبويبات تحليلية:
  - Concept Builder: الطلبات حسب نوع الإجراء والدرس.
  - Simulator journey: مشاهدة الفيديو، فتح المحاكي، إكمال المحاكي، وإجابات الفهم.
  - AI timing: متوسط ووسيط الثواني قبل طلب AI حسب المصدر والمهمة.
  - Student summary: ملخص رحلة كل طالب.
- أزرار تحميل CSV لكل جدول مشتق.
- إدراج الجداول المشتقة ضمن Excel export.

## لماذا مهم بحثياً
هذه النسخة تجعل بيانات مثل `concept_builder_request`, `simulator_completed`, `check_answered`, و `ai_request_timing` قابلة للتحليل مباشرة بدل أن تبقى مدفونة داخل events_log.
