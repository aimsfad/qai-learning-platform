# 3alimnIA (علّمنيا) — V7.2 Liquid Glass Edition

منصة تعليمية وبحثية متكاملة مدعومة بالذكاء الاصطناعي التربوي ومحرك Hybrid RAG على Neon/pgvector، بواجهة **Liquid Glass** متجاوبة مع الهاتف والتابلت والحاسوب.

## ما يتضمنه الإصدار V7.2
- **واجهة Liquid Glass V7.2 متجاوبة بالكامل:** سطوح زجاجية شفافة متعددة الطبقات مع الحفاظ الكامل على تخطيط البطاقات وخط أيقونات `Material Symbols Rounded`، ودعم الحاسوب والتابلت والهاتف والوضع الداكن.
- **التصليحات الحرجة العشرة:** تأمين التغليف (`package_release.py`)، بوابة الأمان (`validate_release_security.py`)، فك ارتباط `db.py` عن `streamlit`، تحصين SQL في محرك RAG، توحيد `requirements.txt` على `psycopg[binary]`، طبقة تعقيم HTML (`safe_html.py`)، وتنظيف المستودع.

## التشغيل والتحقق
```bash
pip install -r requirements-dev.txt
python validate_current_release.py
streamlit run app.py
```
