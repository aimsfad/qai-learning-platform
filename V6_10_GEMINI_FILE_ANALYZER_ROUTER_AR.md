# 3alimnIA V6.10 — محلل Gemini للملفات وموجّه النماذج

## الهدف

تفعيل مفتاح Gemini الموجود في Streamlit Secrets فعليًا داخل فضاء الأستاذ، مع إبقاء Groq محركًا نصيًا أساسيًا وإضافة انتقال تلقائي آمن إلى مزود بديل عند فشل المزود الأول.

## ما أُضيف

### 1. محلل ملفات متعدد الوسائط

أضيف الملف `gemini_file_analyzer.py` ليحلل:

- PDF، بما في ذلك الصفحات المصورة والجداول والرسوم.
- PNG وJPG وJPEG وWEBP.
- MP3 وWAV وM4A.
- MP4 وMOV.
- DOCX وTXT وMD وCSV وJSON عبر استخراج محلي، مع إثراء Gemini عند تفعيله.

ينتج التحليل:

- المفاهيم والأهداف والكفاءات.
- الأنشطة وأساليب التدريس والتقييم الموجودة في المصدر.
- وصف الجداول والرسوم والصور.
- التنبيهات العلمية والمعلومات الناقصة.
- توصيات استعمال المصدر داخل الوحدة.
- إشارات إلى الصفحات أو الأقسام أو الأزمنة عندما تكون ظاهرة فعلًا.

لا يدّعي النظام قراءة جزء غير واضح، ولا يختلق رقم صفحة أو مرجعًا.

### 2. استخراج محلي احتياطي

عند غياب Gemini أو فشل الطلب:

- يستخرج PDF النصي محليًا بواسطة `pypdf`.
- يستخرج DOCX مع الفقرات والجداول بواسطة `python-docx`.
- تُقرأ الملفات النصية مباشرة.
- تظهر ملاحظة واضحة عندما يكون الملف غير قابل للتحليل محليًا.

### 3. موجّه النماذج

أضيف `model_router.py` ليختار المزود حسب المهمة:

- المدرّب السريع: Groq أو المزود المحدد في `LLM_PROVIDER`.
- إنتاج محتوى الأستاذ: `CONTENT_LLM_PROVIDER`.
- تحليل الملفات: `FILE_ANALYSIS_PROVIDER`، ويكون Gemini افتراضيًا.

عند تفعيل `ENABLE_MODEL_FALLBACK` ينتقل إنتاج المحتوى بين المزودين المهيئين دون كشف المفاتيح.

### 4. النماذج الافتراضية

- المهام السريعة: `openai/gpt-oss-20b` عبر Groq.
- إنتاج المحتوى العميق: `openai/gpt-oss-120b` عبر Groq.
- تحليل الملفات: `gemini-3.6-flash`.

إذا بقي اسم قديم في Secrets، يحوله الكود أثناء التشغيل:

- `llama-3.1-8b-instant` ← `openai/gpt-oss-20b`
- `llama-3.3-70b-versatile` ← `openai/gpt-oss-120b`
- `gemini-2.0-flash` ← `gemini-3.6-flash`

## إعداد Secrets المقترح

```toml
LLM_PROVIDER = "groq"
GROQ_MODEL = "openai/gpt-oss-20b"
CONTENT_LLM_PROVIDER = "groq"
CONTENT_GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_API_KEY = "..."

FILE_ANALYSIS_PROVIDER = "gemini"
GEMINI_API_KEY = "..."
GEMINI_MODEL = "gemini-3.6-flash"
FILE_ANALYSIS_GEMINI_MODEL = "gemini-3.6-flash"

ENABLE_MODEL_FALLBACK = "true"
```

## ما لم يُفعّل بعد

- مفتاح Cohere يُكتشف، لكن وحدة RAG والفهرسة الدلالية لم تُضف في هذا الإصدار.
- إعداد Cloudflare يُكتشف، لكن Workers AI ليس ضمن مسار التوليد الحالي.
- إنشاء الصور والفيديوهات الفعلية غير مضاف؛ تنتج المراحل الحالية المواصفات والسيناريوهات والبرومبتات.

## التحقق

```bash
python validate_v610_gemini_router.py
```
