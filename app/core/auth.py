from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.core.enums import UserRole

ROLE_HEADER = "X-User-Role"
MENTOR_LIKE_ROLES = {UserRole.ACADEMIC, UserRole.CAREER, UserRole.ADMIN}


@dataclass(frozen=True)
class RequestAuthContext:
    role: UserRole
    is_authenticated: bool

    @property
    def is_mentor_like(self) -> bool:
        return self.role in MENTOR_LIKE_ROLES


def get_request_auth_context(
    user_role: Annotated[str | None, Header(alias=ROLE_HEADER)] = None,
) -> RequestAuthContext:
    if user_role is None:
        return RequestAuthContext(role=UserRole.STUDENT, is_authenticated=False)

    normalized_role = user_role.strip().lower()
    try:
        role = UserRole(normalized_role)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported user role `{user_role}`.",
        ) from exc

    return RequestAuthContext(role=role, is_authenticated=True)


def require_mentor_like_role(
    context: RequestAuthContext = Depends(get_request_auth_context),
) -> RequestAuthContext:
    if not context.is_mentor_like:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mentor-like role required for authored content.",
        )
    return context
