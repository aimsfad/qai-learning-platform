"""Task-aware provider selection for 3alimnIA.

The router never exposes API-key values to the UI. It only reports whether a
provider is configured and returns private connection details to server-side
callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import streamlit as st


@dataclass(frozen=True)
class ProviderSelection:
    provider: str
    model: str
    available: bool
    base_url: str = ""
    api_key: str = ""
    role: str = "primary"


def _secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def _as_bool(name: str, default: bool = True) -> bool:
    raw = _secret(name, "true" if default else "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _configured_provider(task_type: str) -> str:
    task = (task_type or "content").strip().lower()
    if task == "file_analysis":
        return _secret("FILE_ANALYSIS_PROVIDER", "gemini").strip().lower() or "gemini"
    if task == "content":
        return (
            _secret("CONTENT_LLM_PROVIDER", "").strip().lower()
            or _secret("LLM_PROVIDER", "groq").strip().lower()
            or "groq"
        )
    if task == "fast":
        return (
            _secret("FAST_LLM_PROVIDER", "").strip().lower()
            or _secret("LLM_PROVIDER", "groq").strip().lower()
            or "groq"
        )
    return _secret("LLM_PROVIDER", "groq").strip().lower() or "groq"




def _normalize_model(provider: str, model: str) -> str:
    clean = (model or "").strip()
    migrations = {
        ("groq", "llama-3.1-8b-instant"): "openai/gpt-oss-20b",
        ("groq", "llama-3.3-70b-versatile"): "openai/gpt-oss-120b",
        ("gemini", "gemini-2.0-flash"): "gemini-3.6-flash",
    }
    return migrations.get((provider.strip().lower(), clean), clean)

def _model_for(provider: str, task_type: str) -> str:
    task = (task_type or "content").strip().lower()
    provider = provider.strip().lower()

    if provider == "groq":
        if task == "content":
            return (
                _secret("CONTENT_GROQ_MODEL", "").strip()
                or _secret("GROQ_CONTENT_MODEL", "").strip()
                or "openai/gpt-oss-120b"
            )
        if task == "fast":
            return _secret("FAST_GROQ_MODEL", "").strip() or "openai/gpt-oss-20b"
        return _secret("GROQ_MODEL", "").strip() or "openai/gpt-oss-20b"

    if provider == "gemini":
        if task == "file_analysis":
            return (
                _secret("FILE_ANALYSIS_GEMINI_MODEL", "").strip()
                or _secret("GEMINI_MODEL", "").strip()
                or "gemini-3.6-flash"
            )
        if task == "content":
            return (
                _secret("CONTENT_GEMINI_MODEL", "").strip()
                or _secret("GEMINI_MODEL", "").strip()
                or "gemini-3.6-flash"
            )
        return _secret("GEMINI_MODEL", "").strip() or "gemini-3.6-flash"

    if provider == "openrouter":
        return (
            _secret("CONTENT_OPENROUTER_MODEL", "").strip()
            or _secret("OPENROUTER_MODEL", "").strip()
            or "openrouter/free"
        )

    if provider == "openai":
        return (
            _secret("CONTENT_OPENAI_MODEL", "").strip()
            or _secret("OPENAI_MODEL", "").strip()
            or "gpt-4o-mini"
        )

    if provider == "anthropic":
        return (
            _secret("CONTENT_ANTHROPIC_MODEL", "").strip()
            or _secret("ANTHROPIC_MODEL", "").strip()
            or "claude-3-5-haiku-latest"
        )

    return "local-fallback"


def _selection(provider: str, task_type: str, role: str = "primary") -> ProviderSelection:
    provider = (provider or "local").strip().lower()
    model = _normalize_model(provider, _model_for(provider, task_type))

    if provider == "groq":
        key = _secret("GROQ_API_KEY", "").strip()
        base = _secret("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip().rstrip("/")
    elif provider == "gemini":
        key = _secret("GEMINI_API_KEY", "").strip()
        base = "https://generativelanguage.googleapis.com/v1beta"
    elif provider == "openrouter":
        key = _secret("OPENROUTER_API_KEY", "").strip()
        base = _secret("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip().rstrip("/")
    elif provider == "openai":
        key = _secret("OPENAI_API_KEY", "").strip()
        base = _secret("OPENAI_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
    elif provider == "anthropic":
        key = _secret("ANTHROPIC_API_KEY", "").strip()
        base = _secret("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1").strip().rstrip("/")
    else:
        key = ""
        base = ""

    return ProviderSelection(
        provider=provider,
        model=model,
        available=bool(key),
        base_url=base,
        api_key=key,
        role=role,
    )


def generation_candidates(task_type: str = "content") -> List[ProviderSelection]:
    """Return an ordered, de-duplicated provider chain for a task."""
    primary = _configured_provider(task_type)
    if not _as_bool("ENABLE_MODEL_FALLBACK", True):
        return [_selection(primary, task_type, "primary")]

    task = (task_type or "content").strip().lower()
    if task == "file_analysis":
        order = [primary, "gemini"]
    elif task == "content":
        order = [primary, "groq", "gemini", "openrouter", "openai", "anthropic"]
    else:
        order = [primary, "groq", "gemini", "openrouter", "openai", "anthropic"]

    selections: List[ProviderSelection] = []
    seen = set()
    for provider in order:
        provider = (provider or "").strip().lower()
        if not provider or provider in seen or provider in {"local", "none", "fallback"}:
            continue
        seen.add(provider)
        selections.append(_selection(provider, task_type, "primary" if not selections else "fallback"))
    return selections or [_selection("local", task_type, "primary")]


def provider_status(task_type: str = "content") -> Dict[str, Any]:
    candidates = generation_candidates(task_type)
    configured = candidates[0]
    available_candidates = [item for item in candidates if item.available]
    effective = available_candidates[0] if available_candidates else configured
    ready_fallbacks = [item.provider for item in available_candidates[1:]]
    return {
        "provider": effective.provider,
        "model": effective.model,
        "available": bool(available_candidates),
        "configured_provider": configured.provider,
        "configured_model": configured.model,
        "using_fallback": effective.provider != configured.provider,
        "ready_fallbacks": ready_fallbacks,
        "fallback_enabled": _as_bool("ENABLE_MODEL_FALLBACK", True),
    }


def integration_status() -> Dict[str, bool]:
    """Report configured auxiliary services without exposing their secrets."""
    return {
        "cohere": bool(_secret("COHERE_API_KEY", "").strip()),
        "cloudflare": bool(
            _secret("CLOUDFLARE_ACCOUNT_ID", "").strip()
            and _secret("CLOUDFLARE_API_TOKEN", "").strip()
        ),
        "openrouter": bool(_secret("OPENROUTER_API_KEY", "").strip()),
        "gemini": bool(_secret("GEMINI_API_KEY", "").strip()),
        "groq": bool(_secret("GROQ_API_KEY", "").strip()),
    }
