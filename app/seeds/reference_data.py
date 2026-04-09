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
    StoredQuestionReference,
    StudentAttemptCreate,
    TopicCreate,
    build_reference_assessment_modes,
)

PRIMARY_REFERENCE_QUESTION_ID = "sample-question-enterprise-value"
SECONDARY_REFERENCE_QUESTION_ID = "sample-question-when-equity-value-matters"


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
            "question_id": PRIMARY_REFERENCE_QUESTION_ID,
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


def get_reference_follow_up_question_bundle() -> ReferenceQuestionBundle:
    question = QuestionCreate.model_validate(
        {
            "concept_slug": "enterprise-value-vs-equity-value",
            "assessment_mode": "short_answer",
            "difficulty": "intermediate",
            "status": "published",
            "prompt": "When is equity value more informative than enterprise value in an interview answer?",
            "context": (
                "The interviewer wants to know whether you understand when per-share or shareholder "
                "lenses are the right tool."
            ),
            "payload": {
                "question_type": "short_answer",
                "prompt": "When is equity value more informative than enterprise value in an interview answer?",
                "context": "Give a concise answer that mentions per-share metrics and shareholder perspective.",
                "max_duration_seconds": 30,
                "response_guidance": [
                    "State that equity value is the shareholder lens",
                    "Name a per-share metric such as P / E",
                    "Contrast that with enterprise value for operating comparisons",
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
                    "description": "Identifies equity value as the shareholder lens.",
                    "weight": 0.3,
                    "min_score": 0,
                    "max_score": 4,
                    "failure_signals": ["Uses equity value as if it were the same as enterprise value."],
                    "strong_response_fragments": [
                        "equity value reflects what belongs to shareholders",
                        "equity value matters for per-share metrics",
                    ],
                },
                {
                    "name": "application",
                    "description": "Names when equity value is the better metric in interview context.",
                    "weight": 0.4,
                    "min_score": 0,
                    "max_score": 4,
                    "failure_signals": ["Never gives a concrete metric or use case."],
                    "strong_response_fragments": [
                        "p / e",
                        "per-share",
                        "shareholder perspective",
                    ],
                },
                {
                    "name": "reasoning",
                    "description": "Contrasts equity value with enterprise value for operating comparisons.",
                    "weight": 0.2,
                    "min_score": 0,
                    "max_score": 4,
                    "failure_signals": ["Does not explain the contrast with enterprise value."],
                    "strong_response_fragments": [
                        "enterprise value is better for operating comparisons",
                        "capital structure",
                    ],
                },
                {
                    "name": "clarity",
                    "description": "Keeps the answer concise and direct.",
                    "weight": 0.1,
                    "min_score": 0,
                    "max_score": 4,
                    "failure_signals": ["Answer rambles or avoids the question."],
                    "strong_response_fragments": [
                        "direct answer",
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
            "Equity value is more informative when the interviewer wants the shareholder lens or a "
            "per-share metric such as P / E. Enterprise value is still the better tool for operating "
            "comparisons because it normalizes debt and cash."
        ),
        "answer_outline": [
            "State when equity value is relevant",
            "Name one per-share metric",
            "Contrast with enterprise value",
        ],
        "key_points": [
            "Equity value reflects shareholder value",
            "P / E is an equity value metric",
            "Enterprise value is better for operating comparisons",
        ],
        "acceptable_variants": [
            "Market capitalization is acceptable shorthand if the shareholder lens is made explicit."
        ],
    }
    common_mistakes = [
        CommonMistakeCreate(
            mistake_text="Using equity value for every valuation discussion.",
            why_it_is_wrong="That misses the operating comparison use case where enterprise value is more useful.",
            remediation_hint="Always say when EV remains the better comparison lens.",
        )
    ]
    return ReferenceQuestionBundle(
        question=question,
        rubric=rubric,
        expected_answer=expected_answer,
        common_mistakes=common_mistakes,
        sample_attempt=StudentAttemptCreate.model_validate(
            {
                "question_id": SECONDARY_REFERENCE_QUESTION_ID,
                "session_id": "sample-session-valuation-2",
                "response": {
                    "response_type": "free_text",
                    "content": (
                        "Equity value matters when you are using per-share metrics like P / E and want the "
                        "shareholder perspective, but enterprise value is still better for operating "
                        "comparisons across leverage."
                    ),
                },
            }
        ),
        sample_score=ScoreResult(
            overall_score=84,
            mastery_band=MasteryBand.INTERVIEW_READY,
            scoring_method=ScoringMethod.RUBRIC_MANUAL,
            criterion_scores=[
                {"criterion_name": "recall", "score": 4, "max_score": 4, "notes": "Clear shareholder lens."},
                {"criterion_name": "application", "score": 4, "max_score": 4, "notes": "Names P / E directly."},
                {"criterion_name": "reasoning", "score": 3, "max_score": 4, "notes": "Contrasts with EV."},
                {"criterion_name": "clarity", "score": 4, "max_score": 4, "notes": "Concise and direct."},
            ],
        ),
        sample_feedback=FeedbackResult(
            strengths=["The answer makes the shareholder lens explicit.", "You named a concrete metric."],
            gaps=[],
            next_step="Pair this answer with the EV comparison question in a timed drill.",
            remediation_hints=[],
        ),
    )


def build_reference_question_catalog() -> list[StoredQuestionReference]:
    primary = get_reference_module().question_bundle.question
    secondary = get_reference_follow_up_question_bundle().question
    return [
        StoredQuestionReference(external_id=PRIMARY_REFERENCE_QUESTION_ID, question=primary),
        StoredQuestionReference(external_id=SECONDARY_REFERENCE_QUESTION_ID, question=secondary),
    ]


def get_reference_progress_snapshot() -> dict[str, str]:
    return {
        "student_id": "sample-student-justin",
        "topic_slug": "valuation",
        "progress_status": ProgressStatus.IN_PROGRESS,
        "concept_slug": "enterprise-value-vs-equity-value",
        "mastery_band": MasteryBand.READY_FOR_RETRY,
    }
