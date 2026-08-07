"""Pedagogical orchestration rules for 3alimnIA lesson generation.

V6.18.5 keeps the LLM as a pedagogical co-designer rather than a free-form
content writer.  The rules in this module are deterministic, inspectable and
shared by generation, validation and the teacher UI.

The policy operationalises a small set of well-supported learning principles:
retrieval of prior knowledge, explicit explanation with manageable cognitive
load, worked examples followed by guided and independent practice, formative
feedback, metacognitive reflection, and teacher approval before publication.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List


PEDAGOGICAL_PRINCIPLES: List[Dict[str, str]] = [
    {
        "key": "learner_agency",
        "label_ar": "فاعلية المتعلم",
        "label_en": "Learner agency",
        "description": "Require an attempt, prediction, explanation or decision before revealing complete answers when appropriate.",
    },
    {
        "key": "retrieval",
        "label_ar": "الاسترجاع النشط",
        "label_en": "Retrieval practice",
        "description": "Reconnect the new idea to prior knowledge through active recall rather than passive rereading.",
    },
    {
        "key": "scaffolding",
        "label_ar": "التدرج في الدعم",
        "label_en": "Scaffolding",
        "description": "Move from modelling to guided practice to independent performance, fading support progressively.",
    },
    {
        "key": "formative_feedback",
        "label_ar": "التقويم والتغذية الراجعة",
        "label_en": "Formative feedback",
        "description": "Elicit evidence of understanding and provide actionable feedback linked to the success criterion.",
    },
    {
        "key": "metacognition",
        "label_ar": "ما وراء المعرفة",
        "label_en": "Metacognition",
        "description": "Prompt learners to plan, monitor or evaluate their learning at suitable points in the lesson.",
    },
    {
        "key": "human_oversight",
        "label_ar": "إشراف الأستاذ",
        "label_en": "Human oversight",
        "description": "AI drafts and adapts; the teacher reviews, edits and approves pedagogical decisions.",
    },
]


BLOCK_PEDAGOGY: Dict[str, Dict[str, Any]] = {
    "activation": {
        "purpose_ar": "استدعاء المعرفة السابقة وكشف نقطة البداية قبل تقديم المحتوى الجديد.",
        "purpose_en": "Activate prior knowledge and expose the learner's starting point before new instruction.",
        "principles": ["retrieval", "learner_agency"],
        "requirements": [
            "Start with 1-3 short recall/prediction prompts before explanations.",
            "Do not reveal the new lesson answer inside the activation task.",
            "Include one teacher cue for interpreting likely learner responses.",
        ],
    },
    "explanation": {
        "purpose_ar": "بناء نموذج ذهني واضح للمفهوم مع تقليل الحمل المعرفي غير الضروري.",
        "purpose_en": "Build a clear mental model while controlling unnecessary cognitive load.",
        "principles": ["scaffolding"],
        "requirements": [
            "Explain one conceptual step at a time and connect it explicitly to prerequisites.",
            "Use a concrete example or representation before adding complexity.",
            "Flag one likely misconception and contrast it with the correct idea.",
            "Avoid decorative detail that does not support the learning outcome.",
        ],
    },
    "worked_example": {
        "purpose_ar": "نمذجة الحل مع إبقاء المتعلم نشطًا قبل كشف الحل الكامل.",
        "purpose_en": "Model a solution while keeping the learner cognitively active before full reveal.",
        "principles": ["learner_agency", "scaffolding"],
        "requirements": [
            "Use an attempt-first sequence: task -> learner attempt -> graduated hints -> worked solution -> self-check.",
            "Explain why each important step is taken, not only what to type or calculate.",
            "If code is included, provide syntactically coherent code fences and a small expected result when useful.",
            "End with one near-transfer question that changes a meaningful feature of the example.",
        ],
    },
    "guided_practice": {
        "purpose_ar": "تطبيق موجّه مع تقليل الدعم تدريجيًا بناءً على أداء المتعلم.",
        "purpose_en": "Guided application with support that can be faded as competence grows.",
        "principles": ["scaffolding", "formative_feedback", "learner_agency"],
        "requirements": [
            "Provide a task before the answer and use hints from general to specific.",
            "Include checkpoints where the learner explains a decision or predicts an output.",
            "Include concise feedback for a correct response and for one common error.",
        ],
    },
    "independent_practice": {
        "purpose_ar": "التحقق من قدرة المتعلم على الأداء باستقلالية ونقل التعلم إلى حالة جديدة.",
        "purpose_en": "Check independent performance and transfer to a fresh but aligned problem.",
        "principles": ["learner_agency", "retrieval"],
        "requirements": [
            "Give the task without step-by-step solution scaffolds in the main prompt.",
            "State an observable success criterion.",
            "Include a separate self-check or answer key after a clear divider, not before the attempt.",
        ],
    },
    "misconceptions": {
        "purpose_ar": "تشخيص الأخطاء الشائعة وتصحيح النموذج الذهني بدل الاكتفاء بإظهار الإجابة الصحيحة.",
        "purpose_en": "Diagnose common misconceptions and repair the mental model rather than only showing the answer.",
        "principles": ["formative_feedback", "metacognition"],
        "requirements": [
            "For each misconception, show the tempting incorrect reasoning and the diagnostic cue.",
            "Explain the conceptual correction and include a short check that discriminates the two ideas.",
        ],
    },
    "formative_assessment": {
        "purpose_ar": "جمع دليل سريع عن الفهم واستخدامه لاتخاذ قرار تعليمي تالٍ.",
        "purpose_en": "Elicit evidence of understanding and use it to decide the next instructional move.",
        "principles": ["formative_feedback", "retrieval", "metacognition"],
        "requirements": [
            "Align every item to an explicit lesson outcome or success criterion.",
            "Mix at least two response types when appropriate (e.g. explain, predict, apply, debug).",
            "Provide answer guidance plus actionable feedback, not only right/wrong labels.",
            "Include a teacher decision rule: reteach, give another example, or progress.",
        ],
    },
    "summary": {
        "purpose_ar": "تثبيت البنية المفاهيمية ودفع المتعلم إلى تقييم ما أتقنه وما يحتاج إلى مراجعته.",
        "purpose_en": "Consolidate the conceptual structure and prompt the learner to evaluate what is mastered or still uncertain.",
        "principles": ["retrieval", "metacognition"],
        "requirements": [
            "Prefer a short retrieval summary over a long restatement.",
            "End with a learner reflection: what can I now do, what remains unclear, what will I practise next?",
        ],
    },
    "resources": {
        "purpose_ar": "توجيه المتابعة والتمرين اللاحق دون إغراق المتعلم بمصادر غير مبررة.",
        "purpose_en": "Guide follow-up study and practice without overwhelming the learner with unprioritised resources.",
        "principles": ["metacognition", "human_oversight"],
        "requirements": [
            "Prioritise resources already approved for the lesson.",
            "Explain the learning purpose of each recommended follow-up activity.",
            "Offer a simple next-step choice for learners who need reinforcement versus extension.",
        ],
    },
}


LANGUAGE_POLICY = {
    "ar": (
        "Write learner-facing prose and headings in Arabic. Keep programming identifiers, code, standard library names, "
        "source markers, and unavoidable technical tokens in their canonical form. Do not duplicate every heading in English."
    ),
    "fr": "Write learner-facing prose and headings in French; keep code and canonical technical tokens unchanged.",
    "en": "Write learner-facing prose and headings in English.",
}


def language_key(language: str) -> str:
    value = str(language or "").strip().lower()
    if value.startswith("ar") or "arab" in value or "العرب" in value:
        return "ar"
    if value.startswith("fr") or "french" in value or "fran" in value:
        return "fr"
    return "en"


def principles_for_block(block_type: str) -> List[Dict[str, str]]:
    keys = list((BLOCK_PEDAGOGY.get(str(block_type)) or {}).get("principles") or [])
    by_key = {item["key"]: item for item in PEDAGOGICAL_PRINCIPLES}
    return [by_key[key] for key in keys if key in by_key]


def prompt_contract(block_type: str, language: str) -> str:
    """Return a compact, explicit pedagogical contract for the LLM prompt."""
    block = BLOCK_PEDAGOGY.get(str(block_type)) or {}
    lang = language_key(language)
    purpose = str(block.get(f"purpose_{lang}") or block.get("purpose_en") or "")
    requirements = list(block.get("requirements") or [])
    principle_names = ", ".join(item["label_en"] for item in principles_for_block(block_type)) or "evidence-aligned instruction"
    requirement_text = "\n".join(f"- {item}" for item in requirements) or "- Keep the block aligned to the approved learning outcomes."
    return f"""<pedagogical_contract>
Purpose: {purpose}
Learning-science emphasis: {principle_names}
Language policy: {LANGUAGE_POLICY[lang]}
Required design moves:
{requirement_text}

AI role boundaries:
- Act as a pedagogical co-designer, not an autonomous teacher and not an answer vending machine.
- Preserve learner thinking time; do not collapse attempt, hint and solution into one step.
- The teacher remains the final reviewer and approver of instructional content.
- Never claim that a pedagogical choice is universally optimal; adapt to the supplied learners and lesson context.
</pedagogical_contract>""".strip()


def lesson_design_summary(language_code: str = "ar") -> List[str]:
    lang = language_key(language_code)
    return [str(item.get(f"label_{lang}") or item.get("label_en")) for item in PEDAGOGICAL_PRINCIPLES[:5]]


def pedagogical_rationale(block_type: str, language_code: str = "ar") -> str:
    block = BLOCK_PEDAGOGY.get(str(block_type)) or {}
    lang = language_key(language_code)
    return str(block.get(f"purpose_{lang}") or block.get("purpose_en") or "")
