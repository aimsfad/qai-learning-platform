"""Safe, teacher-friendly rendering helpers for generated lesson content.

The LLM is allowed to generate Markdown because it is a practical interchange
format, but the teacher workspace must never expose formatting noise,
placeholder ``None`` values, raw presentation HTML, or mixed-language
boilerplate. Persisted source content remains immutable; all cleanup here is a
presentation transformation.
"""
from __future__ import annotations

import re
from html import escape, unescape
from typing import Any, Dict, List, Sequence, Tuple


_PLACEHOLDER_LINE = re.compile(
    r"^\s*(?:[-*+]\s*)?(?:\*\*)?[^:\n]{0,60}(?::|：)\s*(?:\*\*)?\s*(?:none|null|n/?a|—|-)?\s*$",
    re.IGNORECASE,
)
_RAW_PLACEHOLDER = re.compile(r"(?<![\w.])(?:None|null)(?![\w.])", re.IGNORECASE)

# Only parse a deliberately small presentation subset. Arbitrary LLM HTML is
# never passed to Streamlit with unsafe_allow_html=True.
_DETAILS_RE = re.compile(
    r"<details\b[^>]*>\s*<summary\b[^>]*>(.*?)</summary>(.*?)</details>",
    re.IGNORECASE | re.DOTALL,
)
_FENCED_BLOCK_RE = re.compile(
    r"(?ms)(^\s*```[^\n]*\n.*?^\s*```\s*$)"
)

# Canonical bilingual labels occasionally emitted by models. We keep English
# fallbacks for non-Arabic interfaces but avoid duplicated headings in Arabic.
_AR_HEADING_REPLACEMENTS: Dict[str, str] = {
    "prior-knowledge activation": "تنشيط المعارف السابقة",
    "activation": "تنشيط المعارف السابقة",
    "concept explanation": "شرح المفهوم",
    "worked example": "مثال محلول",
    "attempt": "جرّب أولًا",
    "hints": "تلميحات",
    "solution": "الحل النموذجي",
    "teacher implementation note": "إرشادات للمعلم",
    "guided practice": "تدريب موجه",
    "independent practice": "تدريب مستقل",
    "misconceptions and remediation": "الأخطاء الشائعة ومعالجتها",
    "formative assessment": "تقويم تكويني",
    "lesson summary": "ملخص الدرس",
    "resources and follow-up": "موارد ومتابعة",
    "learning objectives": "الأهداف التعليمية",
    "self-check": "تحقق ذاتي",
    "reflection": "تأمل في التعلم",
    "case-study": "دراسة حالة",
    "case study": "دراسة حالة",
}


def _strip_placeholder_lines(lines: List[str]) -> List[str]:
    cleaned: List[str] = []
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            cleaned.append(line.rstrip())
            continue
        if not in_code and _PLACEHOLDER_LINE.match(line):
            continue
        cleaned.append(line.rstrip())
    return cleaned


def _normalise_arabic_heading(line: str) -> str:
    match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
    if not match:
        return line
    hashes, title = match.groups()
    plain = re.sub(r"[*_`]+", "", title).strip()
    lower = plain.lower()

    # Replace English parenthetical duplicates: "مثال محلول (Worked example)".
    for english, arabic in _AR_HEADING_REPLACEMENTS.items():
        if english in lower:
            arabic_present = any("\u0600" <= ch <= "\u06ff" for ch in plain)
            if arabic_present:
                plain = re.sub(
                    r"\s*[\(（]?\s*" + re.escape(english) + r"\s*[\)）]?",
                    "",
                    plain,
                    flags=re.I,
                ).strip(" -–—")
                return f"{hashes} {plain or arabic}"
            return f"{hashes} {arabic}"
    return f"{hashes} {plain}"


def _split_fenced_regions(text: str) -> List[Tuple[bool, str]]:
    """Split Markdown into fenced-code and prose regions, preserving order."""
    regions: List[Tuple[bool, str]] = []
    cursor = 0
    for match in _FENCED_BLOCK_RE.finditer(str(text or "")):
        if match.start() > cursor:
            regions.append((False, text[cursor:match.start()]))
        regions.append((True, match.group(0)))
        cursor = match.end()
    if cursor < len(text):
        regions.append((False, text[cursor:]))
    return regions or [(False, str(text or ""))]


def _clean_summary_label(value: str, language_code: str) -> str:
    label = unescape(str(value or ""))
    label = re.sub(r"<[^>]+>", " ", label)
    label = re.sub(r"[*_`#]+", "", label)
    label = re.sub(r"\s+", " ", label).strip(" -–—:؛")
    if not label:
        return {"ar": "عرض التفاصيل", "fr": "Afficher les détails", "en": "Show details"}.get(
            str(language_code or "en").lower(), "Show details"
        )
    return label[:120]


def _flatten_details_markup(text: str, language_code: str) -> str:
    def replace(match: re.Match[str]) -> str:
        label = _clean_summary_label(match.group(1), language_code)
        body = str(match.group(2) or "").strip()
        return f"\n\n#### {label}\n\n{body}\n\n"

    return _DETAILS_RE.sub(replace, str(text or ""))


def _convert_known_html_to_markdown(text: str) -> str:
    """Convert a conservative set of presentation tags to safe Markdown."""
    value = str(text or "")
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"</?(?:strong|b)\b[^>]*>", "**", value, flags=re.I)
    value = re.sub(r"</?(?:em|i)\b[^>]*>", "*", value, flags=re.I)
    value = re.sub(r"<li\b[^>]*>", "\n- ", value, flags=re.I)
    value = re.sub(r"</li\s*>", "", value, flags=re.I)
    value = re.sub(r"</?(?:p|div|section|article|ul|ol)\b[^>]*>", "\n", value, flags=re.I)
    # Strip leftover presentation HTML tags, but not arbitrary angle-bracket
    # expressions that do not look like HTML element names.
    value = re.sub(
        r"</?(?:details|summary|span|table|thead|tbody|tfoot|tr|td|th|blockquote)\b[^>]*>",
        "",
        value,
        flags=re.I,
    )
    return value


def _prepare_prose_markup(text: str, language_code: str) -> str:
    value = _flatten_details_markup(text, language_code)
    return _convert_known_html_to_markdown(value)


def normalize_generated_markdown(text: str, language_code: str = "ar") -> str:
    """Return display-safe Markdown without mutating the persisted source.

    Raw presentation HTML emitted by the model is converted to Markdown only
    outside fenced code blocks. ``<details>`` becomes a readable subsection for
    downloads/general previews; the simple lesson workspace may render the
    same disclosure as a native Streamlit expander via
    :func:`teacher_markdown_segments`.
    """
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    raw = raw.replace("\u200f", "").replace("\u200e", "").replace("\ufeff", "")

    prepared_parts: List[str] = []
    for is_code, region in _split_fenced_regions(raw):
        prepared_parts.append(region if is_code else _prepare_prose_markup(region, language_code))
    raw = "".join(prepared_parts)

    lines = _strip_placeholder_lines(raw.split("\n"))
    lang = str(language_code or "").lower()
    output: List[str] = []
    in_code = False
    blank_pending = False

    for original in lines:
        line = original.rstrip()
        if line.strip().startswith("```"):
            in_code = not in_code
            output.append(line)
            blank_pending = False
            continue
        if not in_code:
            if lang.startswith("ar"):
                line = _normalise_arabic_heading(line)
            # Remove isolated placeholder tokens from prose while preserving
            # programming identifiers such as None inside fenced code blocks.
            line = _RAW_PLACEHOLDER.sub("", line)
            line = re.sub(r"\*{2}\s*\*{2}", "", line)
            line = re.sub(r"[ \t]+$", "", line)
        if not line.strip():
            if output and not blank_pending:
                output.append("")
                blank_pending = True
            continue
        output.append(line)
        blank_pending = False

    # Repair an unclosed code fence for display so the remainder of the page
    # does not become a single code block. Validation separately flags it.
    if in_code:
        output.append("```")
    return "\n".join(output).strip()


def teacher_markdown_segments(text: str, language_code: str = "ar") -> List[Dict[str, str]]:
    """Parse model Markdown into safe teacher-display segments.

    The only interactive HTML pattern recognized is ``details/summary``. It is
    converted to a semantic ``disclosure`` segment. All content is normalized
    before rendering, and callers should pass it to ``st.markdown`` with the
    default ``unsafe_allow_html=False``.
    """
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    raw = raw.replace("\u200f", "").replace("\u200e", "").replace("\ufeff", "")
    segments: List[Dict[str, str]] = []

    def add_markdown(value: str) -> None:
        cleaned = normalize_generated_markdown(value, language_code)
        if not cleaned:
            return
        if segments and segments[-1].get("kind") == "markdown":
            segments[-1]["text"] = (segments[-1].get("text", "") + "\n\n" + cleaned).strip()
        else:
            segments.append({"kind": "markdown", "text": cleaned})

    for is_code, region in _split_fenced_regions(raw):
        if is_code:
            add_markdown(region)
            continue
        cursor = 0
        for match in _DETAILS_RE.finditer(region):
            add_markdown(region[cursor:match.start()])
            label = _clean_summary_label(match.group(1), language_code)
            body = normalize_generated_markdown(match.group(2), language_code)
            if body:
                segments.append({"kind": "disclosure", "label": label, "text": body})
            cursor = match.end()
        add_markdown(region[cursor:])

    return segments


def markdown_has_unclosed_fence(text: str) -> bool:
    return len(re.findall(r"(?m)^\s*```", str(text or ""))) % 2 == 1


def content_has_placeholder(text: str) -> bool:
    raw = str(text or "")
    in_code = False
    for line in raw.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if not in_code and (_PLACEHOLDER_LINE.match(line) or _RAW_PLACEHOLDER.search(line)):
            return True
    return False


def lesson_section_nav_html(rows: List[Dict[str, object]], language_code: str = "ar") -> str:
    """Return a compact, non-click navigation strip for the current lesson."""
    chips: List[str] = []
    for row in rows:
        state = "approved" if row.get("approved") else ("ready" if row.get("run") else "pending")
        label = escape(str(row.get("label") or row.get("block_type") or ""))
        index = int(row.get("index") or 0)
        chips.append(
            f"<span class='v6185-section-chip {state}' title='{label}' aria-label='{index:02d} {label}'>"
            f"<b>{index:02d}</b><em>{label}</em></span>"
        )
    direction = "rtl" if str(language_code).lower().startswith("ar") else "ltr"
    return f"<div class='v6185-section-nav' dir='{direction}'>" + "".join(chips) + "</div>"


_QUALITY_ISSUES: Dict[str, Dict[str, str]] = {
    "content_is_short": {"ar": "المحتوى أقصر من النطاق المقترح", "fr": "Contenu plus court que prévu", "en": "Content is shorter than the suggested range"},
    "missing_markdown_heading": {"ar": "يحتاج إلى تنظيم أوضح للعناوين", "fr": "La structure des titres peut être améliorée", "en": "Heading structure can be improved"},
    "placeholder_value_detected": {"ar": "توجد قيمة فارغة أو مؤقتة يجب مراجعتها", "fr": "Une valeur vide ou provisoire doit être vérifiée", "en": "A placeholder or empty value needs review"},
    "worked_example_missing_attempt": {"ar": "المثال يحتاج محاولة للمتعلم قبل الحل", "fr": "L’exemple doit inviter l’apprenant à essayer avant la solution", "en": "Worked example needs a learner attempt before the solution"},
    "worked_example_missing_hints": {"ar": "المثال يحتاج تلميحات متدرجة", "fr": "L’exemple a besoin d’indices progressifs", "en": "Worked example needs graduated hints"},
    "worked_example_missing_solution": {"ar": "الحل النموذجي غير واضح", "fr": "La solution modèle n’est pas clairement identifiée", "en": "The worked solution is not clearly identified"},
    "activation_missing_retrieval_prompt": {"ar": "التنشيط يحتاج سؤال استرجاع أو توقع", "fr": "L’activation nécessite une question de rappel ou de prédiction", "en": "Activation needs a retrieval or prediction prompt"},
    "assessment_missing_feedback_or_criterion": {"ar": "التقويم يحتاج معيار نجاح أو تغذية راجعة قابلة للتنفيذ", "fr": "L’évaluation a besoin d’un critère ou d’un feedback exploitable", "en": "Assessment needs a success criterion or actionable feedback"},
    "summary_missing_metacognitive_reflection": {"ar": "الملخص يحتاج تأملًا قصيرًا في التعلم", "fr": "La synthèse devrait inclure une brève réflexion métacognitive", "en": "Summary needs a short metacognitive reflection"},
    "unclosed_code_fence": {"ar": "كتلة كود غير مغلقة", "fr": "Bloc de code non fermé", "en": "Unclosed code block"},
    "empty_content": {"ar": "المحتوى فارغ", "fr": "Le contenu est vide", "en": "Content is empty"},
    "lesson_identity_source_pollution": {"ar": "هوية الدرس مشتقة من اسم مصدر مرجعي وتحتاج إعادة بناء الخطة", "fr": "L’identité de la leçon provient d’un titre de source et le plan doit être reconstruit", "en": "Lesson identity is derived from a reference-source title and the plan must be rebuilt"},
}


def quality_issue_label(code: str, language_code: str = "ar") -> str:
    raw = str(code or "")
    key = raw.split(":", 1)[0]
    lang = str(language_code or "en").lower()
    lang = "ar" if lang.startswith("ar") else ("fr" if lang.startswith("fr") else "en")
    item = _QUALITY_ISSUES.get(key)
    if item:
        return item.get(lang) or item.get("en") or raw
    return raw.replace("_", " ")
