"""Multi-Tenant Role-Based Access Control (RBAC) & Audit Trail for 3alimnIA V7.0."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Set


class Role(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    REVIEWER = "reviewer"
    EVALUATOR = "evaluator"
    INSTITUTION_ADMIN = "institution_admin"


class Permission(str, Enum):
    VIEW_PUBLISHED_COURSE = "view_published_course"
    AUTHOR_COURSE = "author_course"
    APPROVE_COURSE = "approve_course"
    PUBLISH_COURSE = "publish_course"
    EXPORT_RESEARCH = "export_research"
    MANAGE_TENANT = "manage_tenant"


_ROLE_MATRIX: Dict[Role, Set[Permission]] = {
    Role.STUDENT: {Permission.VIEW_PUBLISHED_COURSE},
    Role.TEACHER: {Permission.VIEW_PUBLISHED_COURSE, Permission.AUTHOR_COURSE, Permission.PUBLISH_COURSE},
    Role.REVIEWER: {Permission.VIEW_PUBLISHED_COURSE, Permission.APPROVE_COURSE},
    Role.EVALUATOR: {Permission.VIEW_PUBLISHED_COURSE, Permission.EXPORT_RESEARCH},
    Role.INSTITUTION_ADMIN: set(Permission),
}


class RBACEngine:
    def can(self, role: Role | str, permission: Permission) -> bool:
        resolved = role if isinstance(role, Role) else Role(str(role).lower())
        return permission in _ROLE_MATRIX.get(resolved, set())
