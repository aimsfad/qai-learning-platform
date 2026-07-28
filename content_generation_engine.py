"""Generic LLM generation engine for the 3alimnIA Teacher Content Studio."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Tuple

import requests
import streamlit as st


@dataclass
class ContentGenerationResult:
    response: str
    provider: str
    model: str
    status: str
    diagnostic: str = ""
    latency_ms: int = 0


def _secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def provider_status() -> Dict[str, Any]:
    configured = _secret("CONTENT_LLM_PROVIDER", "").strip().lower() or _secret("LLM_PROVIDER", "").strip().lower()
    keys = {
        "groq": bool(_secret("GROQ_API_KEY", "").strip()),
        "openai": bool(_secret("OPENAI_API_KEY", "").strip()),
        "gemini": bool(_secret("GEMINI_API_KEY", "").strip()),
        "anthropic": bool(_secret("ANTHROPIC_API_KEY", "").strip()),
    }
    if configured in {"", "local", "none", "fallback"}:
        provider = next((name for name in ("groq", "gemini", "openai", "anthropic") if keys[name]), "local")
    else:
        provider = configured
    models = {
        "groq": _secret("CONTENT_GROQ_MODEL", "").strip() or _secret("GROQ_MODEL", "llama-3.1-8b-instant").strip(),
        "openai": _secret("CONTENT_OPENAI_MODEL", "").strip() or _secret("OPENAI_MODEL", "gpt-4o-mini").strip(),
        "gemini": _secret("CONTENT_GEMINI_MODEL", "").strip() or _secret("GEMINI_MODEL", "gemini-2.0-flash").strip(),
        "anthropic": _secret("CONTENT_ANTHROPIC_MODEL", "").strip() or _secret("ANTHROPIC_MODEL", "claude-3-5-haiku-latest").strip(),
        "local": "prompt-export-only",
    }
    return {"provider": provider, "available": keys.get(provider, False), "model": models.get(provider, "prompt-export-only")}


def content_system_prompt(output_language: str) -> str:
    return (
        "You are the 3alimnIA Educational Content Production Engine. "
        "Follow the supplied master prompt and teacher brief exactly. Work on the requested phase only. "
        "Prioritize scientific accuracy, evidence, instructional sequencing, accessibility, multilingual consistency, "
        "and implementation-ready outputs. Do not invent sources or claim that you browsed when browsing is unavailable. "
        "Explicitly mark missing evidence. Preserve the attempt-first pedagogy and progressive AI scaffolding. "
        f"Write the response in {output_language}."
    )


def _call_openai_compatible(prompt: str, system: str, *, provider: str, model: str, max_tokens: int) -> Tuple[str, str, str]:
    if provider == "groq":
        key = _secret("GROQ_API_KEY", "").strip()
        base = _secret("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
    else:
        key = _secret("OPENAI_API_KEY", "").strip()
        base = _secret("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    response = requests.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "temperature": 0.25,
            "max_tokens": max_tokens,
        },
        timeout=90,
    )
    if response.status_code != 200:
        raise RuntimeError(f"{provider} HTTP {response.status_code}: {response.text[:1200]}")
    data = response.json()
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not text:
        raise RuntimeError(f"{provider} returned an empty response")
    return text, provider, model


def _call_gemini(prompt: str, system: str, model: str, max_tokens: int) -> Tuple[str, str, str]:
    key = _secret("GEMINI_API_KEY", "").strip()
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        json={
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.25, "maxOutputTokens": max_tokens},
        },
        timeout=90,
    )
    if response.status_code != 200:
        raise RuntimeError(f"gemini HTTP {response.status_code}: {response.text[:1200]}")
    data = response.json()
    candidates = data.get("candidates", [])
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    text = "\n".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError(f"gemini returned an empty response: {json.dumps(data)[:800]}")
    return text, "gemini", model


def _call_anthropic(prompt: str, system: str, model: str, max_tokens: int) -> Tuple[str, str, str]:
    key = _secret("ANTHROPIC_API_KEY", "").strip()
    base = _secret("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1").rstrip("/")
    response = requests.post(
        f"{base}/messages",
        headers={
            "x-api-key": key,
            "anthropic-version": _secret("ANTHROPIC_VERSION", "2023-06-01"),
            "content-type": "application/json",
        },
        json={
            "model": model,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.25,
            "max_tokens": max_tokens,
        },
        timeout=90,
    )
    if response.status_code != 200:
        raise RuntimeError(f"anthropic HTTP {response.status_code}: {response.text[:1200]}")
    data = response.json()
    text = "\n".join(item.get("text", "") for item in data.get("content", []) if item.get("type") == "text").strip()
    if not text:
        raise RuntimeError("anthropic returned an empty response")
    return text, "anthropic", model


def generate_content(prompt: str, output_language: str, max_tokens: int = 4000) -> ContentGenerationResult:
    started = time.perf_counter()
    status = provider_status()
    provider = status["provider"]
    model = status["model"]
    if provider == "local" or not status["available"]:
        return ContentGenerationResult(
            response=(
                "No content-generation provider is configured. The production prompt has been compiled successfully. "
                "Configure a supported API key, then run generation again."
            ),
            provider="local",
            model="prompt-export-only",
            status="not_configured",
            diagnostic="Set CONTENT_LLM_PROVIDER or LLM_PROVIDER and the corresponding API key in Streamlit secrets.",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
    try:
        system = content_system_prompt(output_language)
        if provider in {"groq", "openai"}:
            text, provider_name, model_name = _call_openai_compatible(
                prompt, system, provider=provider, model=model, max_tokens=max_tokens
            )
        elif provider == "gemini":
            text, provider_name, model_name = _call_gemini(prompt, system, model, max_tokens)
        elif provider == "anthropic":
            text, provider_name, model_name = _call_anthropic(prompt, system, model, max_tokens)
        else:
            raise RuntimeError(f"Unsupported provider: {provider}")
        return ContentGenerationResult(
            response=text,
            provider=provider_name,
            model=model_name,
            status="completed",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
    except Exception as exc:
        return ContentGenerationResult(
            response="Generation failed. The compiled prompt is preserved and can be downloaded or retried.",
            provider=provider,
            model=model,
            status="error",
            diagnostic=str(exc),
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
