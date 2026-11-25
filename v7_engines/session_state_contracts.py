"""Typed Session State Contract replacing ad-hoc session_state string keys."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppSessionState:
    locale: str = "ar"
    theme_mode: str = "liquid_glass_light"
    active_role: str = "student"
    active_course_id: str = ""
    active_lesson_id: str = ""
    attempt_gate_unlocked: bool = False
    voice_coach_enabled: bool = False
