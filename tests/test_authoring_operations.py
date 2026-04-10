from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_session
from app.main import app

MENTOR_HEADERS = {"X-User-Role": "academic"}


def _configure_isolated_session(tmp_path: Path):
    database_path = tmp_path / "prep-dojo-authoring-ops.db"
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


def test_topic_and_concept_crud_endpoints_work_for_mentor_roles(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    with TestClient(app) as client:
        try:
            create_topic_response = client.post(
                "/api/v1/authored/topics",
                headers=MENTOR_HEADERS,
                json={
                    "slug": "accounting",
                    "title": "Accounting",
                    "description": "Accounting topics for interview prep.",
                    "order_index": 2,
                    "status": "draft",
                },
            )
            assert create_topic_response.status_code == 201

            create_concept_response = client.post(
                "/api/v1/authored/concepts",
                headers=MENTOR_HEADERS,
                json={
                    "topic_slug": "accounting",
                    "slug": "working-capital",
                    "title": "Working Capital",
                    "definition": "Operating current assets minus operating current liabilities.",
                    "difficulty": "foundational",
                    "prerequisites": ["balance-sheet"],
                    "status": "draft",
                },
            )
            assert create_concept_response.status_code == 201

            update_topic_response = client.put(
                "/api/v1/authored/topics/accounting",
                headers=MENTOR_HEADERS,
                json={
                    "title": "Accounting and Statements",
                    "description": "Updated accounting coverage.",
                    "order_index": 3,
                    "status": "reviewed",
                },
            )
            update_concept_response = client.put(
                "/api/v1/authored/concepts/working-capital",
                headers=MENTOR_HEADERS,
                json={
                    "topic_slug": "accounting",
                    "title": "Working Capital Mechanics",
                    "definition": "Tracks short-term operating assets and liabilities.",
                    "difficulty": "intermediate",
                    "prerequisites": ["balance-sheet", "cash-flow-statement"],
                    "status": "reviewed",
                },
            )

            topics_response = client.get("/api/v1/authored/topics", headers=MENTOR_HEADERS)
            concepts_response = client.get(
                "/api/v1/authored/concepts",
                headers=MENTOR_HEADERS,
                params={"topic_slug": "accounting"},
            )
        finally:
            app.dependency_overrides.clear()

    assert update_topic_response.status_code == 200
    assert update_concept_response.status_code == 200
    assert topics_response.status_code == 200
    assert concepts_response.status_code == 200
    assert topics_response.json()[0]["title"] == "Accounting and Statements"
    assert concepts_response.json()[0]["title"] == "Working Capital Mechanics"


def test_topic_and_concept_cannot_skip_directly_to_published(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    with TestClient(app) as client:
        try:
            client.post(
                "/api/v1/authored/topics",
                headers=MENTOR_HEADERS,
                json={
                    "slug": "valuation",
                    "title": "Valuation",
                    "description": "Valuation topics for interview prep.",
                    "order_index": 1,
                    "status": "draft",
                },
            )
            client.post(
                "/api/v1/authored/concepts",
                headers=MENTOR_HEADERS,
                json={
                    "topic_slug": "valuation",
                    "slug": "lbo",
                    "title": "LBO",
                    "definition": "Leveraged buyout basics.",
                    "difficulty": "intermediate",
                    "status": "draft",
                },
            )

            publish_topic_response = client.put(
                "/api/v1/authored/topics/valuation",
                headers=MENTOR_HEADERS,
                json={
                    "title": "Valuation",
                    "description": "Valuation topics for interview prep.",
                    "order_index": 1,
                    "status": "published",
                },
            )
            publish_concept_response = client.put(
                "/api/v1/authored/concepts/lbo",
                headers=MENTOR_HEADERS,
                json={
                    "topic_slug": "valuation",
                    "title": "LBO",
                    "definition": "Leveraged buyout basics.",
                    "difficulty": "intermediate",
                    "prerequisites": [],
                    "status": "published",
                },
            )
        finally:
            app.dependency_overrides.clear()

    assert publish_topic_response.status_code == 400
    assert "Cannot transition topic" in publish_topic_response.json()["detail"]
    assert publish_concept_response.status_code == 400
    assert "Cannot transition concept" in publish_concept_response.json()["detail"]


def test_topic_and_concept_list_filters_hide_archived_by_default(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    with TestClient(app) as client:
        try:
            client.post(
                "/api/v1/authored/topics",
                headers=MENTOR_HEADERS,
                json={
                    "slug": "active-topic",
                    "title": "Active Topic",
                    "description": "Visible topic.",
                    "status": "reviewed",
                },
            )
            client.post(
                "/api/v1/authored/topics",
                headers=MENTOR_HEADERS,
                json={
                    "slug": "archived-topic",
                    "title": "Archived Topic",
                    "description": "Hidden unless requested.",
                    "status": "reviewed",
                },
            )
            client.post(
                "/api/v1/authored/concepts",
                headers=MENTOR_HEADERS,
                json={
                    "topic_slug": "active-topic",
                    "slug": "active-concept",
                    "title": "Active Concept",
                    "definition": "Visible concept.",
                    "difficulty": "foundational",
                    "status": "reviewed",
                },
            )
            client.post(
                "/api/v1/authored/concepts",
                headers=MENTOR_HEADERS,
                json={
                    "topic_slug": "archived-topic",
                    "slug": "archived-concept",
                    "title": "Archived Concept",
                    "definition": "Hidden concept.",
                    "difficulty": "foundational",
                    "status": "reviewed",
                },
            )

            client.post("/api/v1/authored/topics/archived-topic/archive", headers=MENTOR_HEADERS)

            visible_topics_response = client.get("/api/v1/authored/topics", headers=MENTOR_HEADERS)
            visible_concepts_response = client.get("/api/v1/authored/concepts", headers=MENTOR_HEADERS)
            archived_topics_response = client.get(
                "/api/v1/authored/topics",
                headers=MENTOR_HEADERS,
                params={"include_archived": True},
            )
            archived_concepts_response = client.get(
                "/api/v1/authored/concepts",
                headers=MENTOR_HEADERS,
                params={"include_archived": True},
            )
            reviewed_topics_response = client.get(
                "/api/v1/authored/topics",
                headers=MENTOR_HEADERS,
                params={"status": "reviewed"},
            )
            archived_concepts_only_response = client.get(
                "/api/v1/authored/concepts",
                headers=MENTOR_HEADERS,
                params={"status": "archived", "include_archived": True},
            )
        finally:
            app.dependency_overrides.clear()

    assert visible_topics_response.status_code == 200
    assert {item["slug"] for item in visible_topics_response.json()} == {"active-topic"}
    assert visible_concepts_response.status_code == 200
    assert {item["slug"] for item in visible_concepts_response.json()} == {"active-concept"}
    assert archived_topics_response.status_code == 200
    assert {item["slug"] for item in archived_topics_response.json()} == {"active-topic", "archived-topic"}
    assert archived_concepts_response.status_code == 200
    assert {item["slug"] for item in archived_concepts_response.json()} == {"active-concept", "archived-concept"}
    assert reviewed_topics_response.status_code == 200
    assert {item["slug"] for item in reviewed_topics_response.json()} == {"active-topic"}
    assert archived_concepts_only_response.status_code == 200
    assert {item["slug"] for item in archived_concepts_only_response.json()} == {"archived-concept"}


def test_authored_question_list_supports_status_topic_and_concept_filters(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    with TestClient(app) as client:
        try:
            client.post(
                "/api/v1/authored/questions",
                headers=MENTOR_HEADERS,
                json={
                    "topic": {
                        "slug": "valuation",
                        "title": "Valuation",
                        "description": "Valuation topics.",
                    },
                    "concept": {
                        "topic_slug": "valuation",
                        "slug": "ev-equity",
                        "title": "EV vs Equity",
                        "definition": "Compare enterprise and equity value.",
                        "difficulty": "foundational",
                    },
                    "question": {
                        "concept_slug": "ev-equity",
                        "assessment_mode": "short_answer",
                        "difficulty": "foundational",
                        "prompt": "Explain EV versus equity value.",
                        "payload": {
                            "question_type": "short_answer",
                            "prompt": "Explain EV versus equity value.",
                        },
                    },
                    "rubric": {
                        "scoring_style": "rubric",
                        "criteria": [{"name": "reasoning", "description": "Explains the distinction.", "weight": 1.0, "min_score": 0, "max_score": 4}],
                        "thresholds": [{"band": "needs_review", "min_percentage": 0}],
                    },
                    "expected_answer": {
                        "answer_text": "EV includes debt and cash adjustments while equity value is residual to shareholders.",
                        "key_points": ["enterprise value", "equity value"],
                    },
                },
            )
            review_create = client.post(
                "/api/v1/authored/questions",
                headers=MENTOR_HEADERS,
                json={
                    "topic": {
                        "slug": "accounting",
                        "title": "Accounting",
                        "description": "Accounting topics.",
                    },
                    "concept": {
                        "topic_slug": "accounting",
                        "slug": "inventory",
                        "title": "Inventory",
                        "definition": "Inventory cash flow effects.",
                        "difficulty": "foundational",
                    },
                    "question": {
                        "concept_slug": "inventory",
                        "assessment_mode": "short_answer",
                        "difficulty": "foundational",
                        "status": "reviewed",
                        "prompt": "Why does inventory reduce free cash flow?",
                        "payload": {
                            "question_type": "short_answer",
                            "prompt": "Why does inventory reduce free cash flow?",
                        },
                    },
                    "rubric": {
                        "scoring_style": "rubric",
                        "criteria": [{"name": "reasoning", "description": "Explains cash use.", "weight": 1.0, "min_score": 0, "max_score": 4}],
                        "thresholds": [{"band": "needs_review", "min_percentage": 0}],
                    },
                    "expected_answer": {
                        "answer_text": "Inventory consumes cash before revenue is recognized.",
                        "key_points": ["use of cash", "working capital"],
                    },
                },
            )
            assert review_create.status_code == 201

            filtered_by_status = client.get(
                "/api/v1/authored/questions",
                headers=MENTOR_HEADERS,
                params={"status_filter": "reviewed"},
            )
            filtered_by_topic = client.get(
                "/api/v1/authored/questions",
                headers=MENTOR_HEADERS,
                params={"topic_slug": "accounting"},
            )
            filtered_by_concept = client.get(
                "/api/v1/authored/questions",
                headers=MENTOR_HEADERS,
                params={"concept_slug": "ev-equity"},
            )
        finally:
            app.dependency_overrides.clear()

    assert filtered_by_status.status_code == 200
    assert all(item["status"] == "reviewed" for item in filtered_by_status.json())
    assert all(item["topic_slug"] == "accounting" for item in filtered_by_topic.json())
    assert all(item["concept_slug"] == "ev-equity" for item in filtered_by_concept.json())


def test_authored_question_list_rejects_invalid_status_filter(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    with TestClient(app) as client:
        try:
            response = client.get(
                "/api/v1/authored/questions",
                headers=MENTOR_HEADERS,
                params={"status_filter": "invalid-status"},
            )
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 422
    assert "status" in response.text


def test_authored_question_update_bumps_versions_and_resets_review_state(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    with TestClient(app) as client:
        try:
            create_response = client.post(
                "/api/v1/authored/questions",
                headers=MENTOR_HEADERS,
                json={
                    "topic": {
                        "slug": "valuation",
                        "title": "Valuation",
                        "description": "Valuation topics.",
                    },
                    "concept": {
                        "topic_slug": "valuation",
                        "slug": "ev-equity",
                        "title": "EV vs Equity",
                        "definition": "Enterprise value versus equity value.",
                        "difficulty": "foundational",
                    },
                    "question": {
                        "concept_slug": "ev-equity",
                        "assessment_mode": "short_answer",
                        "difficulty": "foundational",
                        "prompt": "Explain EV versus equity value.",
                        "payload": {
                            "question_type": "short_answer",
                            "prompt": "Explain EV versus equity value.",
                        },
                    },
                    "rubric": {
                        "scoring_style": "rubric",
                        "criteria": [{"name": "reasoning", "description": "Explains the distinction.", "weight": 1.0, "min_score": 0, "max_score": 4}],
                        "thresholds": [{"band": "needs_review", "min_percentage": 0}],
                    },
                    "expected_answer": {
                        "answer_text": "EV includes debt and cash adjustments while equity value is residual to shareholders.",
                        "key_points": ["enterprise value", "equity value"],
                    },
                    "common_mistakes": [
                        {
                            "mistake_text": "EV equals market cap.",
                            "why_it_is_wrong": "It ignores debt and cash.",
                            "remediation_hint": "Reconcile enterprise and equity claims.",
                        }
                    ],
                },
            )
            question_id = create_response.json()["question"]["id"]

            review_response = client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                headers=MENTOR_HEADERS,
                json={"status": "reviewed", "review_notes": "Reviewed for initial release."},
            )
            update_response = client.put(
                f"/api/v1/authored/questions/{question_id}",
                headers=MENTOR_HEADERS,
                json={
                    "question": {
                        "concept_slug": "ev-equity",
                        "assessment_mode": "short_answer",
                        "difficulty": "intermediate",
                        "prompt": "When would you discuss EV instead of equity value?",
                        "payload": {
                            "question_type": "short_answer",
                            "prompt": "When would you discuss EV instead of equity value?",
                            "response_guidance": ["explain operating comparison", "mention capital structure"],
                        },
                    },
                    "rubric": {
                        "scoring_style": "rubric",
                        "criteria": [{"name": "application", "description": "Applies the concept in interview context.", "weight": 1.0, "min_score": 0, "max_score": 5}],
                        "thresholds": [{"band": "needs_review", "min_percentage": 0}],
                        "review_notes": "This note should clear because the question changed.",
                    },
                    "expected_answer": {
                        "answer_text": "EV is better for operating comparisons across capital structures.",
                        "answer_outline": ["operating comparison", "capital structure"],
                        "key_points": ["operating comparison", "capital structure"],
                        "acceptable_variants": ["EV normalizes leverage differences."],
                    },
                    "common_mistakes": [
                        {
                            "mistake_text": "Equity value always replaces EV.",
                            "why_it_is_wrong": "It misses debt and non-operating cash context.",
                            "remediation_hint": "Anchor the answer in enterprise comparability.",
                        }
                    ],
                },
            )
            fetch_response = client.get(f"/api/v1/authored/questions/{question_id}", headers=MENTOR_HEADERS)
        finally:
            app.dependency_overrides.clear()

    assert review_response.status_code == 200
    assert update_response.status_code == 200
    updated_body = update_response.json()
    fetched_body = fetch_response.json()
    assert updated_body["question"]["version"] == 2
    assert updated_body["question"]["status"] == "draft"
    assert updated_body["question"]["difficulty"] == "intermediate"
    assert updated_body["question"]["prompt"] == "When would you discuss EV instead of equity value?"
    assert updated_body["rubric"]["criteria"][0]["name"] == "application"
    assert updated_body["rubric"]["review_notes"] is None
    assert updated_body["expected_answer"]["acceptable_variants"] == ["EV normalizes leverage differences."]
    assert updated_body["common_mistakes"][0]["mistake_text"] == "Equity value always replaces EV."
    assert fetched_body["question"]["version"] == 2
    assert fetched_body["question"]["status"] == "draft"


def test_published_authored_question_cannot_be_edited(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    with TestClient(app) as client:
        try:
            create_response = client.post(
                "/api/v1/authored/questions",
                headers=MENTOR_HEADERS,
                json={
                    "topic": {
                        "slug": "accounting",
                        "title": "Accounting",
                        "description": "Accounting topics.",
                    },
                    "concept": {
                        "topic_slug": "accounting",
                        "slug": "working-capital",
                        "title": "Working Capital",
                        "definition": "Working capital mechanics.",
                        "difficulty": "foundational",
                    },
                    "question": {
                        "concept_slug": "working-capital",
                        "assessment_mode": "short_answer",
                        "difficulty": "foundational",
                        "prompt": "Why does inventory reduce free cash flow?",
                        "payload": {
                            "question_type": "short_answer",
                            "prompt": "Why does inventory reduce free cash flow?",
                        },
                    },
                    "rubric": {
                        "scoring_style": "rubric",
                        "criteria": [{"name": "reasoning", "description": "Explains cash use.", "weight": 1.0, "min_score": 0, "max_score": 4}],
                        "thresholds": [{"band": "needs_review", "min_percentage": 0}],
                    },
                    "expected_answer": {
                        "answer_text": "Inventory consumes cash before revenue is recognized.",
                        "key_points": ["use of cash", "working capital"],
                    },
                },
            )
            question_id = create_response.json()["question"]["id"]

            client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                headers=MENTOR_HEADERS,
                json={"status": "reviewed", "review_notes": "Ready to publish."},
            )
            client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                headers=MENTOR_HEADERS,
                json={"status": "published"},
            )
            update_response = client.put(
                f"/api/v1/authored/questions/{question_id}",
                headers=MENTOR_HEADERS,
                json={
                    "question": {
                        "concept_slug": "working-capital",
                        "assessment_mode": "short_answer",
                        "difficulty": "intermediate",
                        "prompt": "Why can inventory be a use of cash?",
                        "payload": {
                            "question_type": "short_answer",
                            "prompt": "Why can inventory be a use of cash?",
                        },
                    },
                    "rubric": {
                        "scoring_style": "rubric",
                        "criteria": [{"name": "reasoning", "description": "Explains cash use.", "weight": 1.0, "min_score": 0, "max_score": 4}],
                        "thresholds": [{"band": "needs_review", "min_percentage": 0}],
                    },
                    "expected_answer": {
                        "answer_text": "Inventory build consumes cash.",
                        "key_points": ["inventory", "cash"],
                    },
                },
            )
        finally:
            app.dependency_overrides.clear()

    assert update_response.status_code == 400
    assert update_response.json()["detail"] == "Published or archived authored questions cannot be edited."


def test_publish_requires_expected_answer_key_points(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    with TestClient(app) as client:
        try:
            create_response = client.post(
                "/api/v1/authored/questions",
                headers=MENTOR_HEADERS,
                json={
                    "topic": {
                        "slug": "modeling",
                        "title": "Modeling",
                        "description": "Modeling topics.",
                    },
                    "concept": {
                        "topic_slug": "modeling",
                        "slug": "working-capital-driver",
                        "title": "Working Capital Driver",
                        "definition": "How working capital affects cash flow.",
                        "difficulty": "foundational",
                    },
                    "question": {
                        "concept_slug": "working-capital-driver",
                        "assessment_mode": "short_answer",
                        "difficulty": "foundational",
                        "prompt": "Why can working capital be a use of cash?",
                        "payload": {
                            "question_type": "short_answer",
                            "prompt": "Why can working capital be a use of cash?",
                        },
                    },
                    "rubric": {
                        "scoring_style": "rubric",
                        "criteria": [{"name": "reasoning", "description": "Explains cash use.", "weight": 1.0, "min_score": 0, "max_score": 4}],
                        "thresholds": [{"band": "needs_review", "min_percentage": 0}],
                    },
                    "expected_answer": {
                        "answer_text": "Working capital can absorb cash before revenue converts.",
                        "key_points": [],
                    },
                },
            )
            question_id = create_response.json()["question"]["id"]

            client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                headers=MENTOR_HEADERS,
                json={"status": "reviewed", "review_notes": "Reviewed."},
            )
            publish_response = client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                headers=MENTOR_HEADERS,
                json={"status": "published"},
            )
        finally:
            app.dependency_overrides.clear()

    assert publish_response.status_code == 400
    assert "key points" in publish_response.json()["detail"]


def test_publish_requires_valid_multiple_choice_payload(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    with TestClient(app) as client:
        try:
            create_response = client.post(
                "/api/v1/authored/questions",
                headers=MENTOR_HEADERS,
                json={
                    "topic": {
                        "slug": "valuation",
                        "title": "Valuation",
                        "description": "Valuation topics.",
                    },
                    "concept": {
                        "topic_slug": "valuation",
                        "slug": "trading-multiples",
                        "title": "Trading Multiples",
                        "definition": "Common valuation multiple usage.",
                        "difficulty": "foundational",
                    },
                    "question": {
                        "concept_slug": "trading-multiples",
                        "assessment_mode": "multiple_choice",
                        "difficulty": "foundational",
                        "prompt": "Which multiple is best across capital structures?",
                        "payload": {
                            "question_type": "mcq_single",
                            "prompt": "Which multiple is best across capital structures?",
                            "options": [{"id": "a", "label": "P / E"}],
                            "correct_option_id": "b",
                            "explanation": "",
                        },
                    },
                    "rubric": {
                        "scoring_style": "automatic",
                        "criteria": [{"name": "recall", "description": "Selects the right option.", "weight": 1.0, "min_score": 0, "max_score": 4}],
                        "thresholds": [{"band": "needs_review", "min_percentage": 0}],
                    },
                    "expected_answer": {
                        "answer_text": "EV / EBITDA is the cleaner operating comparison.",
                        "key_points": ["EV / EBITDA", "capital structure"],
                    },
                },
            )
            question_id = create_response.json()["question"]["id"]

            client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                headers=MENTOR_HEADERS,
                json={"status": "reviewed", "review_notes": "Reviewed."},
            )
            publish_response = client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                headers=MENTOR_HEADERS,
                json={"status": "published"},
            )
        finally:
            app.dependency_overrides.clear()

    assert publish_response.status_code == 400
    assert "Multiple-choice" in publish_response.json()["detail"]


def test_publish_requires_oral_target_duration(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    with TestClient(app) as client:
        try:
            create_response = client.post(
                "/api/v1/authored/questions",
                headers=MENTOR_HEADERS,
                json={
                    "topic": {
                        "slug": "behavioral",
                        "title": "Behavioral",
                        "description": "Behavioral interview topics.",
                    },
                    "concept": {
                        "topic_slug": "behavioral",
                        "slug": "tell-me-about-yourself",
                        "title": "Tell Me About Yourself",
                        "definition": "Structured self-introduction under pressure.",
                        "difficulty": "foundational",
                    },
                    "question": {
                        "concept_slug": "tell-me-about-yourself",
                        "assessment_mode": "oral_recall",
                        "difficulty": "foundational",
                        "prompt": "Give me your 30-second introduction.",
                        "payload": {
                            "question_type": "oral_recall",
                            "prompt": "Give me your 30-second introduction.",
                            "cue": "Keep it crisp and recruiting-relevant.",
                        },
                    },
                    "rubric": {
                        "scoring_style": "hybrid",
                        "criteria": [{"name": "clarity", "description": "Delivers a clear intro.", "weight": 1.0, "min_score": 0, "max_score": 4}],
                        "thresholds": [{"band": "needs_review", "min_percentage": 0}],
                    },
                    "expected_answer": {
                        "answer_text": "A strong introduction is concise, structured, and role-relevant.",
                        "key_points": ["background", "interest", "fit"],
                    },
                },
            )
            question_id = create_response.json()["question"]["id"]

            client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                headers=MENTOR_HEADERS,
                json={"status": "reviewed", "review_notes": "Reviewed."},
            )
            publish_response = client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                headers=MENTOR_HEADERS,
                json={"status": "published"},
            )
        finally:
            app.dependency_overrides.clear()

    assert publish_response.status_code == 400
    assert "target duration" in publish_response.json()["detail"]


def test_archiving_concept_and_topic_cascades_to_child_questions(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    with TestClient(app) as client:
        try:
            create_response = client.post(
                "/api/v1/authored/questions",
                headers=MENTOR_HEADERS,
                json={
                    "topic": {
                        "slug": "behavioral",
                        "title": "Behavioral",
                        "description": "Behavioral interview topics.",
                        "status": "reviewed",
                    },
                    "concept": {
                        "topic_slug": "behavioral",
                        "slug": "leadership",
                        "title": "Leadership",
                        "definition": "Leadership communication examples.",
                        "difficulty": "foundational",
                        "status": "reviewed",
                    },
                    "question": {
                        "concept_slug": "leadership",
                        "assessment_mode": "short_answer",
                        "difficulty": "foundational",
                        "status": "reviewed",
                        "prompt": "Describe a time you led through ambiguity.",
                        "payload": {
                            "question_type": "short_answer",
                            "prompt": "Describe a time you led through ambiguity.",
                        },
                    },
                    "rubric": {
                        "scoring_style": "rubric",
                        "criteria": [{"name": "structure", "description": "Uses a clear story arc.", "weight": 1.0, "min_score": 0, "max_score": 4}],
                        "thresholds": [{"band": "needs_review", "min_percentage": 0}],
                    },
                    "expected_answer": {
                        "answer_text": "Strong answers show ownership, tradeoffs, and outcome.",
                        "key_points": ["ownership", "tradeoffs", "outcome"],
                    },
                },
            )
            question_id = create_response.json()["question"]["id"]

            archive_concept_response = client.post(
                "/api/v1/authored/concepts/leadership/archive",
                headers=MENTOR_HEADERS,
            )
            question_after_concept_archive = client.get(
                f"/api/v1/authored/questions/{question_id}",
                headers=MENTOR_HEADERS,
            )

            second_create_response = client.post(
                "/api/v1/authored/questions",
                headers=MENTOR_HEADERS,
                json={
                    "topic": {
                        "slug": "technical",
                        "title": "Technical",
                        "description": "Technical interview topics.",
                        "status": "reviewed",
                    },
                    "concept": {
                        "topic_slug": "technical",
                        "slug": "debugging",
                        "title": "Debugging",
                        "definition": "Structured debugging habits.",
                        "difficulty": "intermediate",
                        "status": "reviewed",
                    },
                    "question": {
                        "concept_slug": "debugging",
                        "assessment_mode": "short_answer",
                        "difficulty": "intermediate",
                        "status": "reviewed",
                        "prompt": "How do you isolate a production bug?",
                        "payload": {
                            "question_type": "short_answer",
                            "prompt": "How do you isolate a production bug?",
                        },
                    },
                    "rubric": {
                        "scoring_style": "rubric",
                        "criteria": [{"name": "method", "description": "Uses a reproducible process.", "weight": 1.0, "min_score": 0, "max_score": 4}],
                        "thresholds": [{"band": "needs_review", "min_percentage": 0}],
                    },
                    "expected_answer": {
                        "answer_text": "Start from repro, narrow variables, confirm root cause.",
                        "key_points": ["repro", "narrow variables", "root cause"],
                    },
                },
            )
            second_question_id = second_create_response.json()["question"]["id"]

            archive_topic_response = client.post(
                "/api/v1/authored/topics/technical/archive",
                headers=MENTOR_HEADERS,
            )
            question_after_topic_archive = client.get(
                f"/api/v1/authored/questions/{second_question_id}",
                headers=MENTOR_HEADERS,
            )
            topics_response = client.get(
                "/api/v1/authored/topics",
                headers=MENTOR_HEADERS,
                params={"include_archived": True},
            )
            concepts_response = client.get(
                "/api/v1/authored/concepts",
                headers=MENTOR_HEADERS,
                params={"include_archived": True},
            )
        finally:
            app.dependency_overrides.clear()

    assert archive_concept_response.status_code == 200
    assert archive_concept_response.json()["current_status"] == "archived"
    assert archive_concept_response.json()["archived_question_count"] == 1
    assert question_after_concept_archive.status_code == 200
    assert question_after_concept_archive.json()["question"]["status"] == "archived"

    assert archive_topic_response.status_code == 200
    assert archive_topic_response.json()["current_status"] == "archived"
    assert archive_topic_response.json()["archived_concept_count"] == 1
    assert archive_topic_response.json()["archived_question_count"] == 1
    assert question_after_topic_archive.status_code == 200
    assert question_after_topic_archive.json()["question"]["status"] == "archived"
    assert any(item["slug"] == "technical" and item["status"] == "archived" for item in topics_response.json())
    assert any(item["slug"] == "debugging" and item["status"] == "archived" for item in concepts_response.json())


def test_archived_questions_are_terminal(tmp_path: Path) -> None:
    _configure_isolated_session(tmp_path)

    with TestClient(app) as client:
        try:
            create_response = client.post(
                "/api/v1/authored/questions",
                headers=MENTOR_HEADERS,
                json={
                    "topic": {
                        "slug": "operations",
                        "title": "Operations",
                        "description": "Operations interview topics.",
                    },
                    "concept": {
                        "topic_slug": "operations",
                        "slug": "tradeoffs",
                        "title": "Tradeoffs",
                        "definition": "Operational tradeoff framing.",
                        "difficulty": "foundational",
                    },
                    "question": {
                        "concept_slug": "tradeoffs",
                        "assessment_mode": "short_answer",
                        "difficulty": "foundational",
                        "prompt": "How do you explain a speed versus quality tradeoff?",
                        "payload": {
                            "question_type": "short_answer",
                            "prompt": "How do you explain a speed versus quality tradeoff?",
                        },
                    },
                    "rubric": {
                        "scoring_style": "rubric",
                        "criteria": [{"name": "balance", "description": "Frames both sides clearly.", "weight": 1.0, "min_score": 0, "max_score": 4}],
                        "thresholds": [{"band": "needs_review", "min_percentage": 0}],
                    },
                    "expected_answer": {
                        "answer_text": "Good answers define the constraint and choose intentionally.",
                        "key_points": ["constraint", "intentional choice"],
                    },
                },
            )
            question_id = create_response.json()["question"]["id"]

            archive_response = client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                headers=MENTOR_HEADERS,
                json={"status": "archived"},
            )
            reopen_response = client.post(
                f"/api/v1/authored/questions/{question_id}/status",
                headers=MENTOR_HEADERS,
                json={"status": "draft"},
            )
        finally:
            app.dependency_overrides.clear()

    assert archive_response.status_code == 200
    assert archive_response.json()["current_status"] == "archived"
    assert reopen_response.status_code == 400
    assert "Cannot transition authored question from `archived` to `draft`." == reopen_response.json()["detail"]
