from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, Uuid, cast, event, func, select, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import inspect, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.session import engine as default_engine

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    concepts: Mapped[list["Concept"]] = relationship(back_populates="topic")


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topics.id"), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    prerequisites_json: Mapped[list[str]] = mapped_column(JSON_TYPE, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    topic: Mapped["Topic"] = relationship(back_populates="concepts")
    questions: Mapped[list["Question"]] = relationship(back_populates="concept")


class AssessmentMode(Base):
    __tablename__ = "assessment_modes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    scoring_style: Mapped[str] = mapped_column(String(20), nullable=False)
    timing_style: Mapped[str] = mapped_column(String(20), nullable=False)

    questions: Mapped[list["Question"]] = relationship(back_populates="assessment_mode")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("concepts.id"), nullable=False)
    assessment_mode_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment_modes.id"), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    author_type: Mapped[str] = mapped_column(String(20), nullable=False, default="human")
    author_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payload_json: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False)
    last_status_transition_actor_role: Mapped[str | None] = mapped_column(String(20))
    last_status_transition_reason: Mapped[str | None] = mapped_column(Text)
    last_status_transition_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    concept: Mapped["Concept"] = relationship(back_populates="questions")
    assessment_mode: Mapped["AssessmentMode"] = relationship(back_populates="questions")
    rubric: Mapped["Rubric"] = relationship(back_populates="question", uselist=False)
    expected_answer: Mapped["ExpectedAnswer"] = relationship(back_populates="question", uselist=False)
    common_mistakes: Mapped[list["CommonMistake"]] = relationship(back_populates="question")
    attempts: Mapped[list["StudentAttempt"]] = relationship(back_populates="question")


class Rubric(Base):
    __tablename__ = "rubrics"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id"), nullable=False, unique=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    criteria_json: Mapped[list[dict]] = mapped_column(JSON_TYPE, nullable=False)
    thresholds_json: Mapped[list[dict]] = mapped_column(JSON_TYPE, nullable=False)
    scoring_style: Mapped[str] = mapped_column(String(20), nullable=False)
    review_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    question: Mapped["Question"] = relationship(back_populates="rubric")


class ExpectedAnswer(Base):
    __tablename__ = "expected_answers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id"), nullable=False, unique=True)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_outline_json: Mapped[list[str]] = mapped_column(JSON_TYPE, nullable=False, default=list)
    key_points_json: Mapped[list[str]] = mapped_column(JSON_TYPE, nullable=False, default=list)
    acceptable_variants_json: Mapped[list[str]] = mapped_column(JSON_TYPE, nullable=False, default=list)

    question: Mapped["Question"] = relationship(back_populates="expected_answer")


class CommonMistake(Base):
    __tablename__ = "common_mistakes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id"), nullable=False)
    mistake_text: Mapped[str] = mapped_column(Text, nullable=False)
    why_it_is_wrong: Mapped[str] = mapped_column(Text, nullable=False)
    remediation_hint: Mapped[str] = mapped_column(Text, nullable=False)

    question: Mapped["Question"] = relationship(back_populates="common_mistakes")


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    client_session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    config_json: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    question_queue_json: Mapped[list[str]] = mapped_column(JSON_TYPE, nullable=False, default=list)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    attempts: Mapped[list["StudentAttempt"]] = relationship(back_populates="session")


class StudentAttempt(Base):
    __tablename__ = "student_attempts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id"), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("practice_sessions.id"), nullable=False)
    response_json: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="submitted")
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    question: Mapped["Question"] = relationship(back_populates="attempts")
    session: Mapped["PracticeSession"] = relationship(back_populates="attempts")
    score: Mapped["Score"] = relationship(back_populates="attempt", uselist=False)
    feedback: Mapped["Feedback"] = relationship(back_populates="attempt", uselist=False)


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_attempts.id"), nullable=False, unique=True)
    rubric_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rubrics.id"), nullable=False)
    rubric_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    mastery_band: Mapped[str] = mapped_column(String(30), nullable=False)
    scoring_method: Mapped[str] = mapped_column(String(20), nullable=False)
    rubric_breakdown_json: Mapped[list[dict]] = mapped_column(JSON_TYPE, nullable=False)
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    attempt: Mapped["StudentAttempt"] = relationship(back_populates="score")
    rubric: Mapped["Rubric"] = relationship()


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_attempts.id"), nullable=False, unique=True)
    strengths_json: Mapped[list[str]] = mapped_column(JSON_TYPE, nullable=False, default=list)
    gaps_json: Mapped[list[str]] = mapped_column(JSON_TYPE, nullable=False, default=list)
    next_step: Mapped[str] = mapped_column(Text, nullable=False)
    feedback_json: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    attempt: Mapped["StudentAttempt"] = relationship(back_populates="feedback")


class ModuleProgress(Base):
    __tablename__ = "module_progress"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topics.id"), nullable=False)
    progress_status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_started")
    concept_mastery_json: Mapped[dict[str, str]] = mapped_column(JSON_TYPE, nullable=False, default=dict)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


def _practice_session_question_identifiers(connection, session_id: uuid.UUID) -> list[str]:
    return [
        identifier
        for (identifier,) in connection.execute(
            select(func.coalesce(Question.external_id, cast(Question.id, String))).join(
                StudentAttempt, StudentAttempt.question_id == Question.id
            ).where(StudentAttempt.session_id == session_id).distinct()
        )
    ]


def _sync_practice_session_lifecycle(connection, session_id: uuid.UUID) -> None:
    row = connection.execute(
        select(PracticeSession.completed_at, PracticeSession.question_queue_json).where(
            PracticeSession.id == session_id
        )
    ).first()
    if row is None:
        return

    completed_at, question_queue = row
    if completed_at is not None:
        return

    queue = list(question_queue or [])
    attempted_identifiers = _practice_session_question_identifiers(connection, session_id)

    if queue and all(question_id in attempted_identifiers for question_id in queue):
        connection.execute(
            update(PracticeSession)
            .where(PracticeSession.id == session_id)
            .values(status="completed", completed_at=func.now())
        )
        return

    if attempted_identifiers:
        connection.execute(
            update(PracticeSession)
            .where(PracticeSession.id == session_id)
            .values(status="in_progress")
        )
        return

    connection.execute(
        update(PracticeSession).where(PracticeSession.id == session_id).values(status="created")
    )


@event.listens_for(StudentAttempt, "after_insert")
def _update_practice_session_lifecycle_after_attempt_insert(
    mapper: object, connection, target: StudentAttempt
) -> None:
    _sync_practice_session_lifecycle(connection, target.session_id)


@event.listens_for(Score, "before_insert")
def _populate_score_rubric_lineage(mapper: object, connection, target: Score) -> None:
    if target.rubric_id is not None:
        return

    rubric_row = connection.execute(
        select(Rubric.id, Rubric.version)
        .join(Question, Question.id == Rubric.question_id)
        .join(StudentAttempt, StudentAttempt.question_id == Question.id)
        .where(StudentAttempt.id == target.attempt_id)
    ).first()
    if rubric_row is None:
        raise ValueError("Unable to resolve rubric lineage for scored attempt.")

    target.rubric_id = rubric_row.id
    target.rubric_version = rubric_row.version


def _ensure_sqlite_lineage_columns() -> None:
    if default_engine.dialect.name != "sqlite":
        return

    inspector = inspect(default_engine)
    if "practice_sessions" in inspector.get_table_names():
        practice_session_columns = {column["name"] for column in inspector.get_columns("practice_sessions")}
        with default_engine.begin() as connection:
            if "status" not in practice_session_columns:
                connection.execute(
                    text("ALTER TABLE practice_sessions ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'created'")
                )
            if "question_queue_json" not in practice_session_columns:
                connection.execute(
                    text("ALTER TABLE practice_sessions ADD COLUMN question_queue_json JSON NOT NULL DEFAULT '[]'")
                )
            connection.execute(
                text(
                    """
                    UPDATE practice_sessions
                    SET question_queue_json = json(COALESCE(json_extract(config_json, '$.question_queue'), '[]'))
                    WHERE question_queue_json IS NULL OR question_queue_json = '[]'
                    """
                )
            )

    if "rubrics" in inspector.get_table_names():
        rubric_columns = {column["name"] for column in inspector.get_columns("rubrics")}
        if "version" not in rubric_columns:
            with default_engine.begin() as connection:
                connection.execute(text("ALTER TABLE rubrics ADD COLUMN version INTEGER NOT NULL DEFAULT 1"))

    if "scores" in inspector.get_table_names():
        score_columns = {column["name"] for column in inspector.get_columns("scores")}
        with default_engine.begin() as connection:
            if "rubric_id" not in score_columns:
                connection.execute(text("ALTER TABLE scores ADD COLUMN rubric_id CHAR(32)"))
            if "rubric_version" not in score_columns:
                connection.execute(text("ALTER TABLE scores ADD COLUMN rubric_version INTEGER NOT NULL DEFAULT 1"))
            connection.execute(
                text(
                    """
                    UPDATE scores
                    SET rubric_id = (
                        SELECT rubrics.id
                        FROM rubrics
                        JOIN questions ON questions.id = rubrics.question_id
                        JOIN student_attempts ON student_attempts.question_id = questions.id
                        WHERE student_attempts.id = scores.attempt_id
                    ),
                    rubric_version = COALESCE((
                        SELECT rubrics.version
                        FROM rubrics
                        JOIN questions ON questions.id = rubrics.question_id
                        JOIN student_attempts ON student_attempts.question_id = questions.id
                        WHERE student_attempts.id = scores.attempt_id
                    ), rubric_version)
                    WHERE rubric_id IS NULL
                    """
                )
            )


_ensure_sqlite_lineage_columns()
