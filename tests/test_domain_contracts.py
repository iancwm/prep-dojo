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
