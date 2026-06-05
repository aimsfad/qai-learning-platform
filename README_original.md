# Quantum AI Learning Evaluation Platform

A Streamlit platform for a one-group pilot study on AI-supported introductory quantum programming learning with Qiskit.

## Study flow

Student flow:

1. Create account or sign in
2. Pre-test
3. Adaptive learning plan based on pre-test weaknesses
4. Scaffolded Qiskit learning module
5. AI Tutor Lab: explanation, feedback, exercise generation, Qiskit interpretation
6. Post-test
7. Usability questionnaire and open-ended feedback

Evaluator flow:

- Protected sign in
- Student list and account creation
- Progress monitor
- Learning analytics
- AI feedback logs with mode/provider/model/diagnostics
- Survey results
- Excel export

## Local installation

```bash
cd qai_platform_final
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
```

Create local secrets:

```bash
mkdir .streamlit
copy .streamlit\secrets_example.toml .streamlit\secrets.toml
```

On macOS/Linux:

```bash
mkdir -p .streamlit
cp .streamlit/secrets_example.toml .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and set. For Groq:

```toml
EVALUATOR_USERNAME = "evaluator"
ADMIN_PASSWORD = "a-strong-password"
REGISTRATION_ACCESS_CODE = "qai-study-2026"

LLM_PROVIDER = "groq"
GROQ_API_KEY = "your-new-groq-key"
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
```

Gemini and OpenAI alternatives are also shown in `.streamlit/secrets_example.toml`.

Run:

```bash
streamlit run app.py
```

## Important security notes

- Do not share API keys in screenshots or chat.
- Do not commit `.streamlit/secrets.toml` to GitHub.
- Change `ADMIN_PASSWORD` before cloud deployment.
- Keep `REGISTRATION_ACCESS_CODE` enabled if the link will be public.
- For Streamlit Cloud, use a persistent PostgreSQL database via `DATABASE_URL`; SQLite files may not persist reliably across app restarts.

## LLM modes

The platform logs each AI interaction as:

- `llm`: external LLM response succeeded.
- `llm_error`: an LLM key was found but the provider returned an error; a local fallback was shown.
- `rule_based`: no external provider was configured; local fallback was used.

For the paper, report the actual provider/model used during the experiment. If Groq is used, the evaluator dashboard and feedback logs will show `provider = groq`, the configured model, and `mode = llm` when generation succeeds.

## Cloud deployment overview

1. Push this folder to a private GitHub repository.
2. Create a Streamlit Community Cloud app from the repository.
3. Add all secrets in **App settings > Secrets**.
4. Use an external PostgreSQL database and set `DATABASE_URL`.
5. Test with a fake student before sharing the link with participants.

## Export

Evaluator workspace > Results Export downloads an Excel workbook containing:

- students
- progress_summary
- test_attempts
- concept_scores
- lesson_reflections
- ai_interactions
- surveys
