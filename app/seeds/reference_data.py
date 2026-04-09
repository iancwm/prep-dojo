from app.core.enums import (
    AssessmentModeType,
    DifficultyLevel,
    MasteryBand,
    ProgressStatus,
    ScoringMethod,
)
from app.schemas.domain import (
    AssessmentModeDefinition,
    CommonMistakeCreate,
    ConceptCreate,
    FeedbackResult,
    QuestionCreate,
    ReferenceModule,
    ReferenceQuestionBundle,
    RubricDefinition,
    ScoreResult,
    StudentAttemptCreate,
    TopicCreate,
    build_reference_assessment_modes,
)


def get_reference_module() -> ReferenceModule:
    short_answer_mode = next(
        mode for mode in build_reference_assessment_modes() if mode.mode == AssessmentModeType.SHORT_ANSWER
    )

    question = QuestionCreate.model_validate(
        {
            "concept_slug": "enterprise-value-vs-equity-value",
            "assessment_mode": "short_answer",
            "difficulty": "intermediate",
            "status": "published",
            "prompt": (
                "Explain why enterprise value is used in valuation multiples and when it is "
                "more informative than equity value."
            ),
            "context": (
                "Answer as if you are in a live finance interview and need to show both "
                "technical correctness and practical judgment."
            ),
            "payload": {
                "question_type": "short_answer",
                "prompt": (
                    "Explain why enterprise value is used in valuation multiples and when it "
                    "is more informative than equity value."
                ),
                "context": (
                    "The interviewer wants to know whether you understand operating value "
                    "versus shareholder value and can explain it cleanly."
                ),
                "max_duration_seconds": 45,
                "response_guidance": [
                    "Define enterprise value and equity value",
                    "Explain capital structure normalization",
                    "State when EV-based multiples are more useful",
                    "Mention when equity value is still the better reference point",
                ],
            },
        }
    )
    rubric = RubricDefinition.model_validate(
        {
            "scoring_style": "rubric",
            "criteria": [
                {
                    "name": "recall",
                    "description": "Defines both enterprise value and equity value correctly.",
                    "weight": 0.25,
                    "min_score": 0,
                    "max_score": 4,
                    "failure_signals": ["Confuses EV with market capitalization."],
                    "strong_response_fragments": [
                        "EV captures operating business value",
                        "equity value is what belongs to shareholders",
                    ],
                },
                {
                    "name": "reasoning",
                    "description": "Explains why EV-based multiples normalize capital structure.",
                    "weight": 0.35,
                    "min_score": 0,
                    "max_score": 4,
                    "failure_signals": ["States the metric without explaining why it is useful."],
                    "strong_response_fragments": [
                        "normalizes debt versus cash differences",
                        "supports apples-to-apples operating comparisons",
                    ],
                },
                {
                    "name": "application",
                    "description": "Connects the explanation to interview or valuation use cases.",
                    "weight": 0.25,
                    "min_score": 0,
                    "max_score": 4,
                    "failure_signals": ["Never says when equity value is still relevant."],
                    "strong_response_fragments": [
                        "EV / EBITDA is useful across different capital structures",
                        "equity value still matters for per-share metrics like P/E",
                    ],
                },
                {
                    "name": "clarity",
                    "description": "Delivers the answer in a concise, pressure-resistant structure.",
                    "weight": 0.15,
                    "min_score": 0,
                    "max_score": 4,
                    "failure_signals": ["Answer rambles or mixes definitions with examples."],
                    "strong_response_fragments": [
                        "short definition first",
                        "contrast second",
                        "use case last",
                    ],
                },
            ],
            "thresholds": [
                {"band": "needs_review", "min_percentage": 0},
                {"band": "partial", "min_percentage": 40},
                {"band": "ready_for_retry", "min_percentage": 65},
                {"band": "interview_ready", "min_percentage": 80},
            ],
        }
    )
    expected_answer = {
        "answer_text": (
            "Enterprise value is usually more useful for operating valuation multiples because "
            "it reflects the value of the business independent of capital structure. Equity value "
            "only captures what belongs to shareholders after debt and cash are considered. In an "
            "interview, I would use EV-based multiples like EV / EBITDA when comparing operating "
            "performance across companies with different leverage, but I would still use equity "
            "value for per-share metrics like P / E."
        ),
        "answer_outline": [
            "Define EV",
            "Define equity value",
            "Explain capital structure normalization",
            "Name one EV-based multiple",
            "Name when equity value remains useful",
        ],
        "key_points": [
            "EV represents operating enterprise value",
            "Equity value represents residual shareholder value",
            "EV-based multiples support cleaner peer comparisons",
            "Equity value remains relevant for per-share measures",
        ],
        "acceptable_variants": [
            "Using firm value instead of enterprise value is acceptable if the logic is correct.",
            "A concise explanation that clearly distinguishes EV from market cap is acceptable.",
        ],
    }
    common_mistakes = [
        CommonMistakeCreate(
            mistake_text="Treating enterprise value as identical to market capitalization.",
            why_it_is_wrong="That drops debt and cash adjustments, which is exactly why EV exists.",
            remediation_hint="Say what EV includes before discussing multiples.",
        ),
        CommonMistakeCreate(
            mistake_text="Giving a memorized definition without explaining the interview use case.",
            why_it_is_wrong="Interviewers care whether the candidate can apply the concept, not just recite it.",
            remediation_hint="End the answer by naming a specific multiple and why it is useful.",
        ),
    ]
    sample_attempt = StudentAttemptCreate.model_validate(
        {
            "question_id": "sample-question-enterprise-value",
            "session_id": "sample-session-valuation-1",
            "response": {
                "response_type": "free_text",
                "content": (
                    "Enterprise value is the value of the company including debt, and equity "
                    "value is just the market cap. EV is better for valuation because companies "
                    "have different debt levels, while equity value is useful for per-share ratios."
                ),
            },
        }
    )
    sample_score = ScoreResult(
        overall_score=76,
        mastery_band=MasteryBand.READY_FOR_RETRY,
        scoring_method=ScoringMethod.RUBRIC_MANUAL,
        criterion_scores=[
            {
                "criterion_name": "recall",
                "score": 3,
                "max_score": 4,
                "notes": "Definitions are mostly correct but EV could be stated more precisely.",
            },
            {
                "criterion_name": "reasoning",
                "score": 3,
                "max_score": 4,
                "notes": "Capital structure point is present but not fully explained.",
            },
            {
                "criterion_name": "application",
                "score": 3,
                "max_score": 4,
                "notes": "Mentions per-share ratios but not a concrete EV-based multiple.",
            },
            {
                "criterion_name": "clarity",
                "score": 4,
                "max_score": 4,
                "notes": "Answer is concise enough for a live interview.",
            },
        ],
    )
    sample_feedback = FeedbackResult(
        strengths=[
            "You distinguished enterprise value from equity value instead of treating them as the same metric.",
            "You correctly noticed that leverage differences are why EV-based comparisons matter.",
        ],
        gaps=[
            "You did not explicitly say that EV captures the value of the operating business before financing choices.",
            "You should name a concrete multiple like EV / EBITDA to make the answer feel interview-ready.",
        ],
        next_step="Retry the same answer out loud in 30 seconds and include one EV-based multiple.",
        remediation_hints=[
            "Use a three-part structure: define, compare, apply.",
            "End with when equity value is still the right lens, such as P / E.",
        ],
    )

    return ReferenceModule(
        topic=TopicCreate(
            slug="valuation",
            title="Valuation",
            description="Core valuation concepts needed for finance interviews and technical recruiting screens.",
            order_index=1,
            status="published",
        ),
        concept=ConceptCreate(
            topic_slug="valuation",
            title="Enterprise Value vs Equity Value",
            definition=(
                "Understand the difference between operating enterprise value and residual shareholder value, "
                "and know when each metric is the right comparison tool."
            ),
            difficulty=DifficultyLevel.INTERMEDIATE,
            prerequisites=["market-capitalization", "net-debt"],
            status="published",
        ),
        assessment_mode=AssessmentModeDefinition.model_validate(short_answer_mode.model_dump(mode="json")),
        question_bundle=ReferenceQuestionBundle(
            question=question,
            rubric=rubric,
            expected_answer=expected_answer,
            common_mistakes=common_mistakes,
            sample_attempt=sample_attempt,
            sample_score=sample_score,
            sample_feedback=sample_feedback,
        ),
    )


def get_reference_progress_snapshot() -> dict[str, str]:
    return {
        "student_id": "sample-student-justin",
        "topic_slug": "valuation",
        "progress_status": ProgressStatus.IN_PROGRESS,
        "concept_slug": "enterprise-value-vs-equity-value",
        "mastery_band": MasteryBand.READY_FOR_RETRY,
    }

