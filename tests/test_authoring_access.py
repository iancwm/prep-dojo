from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute

from app.core.auth import (
    MENTOR_LIKE_ROLES,
    RequestAuthContext,
    get_request_auth_context,
    require_mentor_like_role,
)
from app.core.enums import UserRole
from app.main import app


def _get_route(path: str, method: str) -> APIRoute:
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == path and method in route.methods:
            return route
    raise AssertionError(f"Missing route for {method} {path}")


def _dependency_calls(path: str, method: str) -> list[object]:
    return [dependency.call for dependency in _get_route(path, method).dependant.dependencies]


def test_request_auth_context_defaults_to_student_and_parses_mentor_like_roles() -> None:
    default_context = get_request_auth_context()
    academic_context = get_request_auth_context("academic")
    career_context = get_request_auth_context(" CAREER ")
    admin_context = get_request_auth_context("admin")

    assert default_context == RequestAuthContext(role=UserRole.STUDENT, is_authenticated=False)
    assert academic_context.role == UserRole.ACADEMIC
    assert career_context.role == UserRole.CAREER
    assert admin_context.role == UserRole.ADMIN
    assert academic_context.is_authenticated
    assert career_context.is_mentor_like
    assert admin_context.is_mentor_like
    assert MENTOR_LIKE_ROLES == {UserRole.ACADEMIC, UserRole.CAREER, UserRole.ADMIN}

    with pytest.raises(HTTPException) as exc_info:
        get_request_auth_context("visitor")

    assert exc_info.value.status_code == 400


def test_mentor_guard_rejects_students_and_accepts_mentor_like_roles() -> None:
    with pytest.raises(HTTPException) as exc_info:
        require_mentor_like_role(RequestAuthContext(role=UserRole.STUDENT, is_authenticated=False))

    allowed_context = require_mentor_like_role(
        RequestAuthContext(role=UserRole.ACADEMIC, is_authenticated=True),
    )

    assert exc_info.value.status_code == 403
    assert allowed_context.role == UserRole.ACADEMIC


def test_authored_content_routes_include_mentor_guard() -> None:
    guarded_routes = [
        ("/api/v1/authored/topics", "POST"),
        ("/api/v1/authored/topics", "GET"),
        ("/api/v1/authored/topics/{topic_slug}", "PUT"),
        ("/api/v1/authored/topics/{topic_slug}/archive", "POST"),
        ("/api/v1/authored/concepts", "POST"),
        ("/api/v1/authored/concepts", "GET"),
        ("/api/v1/authored/concepts/{concept_slug}", "PUT"),
        ("/api/v1/authored/concepts/{concept_slug}/archive", "POST"),
        ("/api/v1/authored/questions", "POST"),
        ("/api/v1/authored/questions", "GET"),
        ("/api/v1/authored/questions/{question_id}", "GET"),
        ("/api/v1/authored/questions/{question_id}", "PUT"),
        ("/api/v1/authored/questions/{question_id}/status", "POST"),
    ]

    for path, method in guarded_routes:
        assert require_mentor_like_role in _dependency_calls(path, method)


def test_student_submission_routes_stay_open() -> None:
    open_routes = [
        ("/api/v1/authored/questions/{question_id}/submit", "POST"),
        ("/api/v1/reference/modules/valuation-enterprise-value/submit", "POST"),
        ("/api/v1/reference/questions/{question_external_id}/submit", "POST"),
    ]

    for path, method in open_routes:
        assert require_mentor_like_role not in _dependency_calls(path, method)
