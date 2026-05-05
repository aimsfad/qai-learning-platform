# قائمة التحضير قبل رفع المنصة إلى GitHub وStreamlit Cloud

## 1. قاعدة البيانات

محليًا يمكن تشغيل المنصة بـ SQLite تلقائيًا. عند النشر السحابي يجب استعمال PostgreSQL خارجي مثل Neon أو Supabase.

في Streamlit Cloud Secrets أضيفي:

```toml
DATABASE_URL = "postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require"
```

إذا لم تضعي `DATABASE_URL` ستستعمل المنصة SQLite محليًا، وهذا غير مناسب لتجربة حقيقية عن بعد لأن ملفات الخادم قد تختفي عند إعادة النشر.

## 2. أسرار التطبيق

لا ترفعي `.streamlit/secrets.toml` إلى GitHub. ارفعي فقط `.streamlit/secrets_example.toml`.

ضعي الأسرار الحقيقية في Streamlit Cloud من:

`App settings -> Secrets`

مثال:

```toml
EVALUATOR_USERNAME = "evaluator"
ADMIN_PASSWORD = "ضع_كلمة_مرور_قوية"
REGISTRATION_ACCESS_CODE = "qai-study-2026"
LLM_PROVIDER = "groq"
GROQ_API_KEY = "ضع_مفتاح_Groq"
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DATABASE_URL = "postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require"
```

## 3. ما أضيف في هذه النسخة

- جدول `question_responses` لحفظ إجابة كل سؤال على حدة، وهذا مهم لتحليل المفاهيم.
- جدول `consent_records` لحفظ تأكيد موافقة الطالب على تسجيل البيانات.
- جدول `events_log` لتتبع تسجيل الدخول والخروج، تسليم الاختبارات، إكمال الدروس، وتسليم الاستبيان.
- صفحة `Paper-ready Analysis` في حساب المقيم لاستخراج مؤشرات المقال مباشرة.
- صفحة `Event Logs` في حساب المقيم.
- تصدير Excel موسع يشمل: الطلاب، الاختبارات، إجابات الأسئلة، المفاهيم، التأملات، تفاعلات LLM، الاستبيانات، الموافقات، وسجل الأحداث.

## 4. قبل مشاركة الرابط مع الطلبة

- تأكدي أن Groq يعمل وأن `Feedback Logs` تسجل `mode = llm` و `provider = groq`.
- غيّري كلمة مرور المقيم ولا تستعملي `admin123`.
- فعّلي `REGISTRATION_ACCESS_CODE` ولا ترسلي الرابط وحده دون رمز الدراسة.
- احذفي بيانات التجارب الوهمية.
- اختبري حساب طالب كامل: إنشاء حساب -> Pre-test -> Adaptive Plan -> Learning Module -> AI Tutor -> Post-test -> Survey.

## 5. ملفات لا ترفع إلى GitHub

```gitignore
.streamlit/secrets.toml
data/
.venv/
__pycache__/
*.pyc
.env
*.log
```
