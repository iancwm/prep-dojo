from fastapi.testclient import TestClient

from app.core.enums import AssessmentModeType, MasteryBand, ScoringMethod
from app.main import app
from app.seeds.reference_data import (
    PRIMARY_REFERENCE_QUESTION_ID,
    SECONDARY_REFERENCE_QUESTION_ID,
    build_reference_question_catalog,
    get_reference_follow_up_question_bundle,
    get_reference_module,
    get_reference_progress_snapshot,
)
from app.services.scoring import REFERENCE_QUESTION_ID, score_reference_attempt
from app.schemas.domain import (
    AuthoredQuestionBundleCreate,
    FeedbackResult,
    QuestionCreate,
    RubricCriterion,
    RubricDefinition,
    ScoreResult,
    StudentAttemptCreate,
)


def test_short_answer_question_payload_uses_discriminated_union() -> None:
    question = QuestionCreate.model_validate(
        {
            "concept_slug": "enterprise-value-vs-equity-value",
            "assessment_mode": AssessmentModeType.SHORT_ANSWER,
            "difficulty": "intermediate",
            "prompt": "Explain why enterprise value is useful in valuation multiples.",
            "payload": {
                "question_type": "short_answer",
                "prompt": "Explain why enterprise value is useful in valuation multiples.",
                "response_guidance": [
                    "Define enterprise value",
                    "Contrast it with equity value",
                    "Explain why interviewers care",
                ],
            },
        }
    )

    assert question.payload.question_type == "short_answer"


def test_rubric_definition_accepts_thresholds_and_criteria() -> None:
    rubric = RubricDefinition.model_validate(
        {
            "scoring_style": "rubric",
            "criteria": [
                {
                    "name": "reasoning",
                    "description": "Explains why EV normalizes capital structure.",
                    "weight": 0.4,
                    "min_score": 0,
                    "max_score": 4,
                    "failure_signals": ["Defines EV without using it"],
                    "strong_response_fragments": ["normalizes capital structure"],
                }
            ],
            "thresholds": [
                {"band": "needs_review", "min_percentage": 0},
                {"band": "interview_ready", "min_percentage": 80},
            ],
        }
    )

    assert rubric.criteria[0] == RubricCriterion(
        name="reasoning",
        description="Explains why EV normalizes capital structure.",
        weight=0.4,
        min_score=0,
        max_score=4,
        failure_signals=["Defines EV without using it"],
        strong_response_fragments=["normalizes capital structure"],
    )


def test_authored_question_bundle_contract_accepts_topic_concept_and_scoring_artifacts() -> None:
    bundle = AuthoredQuestionBundleCreate.model_validate(
        {
            "topic": {
                "slug": "accounting",
                "title": "Accounting",
                "description": "Core accounting concepts for finance interviews.",
            },
            "concept": {
                "topic_slug": "accounting",
                "slug": "working-capital",
                "title": "Working Capital",
                "definition": "Short-term operating assets minus operating liabilities.",
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
                    "response_guidance": ["Explain the cash outflow", "Tie it to working capital"],
                },
            },
            "rubric": {
                "scoring_style": "rubric",
                "criteria": [
                    {
                        "name": "reasoning",
                        "description": "Explains the cash flow implication.",
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
                "answer_text": "Inventory is a use of cash because the company pays to build inventory before revenue is recognized.",
                "answer_outline": ["Inventory build requires cash", "This is an increase in working capital"],
                "key_points": ["use of cash", "working capital"],
            },
        }
    )

    assert bundle.question.payload.question_type == "short_answer"
    assert bundle.concept.slug == "working-capital"


def test_score_and_feedback_contracts_match_assessment_framework() -> None:
    score = ScoreResult(
        overall_score=82,
        mastery_band=MasteryBand.INTERVIEW_READY,
        scoring_method=ScoringMethod.RUBRIC_MANUAL,
        criterion_scores=[
            {
                "criterion_name": "clarity",
                "score": 4,
                "max_score": 5,
                "notes": "Answer stayed concise under time pressure.",
            }
        ],
    )
    feedback = FeedbackResult(
        strengths=["Good contrast between EV and equity value."],
        gaps=["Did not explain why capital structure matters."],
        next_step="Retry the answer out loud in 30 seconds.",
        remediation_hints=["Tie the answer back to interview context."],
    )

    assert score.overall_score == 82
    assert score.criterion_scores[0].criterion_name == "clarity"
    assert feedback.next_step == "Retry the answer out loud in 30 seconds."


def test_reference_module_exercises_finance_model_with_real_data() -> None:
    module = get_reference_module()
    feedback_text = " ".join(
        [
            module.question_bundle.sample_feedback.next_step,
            *module.question_bundle.sample_feedback.gaps,
            *module.question_bundle.sample_feedback.remediation_hints,
        ]
    ).lower()

    assert module.topic.slug == "valuation"
    assert module.concept.topic_slug == "valuation"
    assert module.question_bundle.question.payload.question_type == "short_answer"
    assert module.question_bundle.rubric.criteria[0].name == "recall"
    assert module.question_bundle.sample_score.mastery_band == MasteryBand.READY_FOR_RETRY
    assert "ev / ebitda" in feedback_text or "ev-based multiple" in feedback_text


def test_reference_progress_snapshot_matches_seeded_module() -> None:
    snapshot = get_reference_progress_snapshot()

    assert snapshot["topic_slug"] == "valuation"
    assert snapshot["concept_slug"] == "enterprise-value-vs-equity-value"


def test_reference_question_catalog_lists_multiple_stored_questions() -> None:
    catalog = build_reference_question_catalog()

    assert [item.external_id for item in catalog] == [
        PRIMARY_REFERENCE_QUESTION_ID,
        SECONDARY_REFERENCE_QUESTION_ID,
    ]


def test_scoring_service_returns_interview_ready_for_strong_answer() -> None:
    attempt = StudentAttemptCreate.model_validate(
        {
            "question_id": REFERENCE_QUESTION_ID,
            "session_id": "strong-answer-session",
            "response": {
                "response_type": "free_text",
                "content": (
                    "Enterprise value reflects the operating value of the business, while equity value "
                    "is what belongs to shareholders after debt and cash are considered. EV-based "
                    "multiples like EV / EBITDA are more useful when comparing companies with different "
                    "capital structures or leverage, while equity value still matters for per-share "
                    "metrics like P / E."
                ),
            },
        }
    )

    score, feedback = score_reference_attempt(attempt)

    assert score.mastery_band == MasteryBand.INTERVIEW_READY
    assert score.overall_score >= 80
    assert feedback.strengths


def test_scoring_service_supports_second_stored_question() -> None:
    bundle = get_reference_follow_up_question_bundle()
    score, feedback = score_reference_attempt(bundle.sample_attempt)

    assert score.mastery_band == MasteryBand.INTERVIEW_READY
    assert feedback.next_step


def test_submit_reference_attempt_endpoint_returns_score_and_feedback() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/reference/modules/valuation-enterprise-value/submit",
            json={
                "question_id": REFERENCE_QUESTION_ID,
                "session_id": "session-123",
                "response": {
                    "response_type": "free_text",
                    "content": (
                        "Enterprise value is more useful than equity value because it captures the operating "
                        "business and normalizes capital structure. I would use EV / EBITDA across companies "
                        "with different debt levels, but equity value still matters for P / E."
                    ),
                },
            },
        )

    body = response.json()

    assert response.status_code == 200
    assert body["question_id"] == REFERENCE_QUESTION_ID
    assert body["score"]["overall_score"] > 0
    assert body["feedback"]["next_step"]


def test_submit_reference_attempt_endpoint_rejects_non_submitted_status() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/reference/modules/valuation-enterprise-value/submit",
            json={
                "question_id": REFERENCE_QUESTION_ID,
                "session_id": "session-bad-status",
                "status": "created",
                "response": {
                    "response_type": "free_text",
                    "content": "Enterprise value is useful for comparing businesses with different leverage.",
                },
            },
        )

    body = response.json()

    assert response.status_code == 400
    assert "submitted" in body["detail"]


def test_submit_generic_reference_question_endpoint_returns_score_and_feedback() -> None:
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/reference/questions/{SECONDARY_REFERENCE_QUESTION_ID}/submit",
            json={
                "question_id": SECONDARY_REFERENCE_QUESTION_ID,
                "session_id": "session-456",
                "response": {
                    "response_type": "free_text",
                    "content": (
                        "Equity value is more useful when the interviewer wants the shareholder lens or a "
                        "per-share metric like P / E, while enterprise value remains better for operating "
                        "comparisons across different capital structures."
                    ),
                },
            },
        )

    body = response.json()

    assert response.status_code == 200
    assert body["question_id"] == SECONDARY_REFERENCE_QUESTION_ID
    assert body["score"]["overall_score"] > 0


def test_authored_question_endpoints_create_and_fetch_bundle() -> None:
    with TestClient(app) as client:
        create_response = client.post(
            "/api/v1/authored/questions",
            json={
                "topic": {
                    "slug": "accounting",
                    "title": "Accounting",
                    "description": "Accounting topics for finance interviews.",
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
                        "response_guidance": [
                            "Explain the timing of cash leaving the business",
                            "Connect it to working capital",
                        ],
                    },
                },
                "rubric": {
                    "scoring_style": "rubric",
                    "criteria": [
                        {
                            "name": "reasoning",
                            "description": "Explains why inventory is a use of cash.",
                            "weight": 0.6,
                            "min_score": 0,
                            "max_score": 4,
                            "strong_response_fragments": ["use of cash", "working capital"],
                        },
                        {
                            "name": "clarity",
                            "description": "Structures the answer clearly.",
                            "weight": 0.4,
                            "min_score": 0,
                            "max_score": 4,
                        },
                    ],
                    "thresholds": [
                        {"band": "needs_review", "min_percentage": 0},
                        {"band": "ready_for_retry", "min_percentage": 60},
                        {"band": "interview_ready", "min_percentage": 80},
                    ],
                },
                "expected_answer": {
                    "answer_text": "An increase in inventory is a use of cash because the company spends cash before the inventory turns into revenue.",
                    "answer_outline": ["Inventory build consumes cash", "That raises working capital and reduces FCF"],
                    "key_points": ["use of cash", "working capital", "free cash flow"],
                    "acceptable_variants": ["cash is tied up in inventory"],
                },
                "common_mistakes": [
                    {
                        "mistake_text": "Inventory increase boosts free cash flow because inventory is an asset.",
                        "why_it_is_wrong": "Assets can still require cash outflows.",
                        "remediation_hint": "Trace the cash movement, not just the balance sheet label.",
                    }
                ],
            },
        )

        assert create_response.status_code == 201
        created_body = create_response.json()
        question_id = created_body["question"]["id"]

        list_response = client.get("/api/v1/authored/questions")
        assert list_response.status_code == 200
        summaries = list_response.json()

        fetch_response = client.get(f"/api/v1/authored/questions/{question_id}")
        assert fetch_response.status_code == 200
        fetched_body = fetch_response.json()

    assert created_body["question"]["prompt"] == "Why does an increase in inventory reduce free cash flow?"
    assert created_body["concept"]["slug"] == "working-capital"
    assert any(item["id"] == question_id for item in summaries)
    assert fetched_body["question"]["id"] == question_id
    assert fetched_body["question"]["status"] == "draft"
    assert fetched_body["rubric"]["criteria"][0]["name"] == "reasoning"


def test_authored_question_status_flow_requires_review_then_publish() -> None:
    with TestClient(app) as client:
        create_response = client.post(
            "/api/v1/authored/questions",
            json={
                "topic": {
                    "slug": "accounting",
                    "title": "Accounting",
                    "description": "Accounting topics for finance interviews.",
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
                        "response_guidance": [
                            "Explain the cash movement",
                            "Tie it back to working capital",
                        ],
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
                            "description": "Explains the working capital consequence.",
                            "weight": 0.5,
                            "min_score": 0,
                            "max_score": 4,
                            "strong_response_fragments": ["working capital", "cash leaves before revenue"],
                        },
                    ],
                    "thresholds": [
                        {"band": "needs_review", "min_percentage": 0},
                        {"band": "ready_for_retry", "min_percentage": 60},
                        {"band": "interview_ready", "min_percentage": 80},
                    ],
                },
                "expected_answer": {
                    "answer_text": "Inventory increases reduce free cash flow because cash is tied up before revenue is recognized.",
                    "answer_outline": ["Inventory build uses cash", "Working capital rises", "Free cash flow falls"],
                    "key_points": ["inventory", "use of cash", "working capital"],
                    "acceptable_variants": ["cash is tied up in inventory"],
                },
            },
        )
        question_id = create_response.json()["question"]["id"]

        blocked_submit_response = client.post(
            f"/api/v1/authored/questions/{question_id}/submit",
            json={
                "question_id": question_id,
                "session_id": "authored-session-123",
                "response": {
                    "response_type": "free_text",
                    "content": (
                        "An increase in inventory is a use of cash because the company spends cash before that "
                        "inventory becomes revenue. That increases working capital and reduces free cash flow."
                    ),
                },
            },
        )

        review_response = client.post(
            f"/api/v1/authored/questions/{question_id}/status",
            json={"status": "reviewed", "review_notes": "Rubric and prompt are realistic enough to publish."},
        )
        publish_response = client.post(
            f"/api/v1/authored/questions/{question_id}/status",
            json={"status": "published"},
        )
        fetch_response = client.get(f"/api/v1/authored/questions/{question_id}")

    blocked_body = blocked_submit_response.json()
    reviewed_body = review_response.json()
    published_body = publish_response.json()
    fetched_body = fetch_response.json()

    assert blocked_submit_response.status_code == 403
    assert "published" in blocked_body["detail"]
    assert review_response.status_code == 200
    assert reviewed_body["previous_status"] == "draft"
    assert reviewed_body["current_status"] == "reviewed"
    assert publish_response.status_code == 200
    assert published_body["current_status"] == "published"
    assert fetch_response.status_code == 200
    assert fetched_body["question"]["status"] == "published"
    assert fetched_body["rubric"]["review_notes"] == "Rubric and prompt are realistic enough to publish."


def test_authored_question_submit_endpoint_returns_score_and_feedback() -> None:
    with TestClient(app) as client:
        create_response = client.post(
            "/api/v1/authored/questions",
            json={
                "topic": {
                    "slug": "accounting",
                    "title": "Accounting",
                    "description": "Accounting topics for finance interviews.",
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
                        "response_guidance": [
                            "Explain the cash movement",
                            "Tie it back to working capital",
                        ],
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
                            "description": "Explains the working capital consequence.",
                            "weight": 0.5,
                            "min_score": 0,
                            "max_score": 4,
                            "strong_response_fragments": ["working capital", "cash leaves before revenue"],
                        },
                    ],
                    "thresholds": [
                        {"band": "needs_review", "min_percentage": 0},
                        {"band": "ready_for_retry", "min_percentage": 60},
                        {"band": "interview_ready", "min_percentage": 80},
                    ],
                },
                "expected_answer": {
                    "answer_text": "Inventory increases reduce free cash flow because cash is tied up before revenue is recognized.",
                    "answer_outline": ["Inventory build uses cash", "Working capital rises", "Free cash flow falls"],
                    "key_points": ["inventory", "use of cash", "working capital"],
                    "acceptable_variants": ["cash is tied up in inventory"],
                },
            },
        )
        question_id = create_response.json()["question"]["id"]
        client.post(
            f"/api/v1/authored/questions/{question_id}/status",
            json={"status": "reviewed", "review_notes": "Ready for publication."},
        )
        client.post(
            f"/api/v1/authored/questions/{question_id}/status",
            json={"status": "published"},
        )

        submit_response = client.post(
            f"/api/v1/authored/questions/{question_id}/submit",
            json={
                "question_id": question_id,
                "session_id": "authored-session-123",
                "response": {
                    "response_type": "free_text",
                    "content": (
                        "An increase in inventory is a use of cash because the company spends cash before that "
                        "inventory becomes revenue. That increases working capital and reduces free cash flow."
                    ),
                },
            },
        )

    body = submit_response.json()

    assert submit_response.status_code == 200
    assert body["question_id"] == question_id
    assert body["score"]["overall_score"] > 0
    assert body["feedback"]["next_step"]


def test_authored_multiple_choice_submit_returns_automatic_score() -> None:
    with TestClient(app) as client:
        create_response = client.post(
            "/api/v1/authored/questions",
            json={
                "topic": {
                    "slug": "valuation",
                    "title": "Valuation",
                    "description": "Valuation concepts for interviews.",
                },
                "concept": {
                    "topic_slug": "valuation",
                    "slug": "valuation-multiples",
                    "title": "Valuation Multiples",
                    "definition": "Common multiples used in interviews.",
                    "difficulty": "foundational",
                },
                "question": {
                    "concept_slug": "valuation-multiples",
                    "assessment_mode": "multiple_choice",
                    "difficulty": "foundational",
                    "prompt": "Which multiple is most useful for comparing companies with different capital structures?",
                    "payload": {
                        "question_type": "mcq_single",
                        "prompt": "Which multiple is most useful for comparing companies with different capital structures?",
                        "options": [
                            {"id": "a", "label": "P / E"},
                            {"id": "b", "label": "EV / EBITDA"},
                            {"id": "c", "label": "Dividend Yield"},
                        ],
                        "correct_option_id": "b",
                        "explanation": "EV / EBITDA neutralizes differences in leverage better than equity-value-based multiples.",
                    },
                },
                "rubric": {
                    "scoring_style": "automatic",
                    "criteria": [
                        {
                            "name": "recall",
                            "description": "Selects the correct multiple.",
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
                    "answer_text": "EV / EBITDA is best because it compares operating value independent of capital structure.",
                    "key_points": ["EV / EBITDA", "capital structure"],
                },
            },
        )
        question_id = create_response.json()["question"]["id"]
        client.post(
            f"/api/v1/authored/questions/{question_id}/status",
            json={"status": "reviewed", "review_notes": "Answer key is accurate."},
        )
        client.post(
            f"/api/v1/authored/questions/{question_id}/status",
            json={"status": "published"},
        )

        submit_response = client.post(
            f"/api/v1/authored/questions/{question_id}/submit",
            json={
                "question_id": question_id,
                "session_id": "authored-mcq-session-1",
                "response": {
                    "response_type": "multiple_choice",
                    "selected_option_id": "b",
                },
            },
        )

    body = submit_response.json()

    assert submit_response.status_code == 200
    assert body["score"]["mastery_band"] == MasteryBand.INTERVIEW_READY
    assert body["score"]["scoring_method"] == ScoringMethod.AUTOMATIC
    assert body["feedback"]["strengths"]
