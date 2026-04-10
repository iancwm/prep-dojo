from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import PracticeSession
from app.db.session import get_session
from app.main import app
from app.seeds.reference_data import SECONDARY_REFERENCE_QUESTION_ID
from app.services.scoring import REFERENCE_QUESTION_ID


def _configure_isolated_session(tmp_path: Path):
    database_path = tmp_path / "prep-dojo-practice-session.db"
    engine = create_engine(f"sqlite:///{database_path}", future=True, connect_args={"check_same_thread": False})
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_session():
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    return engine


def test_create_practice_session_tracks_queue_and_progress_fields(tmp_path: Path) -> None:
    engine = _configure_isolated_session(tmp_path)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/practice-sessions",
                json={
                    "session_id": "session-queue-1",
                    "source": "authored-practice",
                    "question_queue": [
                        REFERENCE_QUESTION_ID,
                        SECONDARY_REFERENCE_QUESTION_ID,
                    ],
                },
            )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 201
    assert body["session_id"] == "session-queue-1"
    assert body["status"] == "created"
    assert body["question_queue"] == [REFERENCE_QUESTION_ID, SECONDARY_REFERENCE_QUESTION_ID]
    assert body["queued_question_count"] == 2
    assert body["completed_question_count"] == 0
    assert body["remaining_question_count"] == 2
    assert body["current_question_id"] == REFERENCE_QUESTION_ID

    with Session(engine) as session:
        stored_session = session.scalar(select(PracticeSession).where(PracticeSession.client_session_id == "session-queue-1"))
        assert stored_session is not None
        assert stored_session.status == "created"
        assert stored_session.question_queue_json == [REFERENCE_QUESTION_ID, SECONDARY_REFERENCE_QUESTION_ID]


def test_practice_session_progress_moves_through_queued_questions(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    try:
        with TestClient(app) as client:
            create_response = client.post(
                "/api/v1/practice-sessions",
                json={
                    "session_id": "session-queue-2",
                    "source": "authored-practice",
                    "question_queue": [
                        REFERENCE_QUESTION_ID,
                        SECONDARY_REFERENCE_QUESTION_ID,
                    ],
                },
            )
            assert create_response.status_code == 201

            first_attempt = client.post(
                f"/api/v1/reference/questions/{REFERENCE_QUESTION_ID}/submit",
                json={
                    "question_id": REFERENCE_QUESTION_ID,
                    "session_id": "session-queue-2",
                    "response": {
                        "response_type": "free_text",
                        "content": (
                            "Enterprise value captures operating value independent of capital structure, "
                            "while equity value is the residual claim for shareholders."
                        ),
                    },
                },
            )
            assert first_attempt.status_code == 200

            in_progress_response = client.get("/api/v1/practice-sessions/session-queue-2")

            second_attempt = client.post(
                f"/api/v1/reference/questions/{SECONDARY_REFERENCE_QUESTION_ID}/submit",
                json={
                    "question_id": SECONDARY_REFERENCE_QUESTION_ID,
                    "session_id": "session-queue-2",
                    "response": {
                        "response_type": "free_text",
                        "content": (
                            "The follow-up question still compares operating value with equity value, "
                            "and EV-based multiples remain better for leverage-neutral comparisons."
                        ),
                    },
                },
            )
            assert second_attempt.status_code == 200

            completed_response = client.get("/api/v1/practice-sessions/session-queue-2")
    finally:
        app.dependency_overrides.clear()

    in_progress_body = in_progress_response.json()
    completed_body = completed_response.json()

    assert in_progress_response.status_code == 200
    assert in_progress_body["status"] == "in_progress"
    assert in_progress_body["queued_question_count"] == 2
    assert in_progress_body["completed_question_count"] == 1
    assert in_progress_body["remaining_question_count"] == 1
    assert in_progress_body["current_question_id"] == SECONDARY_REFERENCE_QUESTION_ID
    assert in_progress_body["completed_at"] is None

    assert completed_response.status_code == 200
    assert completed_body["status"] == "completed"
    assert completed_body["queued_question_count"] == 2
    assert completed_body["completed_question_count"] == 2
    assert completed_body["remaining_question_count"] == 0
    assert completed_body["current_question_id"] is None
    assert completed_body["completed_at"] is not None


def test_explicit_start_and_complete_endpoints_drive_session_status(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    try:
        with TestClient(app) as client:
            create_response = client.post(
                "/api/v1/practice-sessions",
                json={
                    "session_id": "session-manual-1",
                    "source": "authored-practice",
                    "question_queue": [REFERENCE_QUESTION_ID],
                },
            )
            assert create_response.status_code == 201

            start_response = client.post(
                "/api/v1/practice-sessions/session-manual-1/start",
                json={"status": "in_progress"},
            )
            complete_response = client.post(
                "/api/v1/practice-sessions/session-manual-1/complete",
                json={"status": "completed"},
            )
    finally:
        app.dependency_overrides.clear()

    assert start_response.status_code == 200
    assert start_response.json()["status"] == "in_progress"
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"
    assert complete_response.json()["completed_at"] is not None


def test_invalid_explicit_transitions_are_rejected(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    try:
        with TestClient(app) as client:
            create_response = client.post(
                "/api/v1/practice-sessions",
                json={
                    "session_id": "session-manual-2",
                    "source": "authored-practice",
                    "question_queue": [REFERENCE_QUESTION_ID],
                },
            )
            assert create_response.status_code == 201

            wrong_start_payload = client.post(
                "/api/v1/practice-sessions/session-manual-2/start",
                json={"status": "completed"},
            )
            early_complete = client.post(
                "/api/v1/practice-sessions/session-manual-2/complete",
                json={"status": "completed"},
            )
    finally:
        app.dependency_overrides.clear()

    assert wrong_start_payload.status_code == 400
    assert "in_progress" in wrong_start_payload.json()["detail"]
    assert early_complete.status_code == 400
    assert "started" in early_complete.json()["detail"]


def test_practice_session_list_filters_by_status_and_source(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    try:
        with TestClient(app) as client:
            created_authored = client.post(
                "/api/v1/practice-sessions",
                json={
                    "session_id": "session-filter-created",
                    "source": "authored-practice",
                    "question_queue": [REFERENCE_QUESTION_ID],
                },
            )
            completed_authored = client.post(
                "/api/v1/practice-sessions",
                json={
                    "session_id": "session-filter-completed",
                    "source": "authored-practice",
                    "question_queue": [SECONDARY_REFERENCE_QUESTION_ID],
                },
            )
            created_default = client.post(
                "/api/v1/practice-sessions",
                json={
                    "session_id": "session-filter-default",
                    "source": "practice-session",
                    "question_queue": [REFERENCE_QUESTION_ID],
                },
            )
            assert created_authored.status_code == 201
            assert completed_authored.status_code == 201
            assert created_default.status_code == 201

            start_response = client.post(
                "/api/v1/practice-sessions/session-filter-completed/start",
                json={"status": "in_progress"},
            )
            complete_response = client.post(
                "/api/v1/practice-sessions/session-filter-completed/complete",
                json={"status": "completed"},
            )
            assert start_response.status_code == 200
            assert complete_response.status_code == 200

            completed_filter_response = client.get(
                "/api/v1/practice-sessions",
                params={"status": "completed"},
            )
            authored_source_response = client.get(
                "/api/v1/practice-sessions",
                params={"source": "authored-practice"},
            )
            invalid_status_response = client.get(
                "/api/v1/practice-sessions",
                params={"status": "not-a-real-status"},
            )
    finally:
        app.dependency_overrides.clear()

    assert completed_filter_response.status_code == 200
    assert [item["session_id"] for item in completed_filter_response.json()] == [
        "session-filter-completed"
    ]

    assert authored_source_response.status_code == 200
    assert {item["session_id"] for item in authored_source_response.json()} == {
        "session-filter-created",
        "session-filter-completed",
    }

    assert invalid_status_response.status_code == 422
    assert invalid_status_response.json()["detail"]


def test_practice_session_list_filters_by_time_and_queue_position(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    try:
        with TestClient(app) as client:
            queued_response = client.post(
                "/api/v1/practice-sessions",
                json={
                    "session_id": "session-filter-queued",
                    "source": "pilot-smoke",
                    "question_queue": [REFERENCE_QUESTION_ID, SECONDARY_REFERENCE_QUESTION_ID],
                },
            )
            finished_response = client.post(
                "/api/v1/practice-sessions",
                json={
                    "session_id": "session-filter-finished",
                    "source": "pilot-smoke",
                    "question_queue": [REFERENCE_QUESTION_ID],
                },
            )
            assert queued_response.status_code == 201
            assert finished_response.status_code == 201

            start_finished = client.post(
                "/api/v1/practice-sessions/session-filter-finished/start",
                json={"status": "in_progress"},
            )
            submit_finished = client.post(
                f"/api/v1/reference/questions/{REFERENCE_QUESTION_ID}/submit",
                json={
                    "question_id": REFERENCE_QUESTION_ID,
                    "session_id": "session-filter-finished",
                    "response": {
                        "response_type": "free_text",
                        "content": "Enterprise value is better for leverage-neutral comparison.",
                    },
                },
            )
            complete_finished = client.post(
                "/api/v1/practice-sessions/session-filter-finished/complete",
                json={"status": "completed"},
            )
            assert start_finished.status_code == 200
            assert submit_finished.status_code == 200
            assert complete_finished.status_code == 200

            current_question_response = client.get(
                "/api/v1/practice-sessions",
                params={
                    "current_question_id": REFERENCE_QUESTION_ID,
                    "has_remaining": "true",
                },
            )
            no_remaining_response = client.get(
                "/api/v1/practice-sessions",
                params={"has_remaining": "false"},
            )

            started_after = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
            started_before = (datetime.now(UTC) + timedelta(minutes=5)).isoformat()
            time_window_response = client.get(
                "/api/v1/practice-sessions",
                params={
                    "started_after": started_after,
                    "started_before": started_before,
                    "source": "pilot-smoke",
                },
            )
            invalid_window_response = client.get(
                "/api/v1/practice-sessions",
                params={
                    "started_after": started_before,
                    "started_before": started_after,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert current_question_response.status_code == 200
    assert [item["session_id"] for item in current_question_response.json()] == ["session-filter-queued"]

    assert no_remaining_response.status_code == 200
    assert [item["session_id"] for item in no_remaining_response.json()] == ["session-filter-finished"]

    assert time_window_response.status_code == 200
    assert {item["session_id"] for item in time_window_response.json()} == {
        "session-filter-queued",
        "session-filter-finished",
    }

    assert invalid_window_response.status_code == 422
    assert invalid_window_response.json()["detail"]
