"""Static validation for the multilingual educational content.

Run with: python validate_multilingual.py
This script does not require Streamlit or a database.
"""
from __future__ import annotations

import content
import i18n

REQUIRED_LESSON_FIELDS = (
    "title", "short_title", "objective", "concept", "why_it_matters",
    "big_idea", "misconception", "mini_task", "check_question",
    "before_measurement", "after_measurement",
)
REQUIRED_LIST_FIELDS = ("visual_steps", "code_focus", "can_do")


def validate() -> None:
    for language in ("en", "ar", "fr"):
        lessons = content.lessons_for(language)
        pre = content.questions_for("pre", language)
        post = content.questions_for("post", language)
        assert len(lessons) == 6, (language, "lessons", len(lessons))
        assert len(pre) == 18, (language, "pre", len(pre))
        assert len(post) == 18, (language, "post", len(post))
        for lesson in lessons:
            for field in REQUIRED_LESSON_FIELDS:
                assert str(lesson.get(field, "")).strip(), (language, lesson["id"], field)
            for field in REQUIRED_LIST_FIELDS:
                assert lesson.get(field), (language, lesson["id"], field)
        for question in pre + post:
            assert question.question.strip(), (language, question.id, "question")
            assert len(question.options) == 4, (language, question.id, "options")
            assert 0 <= question.answer_index < 4, (language, question.id, "answer_index")
            assert question.explanation.strip(), (language, question.id, "explanation")
        assert content.survey_items_for(language)
        assert content.open_ended_items_for(language)

    assert i18n.translate("Explain a concept", "ar") != "Explain a concept"
    assert i18n.translate("Explain a concept", "fr") != "Explain a concept"
    print("Multilingual content validation passed: ar / fr / en")


if __name__ == "__main__":
    validate()
