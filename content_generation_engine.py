"""Task-routed LLM generation engine for the 3alimnIA Teacher Content Studio."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Tuple

import requests
import streamlit as st

import model_router


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


def provider_status():
    """Return a sanitized status object for display in Streamlit."""
    return model_router.provider_status("content")


def content_system_prompt(output_language: str) -> str:
    return (
        "You are the 3alimnIA Educational Content Production Engine. "
        "Follow the supplied master prompt and teacher brief exactly. Work on the requested phase only. "
        "Prioritize scientific accuracy, evidence, instructional sequencing, accessibility, multilingual consistency, "
        "and implementation-ready outputs. Do not invent sources or claim that you browsed when browsing is unavailable. "
        "Explicitly mark missing evidence. Preserve the attempt-first pedagogy and progressive AI scaffolding. "
        f"Write the response in {output_language}."
    )


def _call_openai_compatible(
    prompt: str,
    system: str,
    *,
    provider: str,
    model: str,
    max_tokens: int,
    api_key: str,
    base_url: str,
) -> Tuple[str, str, str]:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if provider == "openrouter":
        app_url = _secret("APP_BASE_URL", "").strip()
        app_name = _secret("OPENROUTER_APP_NAME", "3alimnIA").strip() or "3alimnIA"
        if app_url:
            headers["HTTP-Referer"] = app_url
        headers["X-Title"] = app_name

    response = requests.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers=headers,
        json={
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "temperature": 0.25,
            "max_tokens": max_tokens,
        },
        timeout=int(_secret("CONTENT_GENERATION_TIMEOUT_SECONDS", "120") or "120"),
    )
    if response.status_code != 200:
        raise RuntimeError(f"{provider} HTTP {response.status_code}: {response.text[:1200]}")
    data = response.json()
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not text:
        raise RuntimeError(f"{provider} returned an empty response")
    return text, provider, model


def _call_gemini(
    prompt: str,
    system: str,
    *,
    model: str,
    max_tokens: int,
    api_key: str,
    base_url: str,
) -> Tuple[str, str, str]:
    response = requests.post(
        f"{base_url.rstrip('/')}/models/{model}:generateContent",
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json={
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.25, "maxOutputTokens": max_tokens},
        },
        timeout=int(_secret("CONTENT_GENERATION_TIMEOUT_SECONDS", "120") or "120"),
    )
    if response.status_code != 200:
        raise RuntimeError(f"gemini HTTP {response.status_code}: {response.text[:1200]}")
    data = response.json()
    candidates = data.get("candidates", [])
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    text = "\n".join(part.get("text", "") for part in parts if part.get("text")).strip()
    if not text:
        raise RuntimeError(f"gemini returned an empty response: {json.dumps(data)[:800]}")
    return text, "gemini", model


def _call_anthropic(
    prompt: str,
    system: str,
    *,
    model: str,
    max_tokens: int,
    api_key: str,
    base_url: str,
) -> Tuple[str, str, str]:
    response = requests.post(
        f"{base_url.rstrip('/')}/messages",
        headers={
            "x-api-key": api_key,
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
        timeout=int(_secret("CONTENT_GENERATION_TIMEOUT_SECONDS", "120") or "120"),
    )
    if response.status_code != 200:
        raise RuntimeError(f"anthropic HTTP {response.status_code}: {response.text[:1200]}")
    data = response.json()
    text = "\n".join(item.get("text", "") for item in data.get("content", []) if item.get("type") == "text").strip()
    if not text:
        raise RuntimeError("anthropic returned an empty response")
    return text, "anthropic", model


def _call_selection(selection, prompt: str, system: str, max_tokens: int) -> Tuple[str, str, str]:
    if selection.provider in {"groq", "openai", "openrouter"}:
        return _call_openai_compatible(
            prompt,
            system,
            provider=selection.provider,
            model=selection.model,
            max_tokens=max_tokens,
            api_key=selection.api_key,
            base_url=selection.base_url,
        )
    if selection.provider == "gemini":
        return _call_gemini(
            prompt,
            system,
            model=selection.model,
            max_tokens=max_tokens,
            api_key=selection.api_key,
            base_url=selection.base_url,
        )
    if selection.provider == "anthropic":
        return _call_anthropic(
            prompt,
            system,
            model=selection.model,
            max_tokens=max_tokens,
            api_key=selection.api_key,
            base_url=selection.base_url,
        )
    raise RuntimeError(f"Unsupported provider: {selection.provider}")


def generate_content(prompt: str, output_language: str, max_tokens: int = 5000) -> ContentGenerationResult:
    """Generate content with task-aware routing and a safe provider fallback chain."""
    started = time.perf_counter()
    candidates = model_router.generation_candidates("content")
    available = [selection for selection in candidates if selection.available]
    if not available:
        primary = candidates[0]
        return ContentGenerationResult(
            response=(
                "No content-generation provider is configured. The production prompt has been compiled successfully. "
                "Configure a supported API key, then run generation again."
            ),
            provider=primary.provider if primary.provider != "local" else "local",
            model=primary.model if primary.provider != "local" else "prompt-export-only",
            status="not_configured",
            diagnostic="Configure GROQ_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY.",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    system = content_system_prompt(output_language)
    failures = []
    for index, selection in enumerate(available):
        try:
            text, provider_name, model_name = _call_selection(selection, prompt, system, max_tokens)
            fallback_note = ""
            if index > 0:
                previous = "; ".join(failures)
                fallback_note = f"Fallback used after earlier provider failure(s): {previous}"[:1500]
            return ContentGenerationResult(
                response=text,
                provider=provider_name,
                model=model_name,
                status="completed",
                diagnostic=fallback_note,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
        except Exception as exc:
            failures.append(f"{selection.provider}/{selection.model}: {exc}")

    primary = available[0]
    return ContentGenerationResult(
        response="Generation failed. The compiled prompt is preserved and can be downloaded or retried.",
        provider=primary.provider,
        model=primary.model,
        status="error",
        diagnostic=" | ".join(failures)[:5000],
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
