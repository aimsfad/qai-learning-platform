"""Centralized XSS-safe HTML rendering helpers for 3alimnIA V7.1 Ultra Liquid Glass UI."""

from __future__ import annotations

import html
import re
from typing import Iterable, Mapping, Optional
from urllib.parse import urlparse

_SAFE_SCHEMES = {"http", "https", "mailto"}
_DANGEROUS_TAG_RE = re.compile(
    r"<\s*(script|iframe|object|embed|form|style)\b[^>]*>.*?<\s*/\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_INLINE_HANDLER_RE = re.compile(r"\son[a-z]+\s*=\s*(['\"]).*?\1", re.IGNORECASE)


def esc(value: object) -> str:
    """Escape untrusted text for safe insertion into HTML templates."""
    return html.escape(str(value if value is not None else ""), quote=True)


def safe_url(url: Optional[str], fallback: str = "#") -> str:
    """Allow only http/https/mailto URLs to prevent javascript: XSS."""
    raw = str(url or "").strip()
    if not raw:
        return fallback
    parsed = urlparse(raw)
    if parsed.scheme.lower() in _SAFE_SCHEMES:
        return esc(raw)
    if raw.startswith("/") and not raw.startswith("//"):
        return esc(raw)
    return fallback


def sanitize_fragment(fragment: str) -> str:
    """Strip executable tags and inline JS handlers from rich HTML fragments."""
    cleaned = _DANGEROUS_TAG_RE.sub("", str(fragment or ""))
    cleaned = _INLINE_HANDLER_RE.sub("", cleaned)
    return cleaned


def glass_badge(label: str, tone: str = "primary") -> str:
    allowed_tones = {"primary", "emerald", "amber", "rose", "neutral"}
    safe_tone = tone if tone in allowed_tones else "primary"
    return f'<span class="lg-badge lg-badge--{safe_tone}">{esc(label)}</span>'


def glass_card(
    title: str,
    body: str,
    *,
    eyebrow: str = "",
    badge: str = "",
    tone: str = "primary",
    footer: str = "",
) -> str:
    parts = ['<div class="lg-card">']
    if eyebrow or badge:
        parts.append('<div class="lg-card__top">')
        if eyebrow:
            parts.append(f'<span class="lg-eyebrow">{esc(eyebrow)}</span>')
        if badge:
            parts.append(glass_badge(badge, tone=tone))
        parts.append("</div>")
    parts.append(f'<h3 class="lg-card__title">{esc(title)}</h3>')
    parts.append(f'<p class="lg-card__body">{esc(body)}</p>')
    if footer:
        parts.append(f'<div class="lg-card__footer">{esc(footer)}</div>')
    parts.append("</div>")
    return "".join(parts)


def glass_metric_row(metrics: Iterable[Mapping[str, object]]) -> str:
    items = []
    for item in metrics:
        label = esc(item.get("label", ""))
        value = esc(item.get("value", ""))
        delta = esc(item.get("delta", ""))
        delta_html = f'<span class="lg-kpi__delta">{delta}</span>' if delta else ""
        items.append(
            f'<div class="lg-kpi">'
            f'<span class="lg-kpi__label">{label}</span>'
            f'<span class="lg-kpi__value">{value}</span>'
            f'{delta_html}</div>'
        )
    return f'<div class="lg-kpi-grid">{"".join(items)}</div>'


def glass_hero(title: str, subtitle: str, *, badges: Iterable[str] = ()) -> str:
    badge_html = "".join(glass_badge(b, "primary") for b in badges)
    badges_wrap = f'<div class="lg-hero__badges">{badge_html}</div>' if badge_html else ""
    return (
        f'<section class="lg-hero">'
        f'{badges_wrap}'
        f'<h1 class="lg-hero__title">{esc(title)}</h1>'
        f'<p class="lg-hero__subtitle">{esc(subtitle)}</p>'
        f'</section>'
    )


def glass_progress_ring(percent: float, label: str = "") -> str:
    """Render a crisp inline SVG mastery ring."""
    pct = max(0.0, min(100.0, float(percent)))
    radius = 34
    circ = 2 * 3.14159265 * radius
    offset = circ * (1 - pct / 100.0)
    return (
        f'<div class="lg-ring" style="display:inline-flex;align-items:center;gap:12px;">'
        f'<svg width="84" height="84" viewBox="0 0 84 84" role="img" aria-label="{esc(label)} {int(pct)}%">'
        f'<circle cx="42" cy="42" r="{radius}" fill="none" stroke="rgba(148,163,184,0.25)" stroke-width="7"/>'
        f'<circle cx="42" cy="42" r="{radius}" fill="none" stroke="#2563EB" stroke-width="7" '
        f'stroke-linecap="round" stroke-dasharray="{circ:.2f}" stroke-dashoffset="{offset:.2f}" transform="rotate(-90 42 42)"/>'
        f'<text x="42" y="47" text-anchor="middle" font-size="16" font-weight="700" fill="currentColor">{int(pct)}%</text>'
        f'</svg>'
        f'<span>{esc(label)}</span></div>'
    )


def glass_mobile_dock(items: Iterable[Mapping[str, object]]) -> str:
    """Render a floating iOS-style Liquid Glass bottom dock visible on phones."""
    links = []
    for item in items:
        label = esc(item.get("label", ""))
        href = safe_url(str(item.get("href", "#")))
        active = " is-active" if item.get("active") else ""
        links.append(f'<a class="lg-mobile-dock__item{active}" href="{href}">{label}</a>')
    return f'<nav class="lg-mobile-dock" aria-label="Mobile Navigation">{"".join(links)}</nav>'
