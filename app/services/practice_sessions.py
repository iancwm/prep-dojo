from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import AttemptStatus, MasteryBand, UserRole
from app.core.settings import get_settings
from app.db.models import PracticeSession, User
from app.schemas.domain import (
    PracticeSessionAttemptSummary,
    PracticeSessionCreate,
    PracticeSessionListFilters,
    PracticeSessionRecord,
    PracticeSessionSummary,
)

settings = get_settings()


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
            status="created",
            config_json={"source": payload.source, "question_queue": payload.question_queue},
            question_queue_json=payload.question_queue,
        )
        session.add(practice_session)
        session.commit()
        session.refresh(practice_session)

    return _build_session_record(practice_session)


def list_practice_session_summaries(
    session: Session,
    filters: PracticeSessionListFilters | None = None,
) -> list[PracticeSessionSummary]:
    practice_sessions = session.scalars(
        select(PracticeSession).order_by(PracticeSession.started_at.desc())
    ).all()
    summaries = [
        PracticeSessionSummary(
            session_id=item.client_session_id,
            source=item.config_json.get("source", "practice-session"),
            status=_resolve_practice_session_status(item),
            question_queue=_get_practice_session_queue(item),
            queued_question_count=_queued_question_count(item),
            completed_question_count=_completed_question_count(item),
            remaining_question_count=_remaining_question_count(item),
            current_question_id=_current_question_id(item),
            started_at=item.started_at,
            completed_at=item.completed_at,
            attempt_count=len(item.attempts),
        )
        for item in practice_sessions
    ]

    if filters is None:
        return summaries

    return [
        item
        for item in summaries
        if (filters.status is None or item.status == filters.status)
        and (filters.source is None or item.source == filters.source)
        and (filters.started_after is None or _normalize_session_datetime(item.started_at) >= filters.started_after)
        and (filters.started_before is None or _normalize_session_datetime(item.started_at) <= filters.started_before)
        and (filters.current_question_id is None or item.current_question_id == filters.current_question_id)
        and (
            filters.has_remaining is None
            or (item.remaining_question_count > 0) == filters.has_remaining
        )
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
        status=_resolve_practice_session_status(practice_session),
        question_queue=_get_practice_session_queue(practice_session),
        queued_question_count=_queued_question_count(practice_session),
        completed_question_count=_completed_question_count(practice_session),
        remaining_question_count=_remaining_question_count(practice_session),
        current_question_id=_current_question_id(practice_session),
        started_at=practice_session.started_at,
        completed_at=practice_session.completed_at,
        attempts=attempts,
    )


def start_practice_session(session: Session, session_id: str) -> PracticeSessionRecord:
    practice_session = session.scalar(
        select(PracticeSession).where(PracticeSession.client_session_id == session_id)
    )
    if practice_session is None:
        raise HTTPException(status_code=404, detail="Unknown practice session.")
    if _resolve_practice_session_status(practice_session) == "completed":
        raise HTTPException(status_code=400, detail="Completed practice sessions cannot be restarted.")

    practice_session.status = "in_progress"
    session.commit()
    session.refresh(practice_session)
    return _build_session_record(practice_session)


def complete_practice_session(session: Session, session_id: str) -> PracticeSessionRecord:
    practice_session = session.scalar(
        select(PracticeSession).where(PracticeSession.client_session_id == session_id)
    )
    if practice_session is None:
        raise HTTPException(status_code=404, detail="Unknown practice session.")
    resolved_status = _resolve_practice_session_status(practice_session)
    if resolved_status == "completed":
        return _build_session_record(practice_session)
    if resolved_status == "created" and not practice_session.attempts:
        raise HTTPException(status_code=400, detail="Practice session must be started before completion.")

    practice_session.status = "completed"
    practice_session.completed_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(practice_session)
    return _build_session_record(practice_session)


def _get_or_create_reference_student(session: Session) -> User:
    user = session.scalar(select(User).where(User.email == settings.practice.reference_student_email))
    if user is None:
        user = User(role=UserRole.STUDENT.value, email=settings.practice.reference_student_email)
        session.add(user)
        session.flush()
    return user


def _get_practice_session_queue(practice_session: PracticeSession) -> list[str]:
    queue = practice_session.question_queue_json or practice_session.config_json.get("question_queue", [])
    return list(queue)


def _queued_question_count(practice_session: PracticeSession) -> int:
    return len(_get_practice_session_queue(practice_session))


def _completed_question_count(practice_session: PracticeSession) -> int:
    queue = _get_practice_session_queue(practice_session)
    if not queue:
        return len(practice_session.attempts)

    completed_question_ids: list[str] = []
    for attempt in sorted(practice_session.attempts, key=lambda item: item.submitted_at):
        question_identifier = attempt.question.external_id or str(attempt.question.id)
        if question_identifier in queue and question_identifier not in completed_question_ids:
            completed_question_ids.append(question_identifier)
    return len(completed_question_ids)


def _remaining_question_count(practice_session: PracticeSession) -> int:
    queue = _get_practice_session_queue(practice_session)
    return max(0, len(queue) - _completed_question_count(practice_session))


def _current_question_id(practice_session: PracticeSession) -> str | None:
    queue = _get_practice_session_queue(practice_session)
    if not queue:
        return None

    completed_question_ids: list[str] = []
    for attempt in sorted(practice_session.attempts, key=lambda item: item.submitted_at):
        question_identifier = attempt.question.external_id or str(attempt.question.id)
        if question_identifier in queue and question_identifier not in completed_question_ids:
            completed_question_ids.append(question_identifier)

    for question_identifier in queue:
        if question_identifier not in completed_question_ids:
            return question_identifier
    return None


def _resolve_practice_session_status(practice_session: PracticeSession) -> str:
    if practice_session.completed_at is not None:
        return "completed"

    if practice_session.status == "completed":
        return "completed"

    if _remaining_question_count(practice_session) == 0 and _queued_question_count(practice_session) > 0:
        return "completed"

    if practice_session.status == "in_progress":
        return "in_progress"

    if practice_session.attempts:
        return "in_progress"
    return "created"


def _normalize_session_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
