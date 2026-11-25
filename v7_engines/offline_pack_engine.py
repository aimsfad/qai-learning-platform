"""Feature 9: Offline Study Pack Exporter (Self-Contained HTML Bundle)."""

from __future__ import annotations

import html
from typing import Mapping, Sequence


class OfflinePackEngine:
    """Exports an approved course into a zero-network self-contained HTML study pack."""

    def export_html(self, course_title: str, lessons: Sequence[Mapping[str, str]], locale: str = "ar") -> str:
        dir_attr = "rtl" if locale.startswith("ar") else "ltr"
        sections = []
        for idx, lesson in enumerate(lessons, 1):
            t = html.escape(lesson.get("title", f"Lesson {idx}"))
            b = html.escape(lesson.get("content", "")).replace("\n", "<br>")
            sections.append(f'<article class="card"><h2>{idx}. {t}</h2><p>{b}</p></article>')
        return f"""<!DOCTYPE html>
<html lang="{html.escape(locale)}" dir="{dir_attr}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(course_title)} — Offline Study Pack</title>
<style>
body{{margin:0;padding:24px;font-family:system-ui,sans-serif;background:#EEF3FA;color:#0B1324;line-height:1.75;}}
main{{max-width:860px;margin:auto;}}
.card{{background:#FFFFFF;border:1px solid #CBD5E1;border-radius:18px;padding:22px;margin-bottom:16px;}}
</style>
</head>
<body><main><h1>{html.escape(course_title)}</h1>{"".join(sections)}</main></body>
</html>"""
