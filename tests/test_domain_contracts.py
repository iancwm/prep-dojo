from app.core.enums import AssessmentModeType, MasteryBand, ScoringMethod
from app.schemas.domain import (
    FeedbackResult,
    QuestionCreate,
    RubricCriterion,
    RubricDefinition,
    ScoreResult,
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
