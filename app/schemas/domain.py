from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import (
    AssessmentModeType,
    AttemptStatus,
    AuthorType,
    ContentStatus,
    DifficultyLevel,
    MasteryBand,
    ProgressStatus,
    ScoringMethod,
    ScoringStyle,
    TimingStyle,
)


class TopicCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    title: str
    description: str
    order_index: int = 0
    status: ContentStatus = ContentStatus.DRAFT


class ConceptCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_slug: str
    slug: str | None = None
    title: str
    definition: str
    difficulty: DifficultyLevel
    prerequisites: list[str] = Field(default_factory=list)
    status: ContentStatus = ContentStatus.DRAFT


class AssessmentModeDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: AssessmentModeType
    description: str
    scoring_style: ScoringStyle
    timing_style: TimingStyle


class RubricCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    weight: float = Field(gt=0)
    min_score: int = Field(ge=0)
    max_score: int = Field(ge=1)
    failure_signals: list[str] = Field(default_factory=list)
    strong_response_fragments: list[str] = Field(default_factory=list)


class MasteryThreshold(BaseModel):
    model_config = ConfigDict(extra="forbid")

    band: MasteryBand
    min_percentage: float = Field(ge=0, le=100)


class RubricDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criteria: list[RubricCriterion]
    scoring_style: ScoringStyle
    thresholds: list[MasteryThreshold]
    review_notes: str | None = None


class MCQOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    rationale: str | None = None


class MCQSinglePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_type: Literal["mcq_single"]
    prompt: str
    options: list[MCQOption]
    correct_option_id: str
    explanation: str


class ShortAnswerPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_type: Literal["short_answer"]
    prompt: str
    context: str | None = None
    max_duration_seconds: int | None = Field(default=None, ge=15)
    response_guidance: list[str] = Field(default_factory=list)


class OralRecallPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_type: Literal["oral_recall"]
    prompt: str
    cue: str | None = None
    target_duration_seconds: int | None = Field(default=None, ge=15)


QuestionPayload = Annotated[
    MCQSinglePayload | ShortAnswerPayload | OralRecallPayload,
    Field(discriminator="question_type"),
]


class QuestionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_slug: str
    external_id: str | None = None
    assessment_mode: AssessmentModeType
    difficulty: DifficultyLevel
    author_type: AuthorType = AuthorType.HUMAN
    status: ContentStatus = ContentStatus.DRAFT
    prompt: str
    context: str | None = None
    payload: QuestionPayload


class ExpectedAnswerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_text: str
    answer_outline: list[str] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)
    acceptable_variants: list[str] = Field(default_factory=list)


class CommonMistakeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mistake_text: str
    why_it_is_wrong: str
    remediation_hint: str


class TopicRecord(TopicCreate):
    id: str


class ConceptRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    topic_slug: str
    slug: str
    title: str
    definition: str
    difficulty: DifficultyLevel
    prerequisites: list[str] = Field(default_factory=list)
    status: ContentStatus


class QuestionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    concept_slug: str
    external_id: str | None = None
    assessment_mode: AssessmentModeType
    difficulty: DifficultyLevel
    author_type: AuthorType
    status: ContentStatus
    prompt: str
    context: str | None = None
    payload: QuestionPayload
    version: int


class AuthoredQuestionBundleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: TopicCreate
    concept: ConceptCreate
    question: QuestionCreate
    rubric: RubricDefinition
    expected_answer: ExpectedAnswerCreate
    common_mistakes: list[CommonMistakeCreate] = Field(default_factory=list)


class AuthoredQuestionBundleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: TopicRecord
    concept: ConceptRecord
    assessment_mode: AssessmentModeDefinition
    question: QuestionRecord
    rubric: RubricDefinition
    expected_answer: ExpectedAnswerCreate
    common_mistakes: list[CommonMistakeCreate] = Field(default_factory=list)


class ContentStatusTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ContentStatus
    review_notes: str | None = None


class ContentStatusTransitionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    previous_status: ContentStatus
    current_status: ContentStatus
    review_notes: str | None = None


class AuthoredQuestionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    topic_slug: str
    concept_slug: str
    assessment_mode: AssessmentModeType
    difficulty: DifficultyLevel
    status: ContentStatus
    prompt: str
    version: int


class MultipleChoiceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    response_type: Literal["multiple_choice"]
    selected_option_id: str


class FreeTextResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    response_type: Literal["free_text"]
    content: str


class OralResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    response_type: Literal["oral_transcript"]
    transcript: str
    duration_seconds: int | None = Field(default=None, ge=1)


AttemptResponse = Annotated[
    MultipleChoiceResponse | FreeTextResponse | OralResponse,
    Field(discriminator="response_type"),
]


class StudentAttemptCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    session_id: str
    response: AttemptResponse
    status: AttemptStatus = AttemptStatus.SUBMITTED


class CriterionScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion_name: str
    score: int = Field(ge=0)
    max_score: int = Field(ge=1)
    notes: str | None = None


class ScoreResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_score: float = Field(ge=0, le=100)
    mastery_band: MasteryBand
    scoring_method: ScoringMethod
    criterion_scores: list[CriterionScore]


class FeedbackResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    next_step: str
    remediation_hints: list[str] = Field(default_factory=list)


class ModuleProgressSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_id: str
    topic_id: str
    progress_status: ProgressStatus
    concept_mastery: dict[str, MasteryBand] = Field(default_factory=dict)


class PracticeSessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str | None = None
    source: str = "practice-session"


class PracticeSessionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    source: str
    started_at: datetime
    completed_at: datetime | None = None
    attempt_count: int = 0


class PracticeSessionAttemptSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attempt_id: str
    question_id: str
    prompt: str
    response_type: str
    status: AttemptStatus
    submitted_at: datetime
    overall_score: float | None = None
    mastery_band: MasteryBand | None = None


class PracticeSessionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    user_id: str
    source: str
    started_at: datetime
    completed_at: datetime | None = None
    attempts: list[PracticeSessionAttemptSummary] = Field(default_factory=list)


class ReferenceQuestionBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: QuestionCreate
    rubric: RubricDefinition
    expected_answer: ExpectedAnswerCreate
    common_mistakes: list[CommonMistakeCreate] = Field(default_factory=list)
    sample_attempt: StudentAttemptCreate
    sample_score: ScoreResult
    sample_feedback: FeedbackResult


class ReferenceModule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: TopicCreate
    concept: ConceptCreate
    assessment_mode: AssessmentModeDefinition
    question_bundle: ReferenceQuestionBundle


class StoredQuestionReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_id: str
    question: QuestionCreate


def build_reference_assessment_modes() -> list[AssessmentModeDefinition]:
    return [
        AssessmentModeDefinition(
            mode=AssessmentModeType.MULTIPLE_CHOICE,
            description="Low-latency factual and applied recall with one correct option.",
            scoring_style=ScoringStyle.AUTOMATIC,
            timing_style=TimingStyle.TIMED,
        ),
        AssessmentModeDefinition(
            mode=AssessmentModeType.SHORT_ANSWER,
            description="Written explanation scored against a rubric.",
            scoring_style=ScoringStyle.RUBRIC,
            timing_style=TimingStyle.TIMED,
        ),
        AssessmentModeDefinition(
            mode=AssessmentModeType.ORAL_RECALL,
            description="Spoken interview-style recall judged on correctness and clarity.",
            scoring_style=ScoringStyle.HYBRID,
            timing_style=TimingStyle.LIVE,
        ),
        AssessmentModeDefinition(
            mode=AssessmentModeType.CASE_PROMPT,
            description="Scenario-based reasoning that tests application under pressure.",
            scoring_style=ScoringStyle.RUBRIC,
            timing_style=TimingStyle.TIMED,
        ),
        AssessmentModeDefinition(
            mode=AssessmentModeType.MODELING_EXERCISE,
            description="Applied finance task scored on output and reasoning.",
            scoring_style=ScoringStyle.MANUAL,
            timing_style=TimingStyle.LIVE,
        ),
    ]
