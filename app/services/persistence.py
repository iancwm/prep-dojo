from __future__ import annotations

from dataclasses import dataclass
import uuid

from fastapi import HTTPException
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
from app.seeds.reference_data import (
    PRIMARY_REFERENCE_QUESTION_ID,
    SECONDARY_REFERENCE_QUESTION_ID,
    build_reference_question_catalog,
    get_reference_follow_up_question_bundle,
    get_reference_module,
)
from app.services.scoring import score_attempt_for_question

REFERENCE_STUDENT_EMAIL = "reference-student@prep-dojo.local"


@dataclass
class PersistedAttemptResult:
    attempt_id: str
    session_id: str
    question_id: str
    score: ScoreResult
    feedback: FeedbackResult


@dataclass
class ReferenceCatalog:
    topic: Topic
    concepts_by_id: dict
    questions_by_external_id: dict
    rubrics_by_question_id: dict
    expected_answers_by_question_id: dict
    common_mistakes_by_question_id: dict


def persist_reference_attempt(session: Session, attempt: StudentAttemptCreate) -> PersistedAttemptResult:
    catalog = ensure_reference_catalog(session)
    question_row = catalog.questions_by_external_id.get(attempt.question_id)
    if question_row is None:
        raise HTTPException(status_code=404, detail="Unknown reference question.")

    return _persist_attempt_for_question(
        session=session,
        attempt=attempt,
        question_row=question_row,
        rubric=catalog.rubrics_by_question_id[question_row.id],
        expected_answer=catalog.expected_answers_by_question_id[question_row.id],
        common_mistakes=catalog.common_mistakes_by_question_id.get(question_row.id, []),
        topic_id=catalog.topic.id,
        concept_slug=catalog.concepts_by_id[question_row.concept_id].slug,
        session_source="reference-module",
    )


def persist_authored_attempt(
    session: Session,
    question_id: str,
    attempt: StudentAttemptCreate,
) -> PersistedAttemptResult:
    try:
        parsed_id = uuid.UUID(question_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Unknown authored question.") from exc

    question_row = session.scalar(select(Question).where(Question.id == parsed_id, Question.external_id.is_(None)))
    if question_row is None:
        raise HTTPException(status_code=404, detail="Unknown authored question.")

    rubric = session.scalar(select(Rubric).where(Rubric.question_id == question_row.id))
    expected_answer = session.scalar(select(ExpectedAnswer).where(ExpectedAnswer.question_id == question_row.id))
    if rubric is None or expected_answer is None:
        raise HTTPException(status_code=500, detail="Authored question is missing required scoring artifacts.")

    common_mistakes = session.scalars(select(CommonMistake).where(CommonMistake.question_id == question_row.id)).all()
    return _persist_attempt_for_question(
        session=session,
        attempt=attempt,
        question_row=question_row,
        rubric=rubric,
        expected_answer=expected_answer,
        common_mistakes=common_mistakes,
        topic_id=question_row.concept.topic.id,
        concept_slug=question_row.concept.slug,
        session_source="authored-question",
    )


def _persist_attempt_for_question(
    *,
    session: Session,
    attempt: StudentAttemptCreate,
    question_row: Question,
    rubric: Rubric,
    expected_answer: ExpectedAnswer,
    common_mistakes: list[CommonMistake],
    topic_id,
    concept_slug: str,
    session_source: str,
) -> PersistedAttemptResult:
    score, feedback = score_attempt_for_question(
        attempt=attempt,
        question=question_row,
        rubric=rubric,
        expected_answer=expected_answer,
        common_mistakes=common_mistakes,
    )
    user = _get_or_create_reference_student(session)
    practice_session = _get_or_create_practice_session(session, user.id, attempt.session_id, session_source)

    attempt_row = StudentAttempt(
        student_id=user.id,
        question_id=question_row.id,
        session_id=practice_session.id,
        response_json=attempt.response.model_dump(mode="json"),
        status=attempt.status.value,
    )
    session.add(attempt_row)
    session.flush()

    session.add(
        Score(
            attempt_id=attempt_row.id,
            overall_score=score.overall_score,
            mastery_band=score.mastery_band.value,
            scoring_method=score.scoring_method.value,
            rubric_breakdown_json=[item.model_dump(mode="json") for item in score.criterion_scores],
        )
    )
    session.add(
        Feedback(
            attempt_id=attempt_row.id,
            strengths_json=feedback.strengths,
            gaps_json=feedback.gaps,
            next_step=feedback.next_step,
            feedback_json=feedback.model_dump(mode="json"),
        )
    )
    _upsert_module_progress(
        session=session,
        user_id=user.id,
        topic_id=topic_id,
        concept_slug=concept_slug,
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


def ensure_reference_catalog(session: Session) -> ReferenceCatalog:
    module = get_reference_module()
    follow_up_bundle = get_reference_follow_up_question_bundle()
    question_seeds = {
        PRIMARY_REFERENCE_QUESTION_ID: module.question_bundle,
        SECONDARY_REFERENCE_QUESTION_ID: follow_up_bundle,
    }

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

    assessment_mode = session.scalar(select(AssessmentMode).where(AssessmentMode.name == module.assessment_mode.mode.value))
    if assessment_mode is None:
        assessment_mode = AssessmentMode(
            name=module.assessment_mode.mode.value,
            description=module.assessment_mode.description,
            scoring_style=module.assessment_mode.scoring_style.value,
            timing_style=module.assessment_mode.timing_style.value,
        )
        session.add(assessment_mode)
        session.flush()

    questions_by_external_id = {}
    rubrics_by_question_id = {}
    expected_answers_by_question_id = {}
    common_mistakes_by_question_id = {}

    for question_reference in build_reference_question_catalog():
        bundle = question_seeds[question_reference.external_id]
        question = session.scalar(select(Question).where(Question.external_id == question_reference.external_id))
        if question is None:
            question = Question(
                concept_id=concept.id,
                assessment_mode_id=assessment_mode.id,
                external_id=question_reference.external_id,
                prompt=question_reference.question.prompt,
                context=question_reference.question.context,
                difficulty=question_reference.question.difficulty.value,
                status=question_reference.question.status.value,
                author_type=question_reference.question.author_type.value,
                payload_json=question_reference.question.payload.model_dump(mode="json"),
            )
            session.add(question)
            session.flush()

        rubric = session.scalar(select(Rubric).where(Rubric.question_id == question.id))
        if rubric is None:
            rubric = Rubric(
                question_id=question.id,
                criteria_json=[criterion.model_dump(mode="json") for criterion in bundle.rubric.criteria],
                thresholds_json=[threshold.model_dump(mode="json") for threshold in bundle.rubric.thresholds],
                scoring_style=bundle.rubric.scoring_style.value,
                status=question_reference.question.status.value,
            )
            session.add(rubric)
            session.flush()

        expected_answer = session.scalar(select(ExpectedAnswer).where(ExpectedAnswer.question_id == question.id))
        if expected_answer is None:
            expected_answer = ExpectedAnswer(
                question_id=question.id,
                answer_text=bundle.expected_answer.answer_text,
                answer_outline_json=bundle.expected_answer.answer_outline,
                key_points_json=bundle.expected_answer.key_points,
                acceptable_variants_json=bundle.expected_answer.acceptable_variants,
            )
            session.add(expected_answer)
            session.flush()

        mistakes = session.scalars(select(CommonMistake).where(CommonMistake.question_id == question.id)).all()
        if not mistakes:
            for mistake in bundle.common_mistakes:
                session.add(
                    CommonMistake(
                        question_id=question.id,
                        mistake_text=mistake.mistake_text,
                        why_it_is_wrong=mistake.why_it_is_wrong,
                        remediation_hint=mistake.remediation_hint,
                    )
                )
            session.flush()
            mistakes = session.scalars(select(CommonMistake).where(CommonMistake.question_id == question.id)).all()

        questions_by_external_id[question_reference.external_id] = question
        rubrics_by_question_id[question.id] = rubric
        expected_answers_by_question_id[question.id] = expected_answer
        common_mistakes_by_question_id[question.id] = mistakes

    return ReferenceCatalog(
        topic=topic,
        concepts_by_id={concept.id: concept},
        questions_by_external_id=questions_by_external_id,
        rubrics_by_question_id=rubrics_by_question_id,
        expected_answers_by_question_id=expected_answers_by_question_id,
        common_mistakes_by_question_id=common_mistakes_by_question_id,
    )


def _get_or_create_reference_student(session: Session) -> User:
    user = session.scalar(select(User).where(User.email == REFERENCE_STUDENT_EMAIL))
    if user is None:
        user = User(role=UserRole.STUDENT.value, email=REFERENCE_STUDENT_EMAIL)
        session.add(user)
        session.flush()
    return user


def _get_or_create_practice_session(
    session: Session,
    user_id,
    client_session_id: str,
    source: str,
) -> PracticeSession:
    practice_session = session.scalar(
        select(PracticeSession).where(PracticeSession.client_session_id == client_session_id)
    )
    if practice_session is None:
        practice_session = PracticeSession(
            user_id=user_id,
            client_session_id=client_session_id,
            config_json={"source": source},
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
        session.add(
            ModuleProgress(
                student_id=user_id,
                topic_id=topic_id,
                progress_status=progress_status.value,
                concept_mastery_json=concept_mastery,
            )
        )
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
