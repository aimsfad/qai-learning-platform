# 3alimnIA V6.18.1 — Blueprint API Contract Hotfix

## المشكلة

كان `lesson_blueprint_engine.py` يستعمل أسماء قديمة لمعاملات ودوال طبقة قاعدة البيانات:

- `revision_number` بدل `version_number`
- `edit_source` بدل `revision_type`
- `db.log_teacher_blueprint_change` بدل `db.record_teacher_blueprint_audit`
- قراءة `revision_number` عند الاستعادة بدل `version_number`

أدى ذلك إلى توقف إنشاء مخطط المقرر برسالة:

```text
save_teacher_blueprint_bundle() got an unexpected keyword argument 'revision_number'
```

## الإصلاح

تمت مواءمة محرك المخطط مع العقد الفعلي في `db.py`، مع تحديث توليد المخطط، الحفظ اليدوي، سجل التدقيق، واستعادة الإصدارات.

## الاختبار

```cmd
py -3 validate_v6181_blueprint_api_contract.py
py -3 -m py_compile lesson_blueprint_engine.py db.py
```

النتيجة المتوقعة:

```text
V6.18.1 blueprint API contract validation passed.
```

لا يغيّر هذا التحديث مخطط قاعدة البيانات ولا يحتاج إلى Secrets جديدة.
