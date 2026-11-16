"""Consent-gated Gemini text embeddings for the 3alimnIA online RAG prototype.

Only called after an authenticated project owner opts in to transmitting source
excerpts or search queries to the chosen external service. Secrets never appear
in logs or exceptions. Requests go to a fixed official HTTPS endpoint.
"""
from __future__ import annotations

import math
import os
from typing import List

import requests

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 768
_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent"


def _api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        return key
    try:
        import streamlit as st
        return str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        return ""


def configured() -> bool:
    return bool(_api_key())


def _normalize(values: list) -> List[float]:
    if len(values) != EMBEDDING_DIM or not all(isinstance(v, (int, float)) and math.isfinite(float(v)) for v in values):
        raise RuntimeError("Gemini embedding response has an unexpected dimension or invalid values")
    vector = [float(v) for v in values]
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        raise RuntimeError("Gemini embedding response was a zero vector")
    return [v / norm for v in vector]


def embed_texts(texts: List[str], *, purpose: str) -> List[List[float]]:
    """Embed in a fixed space; purpose is document or query.

    One request per text deliberately makes partial failures explicit and limits
    data transmission. Production deployments should use controlled queues and
    quota-aware batching rather than invoking this on the Streamlit UI thread.
    """
    if purpose not in {"document", "query"}:
        raise ValueError("Embedding purpose must be document or query")
    key = _api_key()
    if not key:
        raise RuntimeError("Gemini embedding provider is not configured")
    if len(texts) > 100:
        raise ValueError("Embedding batch exceeds the V0.2 safety limit (100 excerpts)")
    results = []
    for text in texts:
        value = str(text or "").strip()
        if not value or len(value) > 4400:
            raise ValueError("Embedding text must be non-empty and at most 4400 characters")
        payload = {
            "model": f"models/{EMBEDDING_MODEL}",
            "content": {"parts": [{"text": value}]},
            "taskType": "RETRIEVAL_DOCUMENT" if purpose == "document" else "RETRIEVAL_QUERY",
            "outputDimensionality": EMBEDDING_DIM,
        }
        try:
            response = requests.post(_ENDPOINT, headers={
                "x-goog-api-key": key, "Content-Type": "application/json",
            }, json=payload, timeout=25)
            response.raise_for_status()
            raw = response.json()
            results.append(_normalize(raw.get("embedding", {}).get("values", [])))
        except requests.exceptions.RequestException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            # No provider error body, URL query, source text or API key in UI diagnostics.
            raise RuntimeError(f"Gemini embedding request failed (HTTP {status or 'network error'})") from None
        except (TypeError, ValueError, AttributeError, KeyError):
            raise RuntimeError("Gemini embedding response could not be parsed") from None
    return results
