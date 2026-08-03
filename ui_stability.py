"""Shared UI stability and design-system helpers for 3alimnIA.

V6.16.5 centralizes defensive layout handling, friendly error rendering,
and status semantics used across Streamlit workspaces.  The module is
intentionally small and dependency-light so it can be imported safely by
public, teacher, and evaluator interfaces.
"""

from __future__ import annotations

import hashlib
from html import escape
from typing import Any, Iterable, Sequence

try:
    import streamlit as st
except ModuleNotFoundError:  # Allows static/offline validation without Streamlit installed.
    st = None  # type: ignore[assignment]


def _streamlit():
    global st
    if st is None:
        import importlib
        st = importlib.import_module("streamlit")
    return st

ALLOWED_GAPS = {"small", "medium", "large"}
ALLOWED_VERTICAL_ALIGNMENTS = {"top", "center", "bottom"}

STATUS_ALIASES = {
    "completed": ("approved", "approved"),
    "approved": ("approved", "approved"),
    "ready": ("ready", "ready"),
    "generated": ("review", "review"),
    "needs_review": ("review", "review"),
    "review": ("review", "review"),
    "running": ("running", "running"),
    "generating": ("running", "running"),
    "retrying": ("running", "running"),
    "queued": ("queued", "queued"),
    "waiting_for_dependency": ("blocked", "blocked"),
    "blocked": ("blocked", "blocked"),
    "failed": ("failed", "failed"),
    "error": ("failed", "failed"),
    "llm_error": ("failed", "failed"),
    "canceled": ("failed", "failed"),
    "not_started": ("pending", "pending"),
    "pending": ("pending", "pending"),
    "": ("pending", "pending"),
}

STATUS_COPY = {
    "ar": {
        "approved": "معتمدة",
        "ready": "جاهزة",
        "review": "تحتاج مراجعة",
        "running": "جارٍ التنفيذ",
        "queued": "في قائمة الانتظار",
        "blocked": "تنتظر مرحلة سابقة",
        "failed": "تعذر التنفيذ",
        "pending": "لم تبدأ",
    },
    "fr": {
        "approved": "Approuvée",
        "ready": "Prête",
        "review": "À réviser",
        "running": "En cours",
        "queued": "En attente",
        "blocked": "Dépendance requise",
        "failed": "Échec",
        "pending": "Non démarrée",
    },
    "en": {
        "approved": "Approved",
        "ready": "Ready",
        "review": "Needs review",
        "running": "Running",
        "queued": "Queued",
        "blocked": "Waiting for dependency",
        "failed": "Failed",
        "pending": "Not started",
    },
}


def normalize_gap(value: Any, default: str = "small") -> str:
    gap = str(value or default).strip().lower()
    return gap if gap in ALLOWED_GAPS else default


def normalize_vertical_alignment(value: Any, default: str = "top") -> str:
    alignment = str(value or default).strip().lower()
    return alignment if alignment in ALLOWED_VERTICAL_ALIGNMENTS else default


def columns(
    spec: int | Sequence[float],
    *,
    gap: str = "small",
    vertical_alignment: str = "top",
):
    """Create Streamlit columns with validated, backwards-compatible options.

    Streamlit has changed layout signatures across releases.  This helper
    validates values first and retries without ``vertical_alignment`` only when
    the installed version does not support the argument.  Other exceptions are
    re-raised so genuine application errors are never hidden.
    """

    safe_gap = normalize_gap(gap)
    safe_alignment = normalize_vertical_alignment(vertical_alignment)
    try:
        return _streamlit().columns(spec, gap=safe_gap, vertical_alignment=safe_alignment)
    except TypeError:
        return _streamlit().columns(spec, gap=safe_gap)
    except Exception as exc:
        message = str(exc).lower()
        compatibility_error = (
            "verticalalignment" in message
            or "vertical_alignment" in message
            or "unexpected keyword" in message
        )
        if compatibility_error:
            return _streamlit().columns(spec, gap=safe_gap)
        raise


def status_semantics(raw_status: Any) -> tuple[str, str]:
    key = str(raw_status or "").strip().lower()
    return STATUS_ALIASES.get(key, ("pending", "pending"))


def status_label(raw_status: Any, lang: str = "en") -> str:
    semantic, _ = status_semantics(raw_status)
    copy = STATUS_COPY.get(lang, STATUS_COPY["en"])
    return copy.get(semantic, copy["pending"])


def status_badge_html(raw_status: Any, lang: str = "en", label: str | None = None) -> str:
    semantic, css_status = status_semantics(raw_status)
    text = label or STATUS_COPY.get(lang, STATUS_COPY["en"]).get(semantic, semantic)
    return (
        f"<span class='qai-status-badge qai-status-{escape(css_status)}'>"
        f"<i aria-hidden='true'></i>{escape(str(text))}</span>"
    )


def error_fingerprint(message: Any) -> str:
    raw = str(message or "unknown-error").encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()[:10].upper()


def friendly_error(message: Any, lang: str = "en") -> tuple[str, str, str]:
    """Return user-facing copy, technical details, and a stable incident code."""

    raw = str(message or "").strip()
    lowered = raw.lower()
    if "429" in lowered or "quota" in lowered or "resource_exhausted" in lowered:
        key = "quota"
    elif "413" in lowered or "too large" in lowered or "request entity" in lowered:
        key = "size"
    elif "nameerror" in lowered or "not defined" in lowered:
        key = "render"
    elif "verticalalignment" in lowered or "vertical_alignment" in lowered:
        key = "layout"
    elif "timeout" in lowered or "timed out" in lowered:
        key = "timeout"
    else:
        key = "generic"

    copy = {
        "ar": {
            "quota": "بلغت خدمة الذكاء الاصطناعي حد الاستخدام الحالي. احتُفظ بآخر نتيجة ناجحة ويمكن المحاولة لاحقًا.",
            "size": "حجم الطلب أكبر من الحد المتاح. استخدم سياقًا أقصر أو نمط البحث السريع.",
            "render": "تعذر عرض هذا الجزء من الصفحة. بيانات المشروع محفوظة ويمكن إعادة المحاولة بعد تحديث التطبيق.",
            "layout": "حدث تعارض في تخطيط الواجهة مع إصدار Streamlit الحالي. بيانات المشروع محفوظة.",
            "timeout": "استغرقت العملية وقتًا أطول من الحد المتاح. لم تُحذف البيانات ويمكن إعادة المحاولة.",
            "generic": "تعذر إكمال العملية حاليًا. بيانات المشروع محفوظة ويمكن إعادة المحاولة.",
            "title": "تعذر إكمال هذا الجزء",
            "details": "التفاصيل التقنية",
            "incident": "رمز الحادثة",
            "retry": "إعادة المحاولة",
        },
        "fr": {
            "quota": "Le quota actuel du service d’IA est atteint. Le dernier résultat valide a été conservé.",
            "size": "La requête dépasse la taille autorisée. Utilisez un contexte plus court ou la recherche rapide.",
            "render": "Cette section ne peut pas être affichée. Les données du projet sont conservées.",
            "layout": "La mise en page n’est pas compatible avec la version actuelle de Streamlit. Les données sont conservées.",
            "timeout": "L’opération a dépassé le délai autorisé. Les données sont conservées.",
            "generic": "L’opération n’a pas pu être terminée. Les données du projet sont conservées.",
            "title": "Impossible de terminer cette section",
            "details": "Détails techniques",
            "incident": "Code d’incident",
            "retry": "Réessayer",
        },
        "en": {
            "quota": "The current AI-service quota has been reached. The last valid result was preserved.",
            "size": "The request exceeds the available size limit. Use a shorter context or quick research mode.",
            "render": "This section could not be displayed. Project data was preserved.",
            "layout": "The current Streamlit version rejected a layout option. Project data was preserved.",
            "timeout": "The operation exceeded the available time limit. Project data was preserved.",
            "generic": "The operation could not be completed. Project data was preserved.",
            "title": "This section could not be completed",
            "details": "Technical details",
            "incident": "Incident code",
            "retry": "Retry",
        },
    }
    language_copy = copy.get(lang, copy["en"])
    return language_copy[key], raw, error_fingerprint(raw)


def render_error_card(
    error: Exception | str,
    *,
    lang: str = "en",
    retry_key: str | None = None,
) -> bool:
    """Render a safe localized error card.

    Returns ``True`` when the optional retry button is pressed.
    """

    friendly, technical, incident = friendly_error(error, lang)
    labels = {
        "ar": ("تعذر إكمال هذا الجزء", "التفاصيل التقنية", "رمز الحادثة", "إعادة المحاولة"),
        "fr": ("Impossible de terminer cette section", "Détails techniques", "Code d’incident", "Réessayer"),
        "en": ("This section could not be completed", "Technical details", "Incident code", "Retry"),
    }.get(lang, ("This section could not be completed", "Technical details", "Incident code", "Retry"))
    direction = "rtl" if lang == "ar" else "ltr"
    api = _streamlit()
    api.markdown(
        f"<section class='qai-ui-error-card' dir='{direction}' role='alert'>"
        f"<div class='qai-ui-error-icon' aria-hidden='true'>!</div>"
        f"<div><h3>{escape(labels[0])}</h3><p>{escape(friendly)}</p>"
        f"<small>{escape(labels[2])}: {escape(incident)}</small></div></section>",
        unsafe_allow_html=True,
    )
    with api.expander(labels[1], expanded=False):
        api.code(technical or type(error).__name__, language="text")
    if retry_key:
        return bool(api.button(labels[3], key=retry_key, type="primary", use_container_width=True))
    return False


def render_empty_state(title: str, body: str, *, direction: str = "ltr") -> None:
    api = _streamlit()
    api.markdown(
        f"<section class='qai-ui-empty-state' dir='{escape(direction)}'>"
        f"<span aria-hidden='true'></span><h3>{escape(title)}</h3><p>{escape(body)}</p></section>",
        unsafe_allow_html=True,
    )
