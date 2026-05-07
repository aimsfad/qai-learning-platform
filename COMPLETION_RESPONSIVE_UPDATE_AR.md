# تحديث v4.0: جاهزية التجربة، حالة الإكمال، وتحسين الواجهة

أضيفت في هذه النسخة تعديلات قبل مشاركة رابط المنصة مع الطلبة:

## 1. Research Notice / Consent
- صفحة مستقلة للطالب باسم `Research Notice`.
- الحسابات الجديدة تؤكد إشعار الدراسة أثناء التسجيل.
- الحسابات القديمة التي لا تحتوي على consent تُطلب منها الموافقة قبل متابعة المسار.

## 2. Participant Code
- بعد إنشاء الحساب، تعرض المنصة كود المشارك بوضوح وتطلب من الطالب حفظه قبل الانتقال إلى الاختبار القبلي.

## 3. Completion Requirements
- إضافة حالة إكمال واضحة للطالب والمقيم.
- المشاركة تصبح `complete case` فقط إذا اكتملت الشروط التالية:
  - consent
  - pre-test
  - at least one lesson activity
  - at least one AI Tutor interaction
  - post-test
  - survey

## 4. Mandatory AI Tutor Interaction
- لا يستطيع الطالب الوصول إلى post-test قبل تسجيل تفاعل واحد على الأقل مع AI Tutor.
- هذا ضروري لأن الدراسة تقيّم التعلم المدعوم بالذكاء التوليدي.

## 5. Evaluator Analytics
- إضافة أعمدة `is_complete_case` و `complete_case_missing` في Progress Monitor و Paper-ready Analysis.
- تظهر complete cases في لوحة المقيم.

## 6. Responsive / Compact UI
- تحسين CSS حتى تكون الواجهة أوضح على الهاتف والحاسوب.
- تصغير أزرار القائمة الجانبية لتظهر اختيارات أكثر دون تمرير طويل.
- تقليل الهوامش وحجم hero cards على الشاشات الصغيرة.

## الملفات المعدلة
- `app.py`
- `db.py`

## بعد الرفع إلى GitHub
نفّذي:

```bash
git add app.py db.py COMPLETION_RESPONSIVE_UPDATE_AR.md
git commit -m "Add consent, completion status, mandatory AI tutor, and responsive UI"
git push origin main
```

ثم في Streamlit Cloud:

```text
Manage app -> Reboot app
```
