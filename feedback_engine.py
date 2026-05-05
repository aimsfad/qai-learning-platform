"""LLM provider integration and local fallback for the QAI platform."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import requests
import streamlit as st


@dataclass
class TutorResult:
    response: str
    mode: str  # llm, llm_error, rule_based
    provider: str
    model: str
    diagnostic: str = ""


def _secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def provider_status() -> Dict[str, Any]:
    configured_provider = _secret("LLM_PROVIDER", "").lower().strip()
    gemini_key = bool(_secret("GEMINI_API_KEY", "").strip())
    openai_key = bool(_secret("OPENAI_API_KEY", "").strip())
    groq_key = bool(_secret("GROQ_API_KEY", "").strip())

    # If LLM_PROVIDER is missing or set to local, auto-detect a configured key.
    # This helps avoid silent local fallback when the secrets file contains a key
    # but the provider field was forgotten. Prefer Groq for this package.
    if configured_provider in ("", "local", "none", "fallback"):
        if groq_key:
            provider = "groq"
        elif gemini_key:
            provider = "gemini"
        elif openai_key:
            provider = "openai"
        else:
            provider = "local"
    else:
        provider = configured_provider

    if provider == "gemini":
        available = gemini_key
        model = _secret("GEMINI_MODEL", "gemini-2.0-flash")
    elif provider == "openai":
        available = openai_key
        model = _secret("OPENAI_MODEL", "gpt-4o-mini")
    elif provider == "groq":
        available = groq_key
        model = _secret("GROQ_MODEL", "llama-3.1-8b-instant")
    else:
        available = False
        model = "local-fallback"

    return {
        "provider": provider,
        "configured_provider": configured_provider or "auto",
        "available": available,
        "gemini_key_detected": gemini_key,
        "openai_key_detected": openai_key,
        "groq_key_detected": groq_key,
        "model": model,
    }


def _contains_arabic(text: str) -> bool:
    return any("\u0600" <= ch <= "\u06FF" or "\u0750" <= ch <= "\u077F" or "\u08A0" <= ch <= "\u08FF" for ch in text or "")


def _normalize_language(value: str) -> str:
    value = (value or "").strip().lower()
    if value in {"arabic", "العربية", "ar"}:
        return "Arabic"
    if value in {"french", "français", "francais", "fr"}:
        return "French"
    if value in {"english", "en"}:
        return "English"
    return "Auto-detect"


def resolve_response_language(
    student_input: str = "",
    student_profile: Optional[Dict[str, Any]] = None,
    lesson_context: Optional[Dict[str, Any]] = None,
) -> str:
    # Highest priority: explicit UI language selection passed in lesson_context.
    ctx_lang = _normalize_language(str((lesson_context or {}).get("response_language", "")))
    if ctx_lang != "Auto-detect":
        return ctx_lang
    # Second priority: learner profile preference, if later added to the database/UI.
    prof_lang = _normalize_language(str((student_profile or {}).get("preferred_language", "")))
    if prof_lang != "Auto-detect":
        return prof_lang
    # Auto-detect from the student's free text.
    if _contains_arabic(student_input):
        return "Arabic"
    return "English"


def system_prompt(response_language: str = "English") -> str:
    language_rule = (
        f"Respond in {response_language}. Respect the learner's requested language. "
        "If the learner asks in Arabic, answer in clear Modern Standard Arabic while keeping technical terms such as qubit, gate, measurement, counts, and Qiskit when useful. "
        "Do not switch back to English unless the learner requests it."
    )
    return (
        "You are an educational AI tutor for an introductory quantum programming pilot study. "
        "The learner is a computer science student using Qiskit. Use concise, accurate explanations. "
        "Support conceptual scaffolding, guided Qiskit examples, formative feedback, exercise generation, "
        "and reflection. Do not encourage copying generated answers. When solving, first provide hints, "
        "questions, and partial reasoning. Encourage the learner to explain the circuit before giving a final answer. "
        "When giving code, keep it minimal and Qiskit-oriented. Avoid unsupported claims about real hardware. "
        + language_rule
    )


def build_prompt(
    task: str,
    concept: str,
    student_input: str,
    student_profile: Optional[Dict[str, Any]] = None,
    lesson_context: Optional[Dict[str, Any]] = None,
) -> str:
    profile_json = json.dumps(student_profile or {}, ensure_ascii=False, indent=2)
    lesson_json = json.dumps(lesson_context or {}, ensure_ascii=False, indent=2)
    response_language = resolve_response_language(student_input, student_profile, lesson_context)
    language_extra = ""
    if response_language == "Arabic":
        language_extra = "اكتب الرد بالعربية الفصحى المبسطة. حافظ على المصطلحات التقنية الأساسية عند الحاجة مثل qubit و gate و measurement و Qiskit. لا تقدم الحل النهائي مباشرة؛ ابدأ بتلميحات وأسئلة موجهة."
    elif response_language == "French":
        language_extra = "Réponds en français clair et pédagogique. Garde les termes techniques essentiels si nécessaire. Commence par des indices et un raisonnement guidé avant la réponse complète."
    return f"""
Task: {task}
Concept focus: {concept}
Response language: {response_language}
{language_extra}

Student profile and progress:
{profile_json}

Relevant lesson context:
{lesson_json}

Student input:
{student_input or '[No free text provided]'}

Response requirements:
- Keep the explanation suitable for an introductory learner.
- Use scaffolding: concept -> circuit structure -> measurement interpretation.
- If the task asks for feedback, identify strengths and one or two precise improvements.
- If the task asks for exercise generation, generate one short exercise and one reflective question; do not provide the full solution immediately.
- Include a Qiskit snippet only if it helps.
- End with a reflective prompt that requires the learner to write something in their own words.
- Strictly use the requested response language above.
""".strip()


def local_fallback(task: str, concept: str, student_input: str = "", response_language: str = "English") -> str:
    task_lower = task.lower()
    if response_language == "Arabic" or _contains_arabic(student_input):
        base = (
            f"محور المفهوم: {concept}\n\n"
            "طريقة مفيدة للتفكير في هذا الموضوع هي تحليل الدارة على أربع خطوات:\n"
            "1. حدّد عدد الـ qubits والـ classical bits؛\n"
            "2. حدّد البوابة أو العملية المطبقة؛\n"
            "3. اشرح ماذا يتغير قبل القياس measurement؛\n"
            "4. فسّر المخرجات الكلاسيكية بعد القياس اعتمادًا على counts.\n\n"
        )
        if "exercise" in task_lower:
            return base + (
                "تمرين تدريبي: أنشئ دارة Qiskit صغيرة مرتبطة بهذا المفهوم، ثم اكتب ما تتوقعه قبل القياس، "
                "وبعدها اشرح كيف يجب أن تظهر نتائج counts بعد عدة shots.\n\n"
                "سؤال تأملي: أي جزء من الدارة يفسر توزيع المخرجات المتوقع؟"
            )
        if "check" in task_lower or "feedback" in task_lower:
            return base + (
                "تغذية راجعة: يجب أن يذكر شرحك بوضوح حالة النظام قبل القياس والنتيجة الكلاسيكية بعد القياس. "
                "إذا استعملت كود Qiskit، تأكد من عدد classical bits ومن تطابق indices في measurement.\n\n"
                "سؤال تأملي: أعد كتابة إجابتك مستعملًا المصطلحات: state و measurement و counts."
            )
        if "debug" in task_lower or "interpret" in task_lower:
            return base + (
                "تلميح للتصحيح: تأكد أن الدارة تحتوي عددًا كافيًا من classical bits، وأن البوابات تستعمل indices صحيحة، "
                "وأن measurement يربط كل qubit بالـ classical bit المناسب.\n\n"
                "مثال بسيط:\n```python\nfrom qiskit import QuantumCircuit\nqc = QuantumCircuit(1, 1)\nqc.measure(0, 0)\n```\n\n"
                "سؤال تأملي: أي index يمثل qubit وأي index يمثل classical bit؟"
            )
        return base + (
            "شرح موجه: اربط المفهوم بدارة Qiskit صغيرة. اسأل نفسك: ماذا تجهز الدارة؟ ماذا نقيس؟ "
            "وكيف نفسر counts الناتجة؟\n\n"
            "سؤال تأملي: اشرح هذا المفهوم بكلماتك قبل طلب الحل الكامل."
        )

    task_lower = task.lower()
    base = (
        f"Concept focus: {concept}\n\n"
        "A useful way to approach this topic is to inspect the circuit in four steps:\n"
        "1. identify the qubits and classical bits;\n"
        "2. identify the gate or operation being applied;\n"
        "3. explain what changes before measurement;\n"
        "4. interpret the classical output after measurement.\n\n"
    )
    if "exercise" in task_lower:
        return base + (
            "Practice exercise: Build a small Qiskit circuit related to this concept, write what you expect before measurement, "
            "then describe what the measurement counts should show after repeated shots.\n\n"
            "Reflective prompt: What part of the circuit explains the expected output distribution?"
        )
    if "check" in task_lower or "feedback" in task_lower:
        return base + (
            "Formative feedback: Your explanation should explicitly mention the state before measurement and the classical result after measurement. "
            "If you used Qiskit code, verify the number of classical bits and the measurement indices.\n\n"
            "Reflective prompt: Rewrite your answer using the terms state, measurement, and counts where appropriate."
        )
    if "debug" in task_lower or "interpret" in task_lower:
        return base + (
            "Debugging hint: Check whether the circuit allocates enough classical bits, whether gates use valid qubit indices, "
            "and whether measurement maps qubits to classical bits correctly.\n\n"
            "Example:\n```python\nfrom qiskit import QuantumCircuit\nqc = QuantumCircuit(1, 1)\nqc.measure(0, 0)\n```\n\n"
            "Reflective prompt: Which index refers to the qubit and which index refers to the classical bit?"
        )
    return base + (
        "Guided explanation: connect the concept to a minimal Qiskit circuit. Ask what the circuit prepares, what is measured, "
        "and how the resulting counts should be interpreted.\n\n"
        "Reflective prompt: Explain this concept in your own words before asking for a complete solution."
    )


def call_gemini(prompt: str, response_language: str = "English") -> Tuple[str, str, str]:
    api_key = _secret("GEMINI_API_KEY", "").strip()
    model = _secret("GEMINI_MODEL", "gemini-2.0-flash").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_prompt(response_language)}\n\n{prompt}"}],
            }
        ],
        "generationConfig": {"temperature": 0.35, "maxOutputTokens": 900},
    }
    r = requests.post(url, json=payload, timeout=45)
    if r.status_code != 200:
        raise RuntimeError(f"Gemini API HTTP {r.status_code}: {r.text[:1200]}")
    data = r.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {json.dumps(data)[:800]}")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "\n".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError(f"Gemini returned an empty response: {json.dumps(data)[:800]}")
    return text, "gemini", model


def call_openai(prompt: str, response_language: str = "English") -> Tuple[str, str, str]:
    api_key = _secret("OPENAI_API_KEY", "").strip()
    base_url = _secret("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = _secret("OPENAI_MODEL", "gpt-4o-mini").strip()
    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt(response_language)},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.35,
        "max_tokens": 900,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=45)
    if r.status_code != 200:
        raise RuntimeError(f"OpenAI-compatible API HTTP {r.status_code}: {r.text[:1200]}")
    data = r.json()
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not text:
        raise RuntimeError(f"OpenAI-compatible API returned an empty response: {json.dumps(data)[:800]}")
    return text, "openai", model


def call_groq(prompt: str, response_language: str = "English") -> Tuple[str, str, str]:
    """Call Groq through its OpenAI-compatible Chat Completions endpoint."""
    api_key = _secret("GROQ_API_KEY", "").strip()
    base_url = _secret("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
    model = _secret("GROQ_MODEL", "llama-3.1-8b-instant").strip()
    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt(response_language)},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.35,
        "max_tokens": 900,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=45)
    if r.status_code != 200:
        raise RuntimeError(f"Groq API HTTP {r.status_code}: {r.text[:1200]}")
    data = r.json()
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not text:
        raise RuntimeError(f"Groq API returned an empty response: {json.dumps(data)[:800]}")
    return text, "groq", model


def generate_tutor_response(
    task: str,
    concept: str,
    student_input: str = "",
    student_profile: Optional[Dict[str, Any]] = None,
    lesson_context: Optional[Dict[str, Any]] = None,
) -> TutorResult:
    response_language = resolve_response_language(student_input, student_profile, lesson_context)
    prompt = build_prompt(task, concept, student_input, student_profile, lesson_context)
    status = provider_status()
    provider = status["provider"]
    if provider == "gemini" and status["gemini_key_detected"]:
        try:
            text, prov, model = call_gemini(prompt, response_language)
            return TutorResult(text, "llm", prov, model)
        except Exception as exc:
            fallback = (
                "The generative AI tutor is temporarily unavailable. Here is a local learning hint you can use now.\n\n"
                + local_fallback(task, concept, student_input, response_language)
            )
            return TutorResult(fallback, "llm_error", "gemini", status["model"], str(exc))
    if provider == "openai" and status["openai_key_detected"]:
        try:
            text, prov, model = call_openai(prompt, response_language)
            return TutorResult(text, "llm", prov, model)
        except Exception as exc:
            fallback = (
                "The generative AI tutor is temporarily unavailable. Here is a local learning hint you can use now.\n\n"
                + local_fallback(task, concept, student_input, response_language)
            )
            return TutorResult(fallback, "llm_error", "openai", status["model"], str(exc))
    if provider == "groq" and status["groq_key_detected"]:
        try:
            text, prov, model = call_groq(prompt, response_language)
            return TutorResult(text, "llm", prov, model)
        except Exception as exc:
            fallback = (
                "The generative AI tutor is temporarily unavailable. Here is a local learning hint you can use now.\n\n"
                + local_fallback(task, concept, student_input, response_language)
            )
            return TutorResult(fallback, "llm_error", "groq", status["model"], str(exc))
    return TutorResult(local_fallback(task, concept, student_input, response_language), "rule_based", "local", "local-fallback")
