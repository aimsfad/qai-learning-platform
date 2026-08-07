"""Global visual design helpers for 3alimnIA.

V6.18 centralizes premium page headers, KPI cards, action cards, section
introductions, and Plotly styling so the public, learner, evaluator, and teacher
workspaces share one coherent design language.
"""

from __future__ import annotations

from html import escape
from typing import Any, Iterable, Sequence

try:
    import streamlit as st
except ModuleNotFoundError:  # Static validation can still import this module.
    st = None  # type: ignore[assignment]


ROLE_VISUALS = {
    "public": {"icon": "auto_awesome", "class": "public"},
    "student": {"icon": "school", "class": "student"},
    "teacher": {"icon": "edit_note", "class": "teacher"},
    "evaluator": {"icon": "analytics", "class": "evaluator"},
}


def _streamlit():
    global st
    if st is None:
        import importlib

        st = importlib.import_module("streamlit")
    return st


def direction(lang: str) -> str:
    return "rtl" if str(lang).lower().startswith("ar") else "ltr"


def _chips_html(items: Iterable[str]) -> str:
    chips = []
    for item in items:
        text = str(item or "").strip()
        if text:
            chips.append(f"<span class='v618-meta-chip'>{escape(text)}</span>")
    return "".join(chips)


def render_role_marker(role: str) -> None:
    """Emit a hidden role marker used only for safe, scoped CSS styling.

    This does not change routing, state, database access, or business logic.
    """
    api = _streamlit()
    role_key = str(role or "public").strip().lower()
    if role_key not in ROLE_VISUALS:
        role_key = "public"
    api.markdown(
        f"<span class='v6186-role-marker v6186-role-{escape(role_key)}' aria-hidden='true'></span>",
        unsafe_allow_html=True,
    )


def status_badge_html(label: str, *, tone: str = "muted", icon: str = "") -> str:
    """Return a semantic status badge that never relies on color alone."""
    safe_tone = str(tone or "muted").strip().lower()
    if safe_tone not in {"success", "active", "warning", "danger", "muted"}:
        safe_tone = "muted"
    icon_html = (
        f"<span class='material-symbols-rounded' aria-hidden='true'>{escape(str(icon))}</span>"
        if str(icon).strip()
        else "<span class='v6186-status-dot' aria-hidden='true'></span>"
    )
    return (
        f"<span class='v6186-status-badge v6186-status-{safe_tone}'>"
        f"{icon_html}<span>{escape(str(label))}</span></span>"
    )


def render_page_header(
    title: str,
    subtitle: str = "",
    *,
    lang: str = "en",
    eyebrow: str = "3alimnIA",
    status: str = "",
    meta: Sequence[str] | None = None,
    compact: bool = False,
    icon: str = "",
    role: str = "",
) -> None:
    """Render the canonical page heading used across every workspace."""

    api = _streamlit()
    dir_value = direction(lang)
    compact_class = " v618-page-header-compact" if compact else ""
    role_key = str(role or "").strip().lower()
    role_class = f" v618-role-header-{role_key}" if role_key in ROLE_VISUALS else ""
    status_html = (
        f"<span class='v618-page-status'>{escape(str(status))}</span>" if str(status).strip() else ""
    )
    icon_html = (
        f"<span class='material-symbols-rounded v618-page-icon' aria-hidden='true'>{escape(str(icon))}</span>"
        if str(icon).strip()
        else ""
    )
    chips = _chips_html(meta or [])
    meta_html = f"<div class='v618-page-meta'>{chips}</div>" if chips else ""
    subtitle_html = f"<p>{escape(str(subtitle))}</p>" if str(subtitle).strip() else ""
    # Keep the complete HTML tree in a single Markdown payload without leading
    # indentation. Streamlit can otherwise interpret a detached closing tag as
    # a Markdown code block after a rerun, which previously exposed ``</div>``
    # inside the teacher workspace header.
    header_html = (
        f'<section class="qai-hero v4-page-hero v618-page-header{compact_class}{role_class}" dir="{dir_value}">'
        '<div class="v618-page-header-accent" aria-hidden="true"></div>'
        '<div class="v618-page-header-row">'
        '<div class="v618-page-header-copy">'
        f'<div class="v618-page-eyebrow">{icon_html}<span>{escape(str(eyebrow))}</span>{status_html}</div>'
        f'<h1>{escape(str(title))}</h1>'
        f'{subtitle_html}{meta_html}'
        '</div></div></section>'
    )
    api.markdown(header_html, unsafe_allow_html=True)


def render_section_header(
    title: str,
    subtitle: str = "",
    *,
    lang: str = "en",
    eyebrow: str = "",
) -> None:
    api = _streamlit()
    dir_value = direction(lang)
    eyebrow_html = f"<span>{escape(str(eyebrow))}</span>" if str(eyebrow).strip() else ""
    subtitle_html = f"<p>{escape(str(subtitle))}</p>" if str(subtitle).strip() else ""
    api.markdown(
        f"<div class='v618-section-head' dir='{dir_value}'>{eyebrow_html}<h2>{escape(str(title))}</h2>{subtitle_html}</div>",
        unsafe_allow_html=True,
    )


def render_kpi_card(
    label: str,
    value: Any,
    *,
    unit: str = "",
    caption: str = "",
    trend: str = "",
    lang: str = "en",
    tone: str = "primary",
) -> None:
    """Render a consistent KPI card with isolated LTR number flow."""

    api = _streamlit()
    dir_value = direction(lang)
    unit_html = f"<span class='v618-kpi-unit'>{escape(str(unit))}</span>" if str(unit).strip() else ""
    caption_html = f"<div class='v618-kpi-caption'>{escape(str(caption))}</div>" if str(caption).strip() else ""
    trend_html = f"<span class='v618-kpi-trend'>{escape(str(trend))}</span>" if str(trend).strip() else ""
    api.markdown(
        f"""
        <article class="v618-kpi-card v618-kpi-{escape(str(tone))}" dir="{dir_value}">
          <div class="v618-kpi-top"><span class="v618-kpi-label">{escape(str(label))}</span>{trend_html}</div>
          <div class="v618-kpi-value-row" dir="ltr"><strong>{escape(str(value))}</strong>{unit_html}</div>
          {caption_html}
        </article>
        """,
        unsafe_allow_html=True,
    )


def action_card_html(
    index: str,
    title: str,
    description: str,
    *,
    lang: str = "en",
    icon: str = "arrow_forward",
) -> str:
    dir_value = direction(lang)
    return (
        f"<article class='v618-action-card' dir='{dir_value}'>"
        f"<div class='v618-action-top'><span class='v618-action-index'>{escape(str(index))}</span>"
        f"<span class='material-symbols-rounded' aria-hidden='true'>{escape(str(icon))}</span></div>"
        f"<h3>{escape(str(title))}</h3><p>{escape(str(description))}</p></article>"
    )


def apply_plotly_theme(
    fig: Any,
    *,
    x_title: str = "",
    y_title: str = "",
    show_legend: bool = True,
    height: int | None = None,
) -> Any:
    """Apply the shared transparent academic-dashboard Plotly theme."""

    layout: dict[str, Any] = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Tajawal, Arial, sans-serif", "color": "#334155"},
        "margin": {"l": 24, "r": 16, "t": 24, "b": 34},
        "hoverlabel": {"bgcolor": "#0B2F78", "font_color": "#FFFFFF", "bordercolor": "#0B2F78"},
        "showlegend": show_legend,
        "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    }
    if height:
        layout["height"] = int(height)
    fig.update_layout(**layout)
    fig.update_xaxes(
        title=x_title,
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor="#D9E4F1",
        tickcolor="#D9E4F1",
        automargin=True,
    )
    fig.update_yaxes(
        title=y_title,
        showgrid=True,
        gridcolor="rgba(148,163,184,.17)",
        griddash="dot",
        zeroline=False,
        showline=False,
        automargin=True,
    )
    return fig


def render_inline_notice(title: str, body: str, *, lang: str = "en", tone: str = "info") -> None:
    api = _streamlit()
    api.markdown(
        f"<aside class='v618-inline-notice v618-inline-{escape(str(tone))}' dir='{direction(lang)}'>"
        f"<strong>{escape(str(title))}</strong><span>{escape(str(body))}</span></aside>",
        unsafe_allow_html=True,
    )
