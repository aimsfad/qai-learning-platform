# تحديث LLM Performance Evaluation

أضيفت هذه النسخة لتحويل المنصة من أداة تعليمية فقط إلى أداة بحثية تقيس أداء المعلّم الذكي نفسه داخل سياق تعليم البرمجة الكمية.

## الملفات التي تغيّرت

- `db.py`
- `feedback_engine.py`
- `app.py`

## أهم الإضافات

1. جدول جديد في قاعدة البيانات:
   - `llm_evaluations`

2. أعمدة إضافية في جدول `ai_interactions`:
   - `latency_ms`
   - `response_word_count`
   - `student_input_language`
   - `response_language`
   - `error_type`
   - `is_fallback_used`

3. صفحة جديدة في حساب المقيم:
   - `LLM Performance Evaluation`

4. مؤشرات جديدة في `Paper-ready Analysis`:
   - Mean conceptual accuracy
   - Mean answer relevance
   - Mean pedagogical clarity
   - Mean scaffolding quality
   - Mean Qiskit alignment
   - Mean reflection support
   - Mean personalization
   - LLM success/error/fallback rates
   - Mean response latency

5. تحديث Export:
   - `llm_evaluations`
   - `llm_evaluation_summary`

## Rubric التقييم

كل رد من LLM يمكن تقييمه من 1 إلى 5 حسب:

- Conceptual accuracy
- Answer relevance
- Pedagogical clarity
- Scaffolding quality
- Qiskit alignment
- Reflection support
- Personalization

ثم تحسب المنصة متوسطًا يسمى:

`LLM Pedagogical Quality Score`

## بعد رفع التحديث إلى GitHub

1. ادفعي الملفات الجديدة:

```bash
git add app.py db.py feedback_engine.py LLM_PERFORMANCE_UPDATE_AR.md
git commit -m "Add LLM performance evaluation module"
git push origin main
```

2. في Streamlit Cloud اضغطي:

`Reboot app`

3. عند التشغيل ستنشئ المنصة الجداول والأعمدة الجديدة تلقائيًا.

