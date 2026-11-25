"""Optional, local-first Ollama client for 3alimnIA.

Only localhost is accepted by default. Remote servers require an explicit,
operator-controlled opt-in; never forward a teacher's documents silently.
"""
from __future__ import annotations

import ipaddress
import os
from urllib.parse import urlsplit
from typing import Any, Dict, List, Optional

import requests


class LocalModelError(RuntimeError):
    """A local model service was unavailable or returned an invalid response."""


def configured_url() -> str:
    url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/")
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("OLLAMA_BASE_URL must be a valid http(s) URL without credentials")
    if parsed.path or parsed.query or parsed.fragment:
        raise ValueError("OLLAMA_BASE_URL must contain only a host and optional port")
    name = parsed.hostname.lower()
    local = name == "localhost"
    if not local:
        try:
            local = ipaddress.ip_address(name).is_loopback
        except ValueError:
            local = False
    if not local and os.getenv("OLLAMA_ALLOW_REMOTE", "false").lower() not in {"1", "true", "yes"}:
        raise ValueError("Remote Ollama is blocked; configure OLLAMA_ALLOW_REMOTE only on a trusted network")
    return url


def _post(endpoint: str, payload: Dict[str, Any], *, timeout: int = 180) -> Dict[str, Any]:
    try:
        response = requests.post(
            f"{configured_url()}/api/{endpoint}", json=payload, timeout=(10, timeout),
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise LocalModelError("Ollama returned an unexpected response format")
        return data
    except (requests.RequestException, ValueError) as exc:
        raise LocalModelError(f"Ollama {endpoint} failed: {exc}") from exc


def chat(
    *, model: str, prompt: str, system: str = "", max_tokens: int = 2500,
    response_schema: Optional[Dict[str, Any]] = None,
) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": max(128, min(int(max_tokens), 8192)),
            "num_ctx": max(2048, min(int(os.getenv("OLLAMA_CONTEXT_TOKENS", "8192")), 65536)),
        },
    }
    if response_schema:
        payload["format"] = response_schema
    result = _post("chat", payload, timeout=int(os.getenv("OLLAMA_CHAT_TIMEOUT_SECONDS", "300")))
    content = (result.get("message") or {}).get("content", "")
    if not str(content).strip():
        raise LocalModelError("Ollama returned an empty chat message; check the model and context limit")
    return str(content).strip()


def embed(texts: List[str], *, model: Optional[str] = None) -> List[List[float]]:
    if not texts:
        return []
    embedding_model = model or os.getenv("RAG_EMBEDDING_MODEL", "qwen3-embedding:0.6b")
    result = _post("embed", {"model": embedding_model, "input": texts, "truncate": False}, timeout=180)
    vectors = result.get("embeddings")
    if not isinstance(vectors, list) or len(vectors) != len(texts) or not all(isinstance(v, list) and v for v in vectors):
        raise LocalModelError("Ollama returned an invalid embedding batch")
    return [[float(x) for x in vector] for vector in vectors]
