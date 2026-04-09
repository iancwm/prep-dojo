from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import AttemptStatus, MasteryBand, UserRole
from app.db.models import PracticeSession, User
from app.schemas.domain import (
    PracticeSessionAttemptSummary,
    PracticeSessionCreate,
    PracticeSessionRecord,
    PracticeSessionSummary,
)
from app.services.persistence import REFERENCE_STUDENT_EMAIL


def create_practice_session_record(session: Session, payload: PracticeSessionCreate) -> PracticeSessionRecord:
    user = _get_or_create_reference_student(session)
    client_session_id = payload.session_id or str(uuid.uuid4())
    practice_session = session.scalar(
        select(PracticeSession).where(PracticeSession.client_session_id == client_session_id)
    )
    if practice_session is None:
        practice_session = PracticeSession(
            user_id=user.id,
            client_session_id=client_session_id,
            config_json={"source": payload.source},
        )
        session.add(practice_session)
        session.commit()
        session.refresh(practice_session)

    return _build_session_record(practice_session)


def list_practice_session_summaries(session: Session) -> list[PracticeSessionSummary]:
    practice_sessions = session.scalars(
        select(PracticeSession).order_by(PracticeSession.started_at.desc())
    ).all()
    return [
        PracticeSessionSummary(
            session_id=item.client_session_id,
            source=item.config_json.get("source", "practice-session"),
            started_at=item.started_at,
            completed_at=item.completed_at,
            attempt_count=len(item.attempts),
        )
        for item in practice_sessions
    ]


def get_practice_session_record(session: Session, session_id: str) -> PracticeSessionRecord:
    practice_session = session.scalar(
        select(PracticeSession).where(PracticeSession.client_session_id == session_id)
    )
    if practice_session is None:
        raise HTTPException(status_code=404, detail="Unknown practice session.")
    return _build_session_record(practice_session)


def _build_session_record(practice_session: PracticeSession) -> PracticeSessionRecord:
    attempts = []
    for attempt in sorted(practice_session.attempts, key=lambda item: item.submitted_at):
        question_identifier = attempt.question.external_id or str(attempt.question.id)
        mastery_band = MasteryBand(attempt.score.mastery_band) if attempt.score is not None else None
        attempts.append(
            PracticeSessionAttemptSummary(
                attempt_id=str(attempt.id),
                question_id=question_identifier,
                prompt=attempt.question.prompt,
                response_type=attempt.response_json["response_type"],
                status=AttemptStatus(attempt.status),
                submitted_at=attempt.submitted_at,
                overall_score=attempt.score.overall_score if attempt.score is not None else None,
                mastery_band=mastery_band,
            )
        )

    return PracticeSessionRecord(
        session_id=practice_session.client_session_id,
        user_id=str(practice_session.user_id),
        source=practice_session.config_json.get("source", "practice-session"),
        started_at=practice_session.started_at,
        completed_at=practice_session.completed_at,
        attempts=attempts,
    )


def _get_or_create_reference_student(session: Session) -> User:
    user = session.scalar(select(User).where(User.email == REFERENCE_STUDENT_EMAIL))
    if user is None:
        user = User(role=UserRole.STUDENT.value, email=REFERENCE_STUDENT_EMAIL)
        session.add(user)
        session.flush()
    return user
