from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import ProgressStatus, UserRole
from app.db.models import (
    AssessmentMode,
    CommonMistake,
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
    User,
)
from app.schemas.domain import FeedbackResult, ScoreResult, StudentAttemptCreate
from app.seeds.reference_data import get_reference_module
from app.services.scoring import REFERENCE_QUESTION_ID, score_reference_attempt

REFERENCE_STUDENT_EMAIL = "reference-student@prep-dojo.local"


@dataclass
class PersistedAttemptResult:
    attempt_id: str
    session_id: str
    question_id: str
    score: ScoreResult
    feedback: FeedbackResult


def persist_reference_attempt(session: Session, attempt: StudentAttemptCreate) -> PersistedAttemptResult:
    score, feedback = score_reference_attempt(attempt)
    catalog = ensure_reference_catalog(session)
    user = _get_or_create_reference_student(session)
    practice_session = _get_or_create_practice_session(session, user.id, attempt.session_id)

    attempt_row = StudentAttempt(
        student_id=user.id,
        question_id=catalog.question.id,
        session_id=practice_session.id,
        response_json=attempt.response.model_dump(mode="json"),
        status=attempt.status.value,
    )
    session.add(attempt_row)
    session.flush()

    score_row = Score(
        attempt_id=attempt_row.id,
        overall_score=score.overall_score,
        mastery_band=score.mastery_band.value,
        scoring_method=score.scoring_method.value,
        rubric_breakdown_json=[item.model_dump(mode="json") for item in score.criterion_scores],
    )
    feedback_row = Feedback(
        attempt_id=attempt_row.id,
        strengths_json=feedback.strengths,
        gaps_json=feedback.gaps,
        next_step=feedback.next_step,
        feedback_json=feedback.model_dump(mode="json"),
    )
    session.add(score_row)
    session.add(feedback_row)
    _upsert_module_progress(
        session=session,
        user_id=user.id,
        topic_id=catalog.topic.id,
        concept_slug=catalog.concept.slug,
        mastery_band=score.mastery_band.value,
    )
    session.commit()
    session.refresh(attempt_row)

    return PersistedAttemptResult(
        attempt_id=str(attempt_row.id),
        session_id=attempt.session_id,
        question_id=attempt.question_id,
        score=score,
        feedback=feedback,
    )


@dataclass
class ReferenceCatalog:
    topic: Topic
    concept: Concept
    assessment_mode: AssessmentMode
    question: Question


def ensure_reference_catalog(session: Session) -> ReferenceCatalog:
    module = get_reference_module()

    topic = session.scalar(select(Topic).where(Topic.slug == module.topic.slug))
    if topic is None:
        topic = Topic(
            slug=module.topic.slug,
            title=module.topic.title,
            description=module.topic.description,
            order_index=module.topic.order_index,
            status=module.topic.status.value,
        )
        session.add(topic)
        session.flush()

    concept = session.scalar(select(Concept).where(Concept.slug == _slugify_concept_title(module.concept.title)))
    if concept is None:
        concept = Concept(
            topic_id=topic.id,
            slug=_slugify_concept_title(module.concept.title),
            title=module.concept.title,
            definition=module.concept.definition,
            difficulty=module.concept.difficulty.value,
            prerequisites_json=module.concept.prerequisites,
            status=module.concept.status.value,
        )
        session.add(concept)
        session.flush()

    assessment_mode = session.scalar(
        select(AssessmentMode).where(AssessmentMode.name == module.assessment_mode.mode.value)
    )
    if assessment_mode is None:
        assessment_mode = AssessmentMode(
            name=module.assessment_mode.mode.value,
            description=module.assessment_mode.description,
            scoring_style=module.assessment_mode.scoring_style.value,
            timing_style=module.assessment_mode.timing_style.value,
        )
        session.add(assessment_mode)
        session.flush()

    question = session.scalar(select(Question).where(Question.external_id == REFERENCE_QUESTION_ID))
    if question is None:
        question = Question(
            concept_id=concept.id,
            assessment_mode_id=assessment_mode.id,
            external_id=REFERENCE_QUESTION_ID,
            prompt=module.question_bundle.question.prompt,
            context=module.question_bundle.question.context,
            difficulty=module.question_bundle.question.difficulty.value,
            status=module.question_bundle.question.status.value,
            author_type=module.question_bundle.question.author_type.value,
            payload_json=module.question_bundle.question.payload.model_dump(mode="json"),
        )
        session.add(question)
        session.flush()

    rubric = session.scalar(select(Rubric).where(Rubric.question_id == question.id))
    if rubric is None:
        rubric = Rubric(
            question_id=question.id,
            criteria_json=[criterion.model_dump(mode="json") for criterion in module.question_bundle.rubric.criteria],
            thresholds_json=[
                threshold.model_dump(mode="json") for threshold in module.question_bundle.rubric.thresholds
            ],
            scoring_style=module.question_bundle.rubric.scoring_style.value,
            status=module.question_bundle.question.status.value,
        )
        session.add(rubric)

    expected_answer = session.scalar(select(ExpectedAnswer).where(ExpectedAnswer.question_id == question.id))
    if expected_answer is None:
        expected_answer = ExpectedAnswer(
            question_id=question.id,
            answer_text=module.question_bundle.expected_answer.answer_text,
            answer_outline_json=module.question_bundle.expected_answer.answer_outline,
            key_points_json=module.question_bundle.expected_answer.key_points,
            acceptable_variants_json=module.question_bundle.expected_answer.acceptable_variants,
        )
        session.add(expected_answer)

    existing_mistakes = session.scalars(select(CommonMistake).where(CommonMistake.question_id == question.id)).all()
    if not existing_mistakes:
        for mistake in module.question_bundle.common_mistakes:
            session.add(
                CommonMistake(
                    question_id=question.id,
                    mistake_text=mistake.mistake_text,
                    why_it_is_wrong=mistake.why_it_is_wrong,
                    remediation_hint=mistake.remediation_hint,
                )
            )

    session.flush()
    return ReferenceCatalog(
        topic=topic,
        concept=concept,
        assessment_mode=assessment_mode,
        question=question,
    )


def _get_or_create_reference_student(session: Session) -> User:
    user = session.scalar(select(User).where(User.email == REFERENCE_STUDENT_EMAIL))
    if user is None:
        user = User(role=UserRole.STUDENT.value, email=REFERENCE_STUDENT_EMAIL)
        session.add(user)
        session.flush()
    return user


def _get_or_create_practice_session(session: Session, user_id, client_session_id: str) -> PracticeSession:
    practice_session = session.scalar(
        select(PracticeSession).where(PracticeSession.client_session_id == client_session_id)
    )
    if practice_session is None:
        practice_session = PracticeSession(
            user_id=user_id,
            client_session_id=client_session_id,
            config_json={"source": "reference-module"},
        )
        session.add(practice_session)
        session.flush()
    return practice_session


def _upsert_module_progress(
    session: Session,
    user_id,
    topic_id,
    concept_slug: str,
    mastery_band: str,
) -> None:
    progress = session.scalar(
        select(ModuleProgress).where(
            ModuleProgress.student_id == user_id,
            ModuleProgress.topic_id == topic_id,
        )
    )
    concept_mastery = {concept_slug: mastery_band}
    progress_status = _progress_status_from_mastery(mastery_band)
    if progress is None:
        progress = ModuleProgress(
            student_id=user_id,
            topic_id=topic_id,
            progress_status=progress_status.value,
            concept_mastery_json=concept_mastery,
        )
        session.add(progress)
        return

    progress.concept_mastery_json = {**progress.concept_mastery_json, **concept_mastery}
    progress.progress_status = progress_status.value


def _progress_status_from_mastery(mastery_band: str) -> ProgressStatus:
    if mastery_band == "interview_ready":
        return ProgressStatus.STRONG
    if mastery_band == "ready_for_retry":
        return ProgressStatus.IN_PROGRESS
    return ProgressStatus.WEAK


def _slugify_concept_title(title: str) -> str:
    return title.lower().replace(" ", "-")
