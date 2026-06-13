from __future__ import annotations

from typing import Optional, TypedDict
import streamlit as st

class AppState(TypedDict, total=False):
    role: Optional[str]
    student_id: Optional[int]
    evaluator_id: Optional[int]
    student_page: str
    evaluator_page: str
    current_lesson_id: str
    chat_history: list[dict[str, str]]

DEFAULTS = {
    "role": None,
    "student_id": None,
    "evaluator_id": None,
    "student_page": "Student Dashboard",
    "evaluator_page": "Evaluator Dashboard",
    "chat_history": [],
}

def ensure_state() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value.copy() if isinstance(value, list) else value)

def reset_chat() -> None:
    st.session_state["chat_history"] = []
