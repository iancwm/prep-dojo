from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import Feedback, ModuleProgress, PracticeSession, Question, Score, StudentAttempt
from app.db.session import get_session
from app.main import app
from app.seeds.reference_data import SECONDARY_REFERENCE_QUESTION_ID
from app.services.scoring import REFERENCE_QUESTION_ID


def test_submit_reference_attempt_persists_attempt_score_and_feedback(tmp_path: Path) -> None:
    database_path = tmp_path / "prep-dojo-test.db"
    engine = create_engine(f"sqlite:///{database_path}", future=True, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_session():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/reference/modules/valuation-enterprise-value/submit",
                json={
                    "question_id": REFERENCE_QUESTION_ID,
                    "session_id": "persisted-session-1",
                    "response": {
                        "response_type": "free_text",
                        "content": (
                            "Enterprise value captures the operating business and normalizes capital structure. "
                            "I would use EV / EBITDA across companies with different leverage, while equity "
                            "value still matters for P / E."
                        ),
                    },
                },
            )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 200
    assert body["attempt_id"]

    with Session(engine) as session:
        stored_question = session.scalar(select(Question).where(Question.external_id == REFERENCE_QUESTION_ID))
        stored_attempt = session.scalar(select(StudentAttempt))
        stored_score = session.scalar(select(Score))
        stored_feedback = session.scalar(select(Feedback))
        stored_practice_session = session.scalar(select(PracticeSession))
        stored_progress = session.scalar(select(ModuleProgress))

        assert stored_question is not None
        assert stored_attempt is not None
        assert stored_attempt.question_id == stored_question.id
        assert stored_attempt.response_json["response_type"] == "free_text"
        assert stored_score is not None
        assert stored_score.attempt_id == stored_attempt.id
        assert stored_feedback is not None
        assert stored_feedback.attempt_id == stored_attempt.id
        assert stored_practice_session is not None
        assert stored_practice_session.client_session_id == "persisted-session-1"
        assert stored_progress is not None
        assert stored_progress.concept_mastery_json["enterprise-value-vs-equity-value"] in {
            "ready_for_retry",
            "interview_ready",
        }


def test_generic_reference_question_submit_persists_second_question(tmp_path: Path) -> None:
    database_path = tmp_path / "prep-dojo-second.db"
    engine = create_engine(f"sqlite:///{database_path}", future=True, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_session():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session

    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/reference/questions/{SECONDARY_REFERENCE_QUESTION_ID}/submit",
                json={
                    "question_id": SECONDARY_REFERENCE_QUESTION_ID,
                    "session_id": "persisted-session-2",
                    "response": {
                        "response_type": "free_text",
                        "content": (
                            "Equity value matters for per-share metrics like P / E and the shareholder perspective, "
                            "but enterprise value is still better for operating comparisons."
                        ),
                    },
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    with Session(engine) as session:
        stored_question = session.scalar(select(Question).where(Question.external_id == SECONDARY_REFERENCE_QUESTION_ID))
        assert stored_question is not None
        stored_attempt = session.scalar(select(StudentAttempt).where(StudentAttempt.question_id == stored_question.id))
        assert stored_attempt is not None
