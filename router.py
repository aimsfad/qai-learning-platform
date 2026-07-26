from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st


_PAGE_REGISTRY: Dict[str, Any] = {}


def route_key(role: str, page: str) -> str:
    return f"{role}:{page}"


def register_pages(pages: Dict[str, Any]) -> None:
    """Register all page objects created by the current app rerun."""
    _PAGE_REGISTRY.clear()
    _PAGE_REGISTRY.update(pages)


def queue(route: str) -> None:
    """Queue a route for the next rerun.

    This function is safe to use as a Streamlit widget callback because widget
    callbacks already trigger a rerun after returning.
    """
    st.session_state["_native_route_pending"] = route


def navigate(route: str) -> None:
    """Queue a route and rerun immediately from ordinary page code."""
    queue(route)
    st.rerun()


def navigate_student(page: str) -> None:
    st.session_state.role = "student"
    st.session_state.student_page = page
    navigate(route_key("student", page))


def navigate_evaluator(page: str) -> None:
    st.session_state.role = "evaluator"
    st.session_state.evaluator_page = page
    navigate(route_key("evaluator", page))


def navigate_public(page: str = "home") -> None:
    st.session_state.role = None
    navigate(route_key("public", page))


def process_pending_route() -> None:
    """Switch to a queued native Streamlit page after st.navigation is built."""
    pending: Optional[str] = st.session_state.pop("_native_route_pending", None)
    if not pending:
        return
    page = _PAGE_REGISTRY.get(pending)
    if page is None:
        # The target may be unavailable because permissions changed. Let the
        # current navigation default resolve safely instead of trapping users.
        return
    st.switch_page(page)
