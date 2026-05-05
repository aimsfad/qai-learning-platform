# تفعيل Groq في المنصة

1. افتحي Groq Console وأنشئي API key جديدًا.
2. لا ترسلي المفتاح في المحادثة ولا تضعيه في GitHub.
3. داخل مجلد المنصة أنشئي أو افتحي الملف:

```text
.streamlit/secrets.toml
```

4. ضعي القيم التالية:

```toml
EVALUATOR_USERNAME = "evaluator"
ADMIN_PASSWORD = "كلمة-مرور-قوية"
REGISTRATION_ACCESS_CODE = "qai-study-2026"

LLM_PROVIDER = "groq"
GROQ_API_KEY = "ضع-مفتاح-Groq-هنا"
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
```

5. أوقفي Streamlit ثم شغليه من جديد:

```bash
Ctrl + C
streamlit run app.py
```

6. للتأكد، ادخلي كمقيم إلى Evaluator Dashboard. يجب أن تظهر:

```text
provider = groq
available = true
groq_key_detected = true
```

7. بعد سؤال جديد في AI Tutor Lab، افتحي Feedback Logs. إذا ظهر `mode = llm` فهذا يعني أن Groq يعمل فعليًا. إذا ظهر `llm_error` افتحي عمود diagnostic لمعرفة السبب.
