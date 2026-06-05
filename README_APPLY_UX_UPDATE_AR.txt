حزمة تحديث UX آمنة للمنصة

الملف الأساسي الذي يجب استبداله الآن:
- app.py

اختياري فقط إذا لم تطبقي حزمة حماية بيانات pilot السابقة:
- db.py
- .gitignore

هذا التحديث لا يغير قاعدة Neon ولا يحذف أي بيانات. هو فقط يحسن الواجهة:
- توضيح Student/Evaluator في الصفحة الرئيسية.
- شرح سلم 0-3 عند إنشاء الحساب.
- تنظيم الخطة التعليمية.
- تمييز أجزاء Explanation / Interactive Activity / AI Tutor / Reflection.

خطوات الرفع:
git status
git add app.py
git commit -m "Improve onboarding and student UX based on pilot feedback"
git push origin main

ثم من Streamlit Cloud:
Reboot app
