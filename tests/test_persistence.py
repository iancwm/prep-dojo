from __future__ import annotations

import uuid
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import (
    AssessmentMode,
    Concept,
    ExpectedAnswer,
    Feedback,
    ModuleProgress,
    PracticeSession,
    Question,
    Rubric,
    Score,
    StudentAttempt,
    Topic,
)
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
        stored_rubric = session.scalar(select(Rubric).where(Rubric.question_id == stored_question.id))
        stored_practice_session = session.scalar(select(PracticeSession))
        stored_progress = session.scalar(select(ModuleProgress))

        assert stored_question is not None
        assert stored_attempt is not None
        assert stored_attempt.question_id == stored_question.id
        assert stored_attempt.response_json["response_type"] == "free_text"
        assert stored_attempt.status == "complete"
        assert stored_score is not None
        assert stored_score.attempt_id == stored_attempt.id
        assert stored_rubric is not None
        assert stored_score.rubric_id == stored_rubric.id
        assert stored_score.rubric_version == stored_rubric.version
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
        assert stored_attempt.status == "complete"


def test_create_authored_question_persists_bundle_artifacts(tmp_path: Path) -> None:
    database_path = tmp_path / "prep-dojo-authored.db"
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
                "/api/v1/authored/questions",
                json={
                    "topic": {
                        "slug": "accounting",
                        "title": "Accounting",
                        "description": "Accounting topics for interview prep.",
                    },
                    "concept": {
                        "topic_slug": "accounting",
                        "slug": "working-capital",
                        "title": "Working Capital",
                        "definition": "Operating current assets minus operating current liabilities.",
                        "difficulty": "foundational",
                    },
                    "question": {
                        "concept_slug": "working-capital",
                        "assessment_mode": "short_answer",
                        "difficulty": "foundational",
                        "prompt": "Why does an increase in inventory reduce free cash flow?",
                        "payload": {
                            "question_type": "short_answer",
                            "prompt": "Why does an increase in inventory reduce free cash flow?",
                        },
                    },
                    "rubric": {
                        "scoring_style": "rubric",
                        "criteria": [
                            {
                                "name": "reasoning",
                                "description": "Explains why inventory is a use of cash.",
                                "weight": 1.0,
                                "min_score": 0,
                                "max_score": 4,
                            }
                        ],
                        "thresholds": [
                            {"band": "needs_review", "min_percentage": 0},
                            {"band": "interview_ready", "min_percentage": 80},
                        ],
                    },
                    "expected_answer": {
                        "answer_text": "Inventory build consumes cash before revenue is recognized.",
                        "answer_outline": ["Inventory build uses cash", "Working capital rises"],
                        "key_points": ["use of cash", "working capital"],
                    },
                    "common_mistakes": [
                        {
                            "mistake_text": "Inventory is always good for free cash flow because it is an asset.",
                            "why_it_is_wrong": "Assets can still absorb cash.",
                            "remediation_hint": "Track the cash movement directly.",
                        }
                    ],
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    created_body = response.json()

    with Session(engine) as session:
        stored_topic = session.scalar(select(Topic).where(Topic.slug == "accounting"))
        stored_concept = session.scalar(select(Concept).where(Concept.slug == "working-capital"))
        stored_question = session.scalar(
            select(Question).where(Question.id == uuid.UUID(created_body["question"]["id"]))
        )
        stored_assessment_mode = session.scalar(
            select(AssessmentMode).where(AssessmentMode.name == "short_answer")
        )
        stored_rubric = session.scalar(select(Rubric))
        stored_expected_answer = session.scalar(select(ExpectedAnswer))

        assert stored_topic is not None
        assert stored_concept is not None
        assert stored_concept.topic_id == stored_topic.id
        assert stored_question is not None
        assert stored_question.concept_id == stored_concept.id
        assert stored_question.assessment_mode_id == stored_assessment_mode.id
        assert stored_question.external_id is None
        assert stored_question.status == "draft"
        assert stored_rubric is not None
        assert stored_rubric.question_id == stored_question.id
        assert stored_rubric.status == "draft"
        assert stored_rubric.version == 1
        assert stored_expected_answer is not None
        assert stored_expected_answer.question_id == stored_question.id


def test_authored_question_status_transition_persists_review_and_publish_state(tmp_path: Path) -> None:
    database_path = tmp_path / "prep-dojo-authored-review.db"
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
            create_response = client.post(
                "/api/v1/authored/questions",
                json={
                    "topic": {
                        "slug": "accounting",
                        "title": "Accounting",
                        "description": "Accounting topics for interview prep.",
                    },
                    "concept": {
                        "topic_slug": "accounting",
                        "slug": "working-capital",
                        "title": "Working Capital",
                        "definition": "Operating current assets minus operating current liabilities.",
                        "difficulty": "foundational",
                    },
                    "question": {
                        "concept_slug": "working-capital",
                        "assessment_mode": "short_answer",
                        "difficulty": "foundational",
                        "prompt": "Why does an increase in inventory reduce free cash flow?",
                        "payload": {
                            "question_type": "short_answer",
                            "prompt": "Why does an increase in inventory reduce free cash flow?",
                        },
                    },
                    "rubric": {
                        "scoring_style": "rubric",
                        "criteria": [
                            {
                                "name": "reasoning",
                                "description": "Explains why inventory is a use of cash.",
                                "weight": 1.0,
                                "min_score": 0,
                                "max_score": 4,
                            }
                        ],
                        "thresholds": [
                            {"band": "needs_review", "min_percentage": 0},
                            {"band": "interview_ready", "min_percentage": 80},
                        ],
                    },
                    "expected_answer": {
                        "answer_text": "Inventory build consumes cash before revenue is recognized.",
                        "answer_outline": ["Inventory build uses cash", "Working capital rises"],
                        "key_points": ["use of cash", "working capital"],
                    },
                },
            )
            question_id = create_response.json()["question"]["id"]

            review_response = client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                json={"status": "reviewed", "review_notes": "Reviewed and ready for release."},
            )
            publish_response = client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                json={"status": "published"},
            )
    finally:
        app.dependency_overrides.clear()

    assert review_response.status_code == 200
    assert publish_response.status_code == 200

    with Session(engine) as session:
        stored_question = session.scalar(select(Question).where(Question.id == uuid.UUID(question_id)))
        stored_rubric = session.scalar(select(Rubric).where(Rubric.question_id == stored_question.id))
        stored_concept = session.scalar(select(Concept).where(Concept.id == stored_question.concept_id))
        stored_topic = session.scalar(select(Topic).where(Topic.id == stored_concept.topic_id))

        assert stored_question is not None
        assert stored_question.status == "published"
        assert stored_rubric is not None
        assert stored_rubric.status == "published"
        assert stored_rubric.review_notes == "Reviewed and ready for release."
        assert stored_rubric.version == 1
        assert stored_concept is not None
        assert stored_concept.status == "published"
        assert stored_topic is not None
        assert stored_topic.status == "published"


def test_submit_authored_question_persists_attempt_score_and_progress(tmp_path: Path) -> None:
    database_path = tmp_path / "prep-dojo-authored-submit.db"
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
            create_response = client.post(
                "/api/v1/authored/questions",
                json={
                    "topic": {
                        "slug": "accounting",
                        "title": "Accounting",
                        "description": "Accounting topics for interview prep.",
                    },
                    "concept": {
                        "topic_slug": "accounting",
                        "slug": "working-capital",
                        "title": "Working Capital",
                        "definition": "Operating current assets minus operating current liabilities.",
                        "difficulty": "foundational",
                    },
                    "question": {
                        "concept_slug": "working-capital",
                        "assessment_mode": "short_answer",
                        "difficulty": "foundational",
                        "prompt": "Why does an increase in inventory reduce free cash flow?",
                        "payload": {
                            "question_type": "short_answer",
                            "prompt": "Why does an increase in inventory reduce free cash flow?",
                        },
                    },
                    "rubric": {
                        "scoring_style": "rubric",
                        "criteria": [
                            {
                                "name": "recall",
                                "description": "Identifies inventory as a use of cash.",
                                "weight": 0.5,
                                "min_score": 0,
                                "max_score": 4,
                                "strong_response_fragments": ["use of cash", "inventory"],
                            },
                            {
                                "name": "reasoning",
                                "description": "Explains why working capital increases.",
                                "weight": 0.5,
                                "min_score": 0,
                                "max_score": 4,
                                "strong_response_fragments": ["working capital", "revenue"],
                            },
                        ],
                        "thresholds": [
                            {"band": "needs_review", "min_percentage": 0},
                            {"band": "ready_for_retry", "min_percentage": 60},
                            {"band": "interview_ready", "min_percentage": 80},
                        ],
                    },
                    "expected_answer": {
                        "answer_text": "Inventory build consumes cash before revenue is recognized.",
                        "answer_outline": ["Inventory build uses cash", "Working capital rises"],
                        "key_points": ["use of cash", "working capital"],
                    },
                },
            )
            question_id = create_response.json()["question"]["id"]
            client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                json={"status": "reviewed", "review_notes": "Ready to publish."},
            )
            client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                json={"status": "published"},
            )

            submit_response = client.post(
                f"/api/v1/authored/questions/{question_id}/submit",
                json={
                    "question_id": question_id,
                    "session_id": "authored-persisted-session-1",
                    "response": {
                        "response_type": "free_text",
                        "content": (
                            "Inventory is a use of cash because the company pays cash before the inventory becomes "
                            "revenue. That increases working capital and reduces free cash flow."
                        ),
                    },
                },
            )
    finally:
        app.dependency_overrides.clear()

    body = submit_response.json()
    assert submit_response.status_code == 200
    assert body["attempt_id"]

    with Session(engine) as session:
        stored_question = session.scalar(
            select(Question).where(Question.id == uuid.UUID(question_id))
        )
        stored_attempt = session.scalar(select(StudentAttempt).where(StudentAttempt.question_id == stored_question.id))
        stored_score = session.scalar(select(Score).where(Score.attempt_id == stored_attempt.id))
        stored_feedback = session.scalar(select(Feedback).where(Feedback.attempt_id == stored_attempt.id))
        stored_rubric = session.scalar(select(Rubric).where(Rubric.question_id == stored_question.id))
        stored_practice_session = session.scalar(
            select(PracticeSession).where(PracticeSession.client_session_id == "authored-persisted-session-1")
        )
        stored_progress = session.scalar(select(ModuleProgress))

        assert stored_question is not None
        assert stored_question.external_id is None
        assert stored_attempt is not None
        assert stored_attempt.response_json["response_type"] == "free_text"
        assert stored_attempt.status == "complete"
        assert stored_score is not None
        assert stored_score.overall_score > 0
        assert stored_rubric is not None
        assert stored_score.rubric_id == stored_rubric.id
        assert stored_score.rubric_version == stored_rubric.version
        assert stored_feedback is not None
        assert stored_practice_session is not None
        assert stored_practice_session.config_json["source"] == "authored-question"
        assert stored_progress is not None
        assert stored_progress.concept_mastery_json["working-capital"] in {
            "ready_for_retry",
            "interview_ready",
        }


def test_practice_session_endpoints_show_attempt_history(tmp_path: Path) -> None:
    database_path = tmp_path / "prep-dojo-session-history.db"
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
            session_response = client.post(
                "/api/v1/practice-sessions",
                json={"session_id": "session-history-1", "source": "authored-practice"},
            )
            assert session_response.status_code == 201

            create_question_response = client.post(
                "/api/v1/authored/questions",
                json={
                    "topic": {
                        "slug": "accounting",
                        "title": "Accounting",
                        "description": "Accounting topics for interview prep.",
                    },
                    "concept": {
                        "topic_slug": "accounting",
                        "slug": "working-capital",
                        "title": "Working Capital",
                        "definition": "Operating current assets minus operating current liabilities.",
                        "difficulty": "foundational",
                    },
                    "question": {
                        "concept_slug": "working-capital",
                        "assessment_mode": "short_answer",
                        "difficulty": "foundational",
                        "prompt": "Why does an increase in inventory reduce free cash flow?",
                        "payload": {
                            "question_type": "short_answer",
                            "prompt": "Why does an increase in inventory reduce free cash flow?",
                        },
                    },
                    "rubric": {
                        "scoring_style": "rubric",
                        "criteria": [
                            {
                                "name": "reasoning",
                                "description": "Explains why inventory is a use of cash.",
                                "weight": 1.0,
                                "min_score": 0,
                                "max_score": 4,
                            }
                        ],
                        "thresholds": [
                            {"band": "needs_review", "min_percentage": 0},
                            {"band": "interview_ready", "min_percentage": 80},
                        ],
                    },
                    "expected_answer": {
                        "answer_text": "Inventory build consumes cash before revenue is recognized.",
                        "answer_outline": ["Inventory build uses cash", "Working capital rises"],
                        "key_points": ["use of cash", "working capital"],
                    },
                },
            )
            question_id = create_question_response.json()["question"]["id"]
            client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                json={"status": "reviewed", "review_notes": "Approved for practice use."},
            )
            client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                json={"status": "published"},
            )

            submit_response = client.post(
                f"/api/v1/authored/questions/{question_id}/submit",
                json={
                    "question_id": question_id,
                    "session_id": "session-history-1",
                    "response": {
                        "response_type": "free_text",
                        "content": "Inventory uses cash up front, increases working capital, and lowers free cash flow.",
                    },
                },
            )
            assert submit_response.status_code == 200

            list_response = client.get("/api/v1/practice-sessions")
            detail_response = client.get("/api/v1/practice-sessions/session-history-1")
    finally:
        app.dependency_overrides.clear()

    list_body = list_response.json()
    detail_body = detail_response.json()

    assert list_response.status_code == 200
    assert any(item["session_id"] == "session-history-1" for item in list_body)
    assert detail_response.status_code == 200
    assert detail_body["session_id"] == "session-history-1"
    assert detail_body["source"] == "authored-practice"
    assert len(detail_body["attempts"]) == 1
    assert detail_body["attempts"][0]["question_id"] == question_id
