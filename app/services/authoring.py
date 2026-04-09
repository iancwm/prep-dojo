from __future__ import annotations

import re
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AssessmentMode, CommonMistake, Concept, ExpectedAnswer, Question, Rubric, Topic
from app.schemas.domain import (
    AssessmentModeDefinition,
    AuthoredQuestionBundleCreate,
    AuthoredQuestionBundleRecord,
    AuthoredQuestionSummary,
    CommonMistakeCreate,
    ConceptRecord,
    ExpectedAnswerCreate,
    QuestionRecord,
    RubricCriterion,
    RubricDefinition,
    TopicRecord,
    build_reference_assessment_modes,
)


def create_authored_question_bundle(
    session: Session,
    payload: AuthoredQuestionBundleCreate,
) -> AuthoredQuestionBundleRecord:
    _validate_bundle_contract(payload)

    topic = _get_or_create_topic(session, payload)
    concept = _get_or_create_concept(session, payload, topic.id)
    assessment_mode = _get_or_create_assessment_mode(session, payload.question.assessment_mode.value)

    question = Question(
        concept_id=concept.id,
        assessment_mode_id=assessment_mode.id,
        external_id=payload.question.external_id,
        prompt=payload.question.prompt,
        context=payload.question.context,
        difficulty=payload.question.difficulty.value,
        status=payload.question.status.value,
        author_type=payload.question.author_type.value,
        payload_json=payload.question.payload.model_dump(mode="json"),
    )
    session.add(question)
    session.flush()

    session.add(
        Rubric(
            question_id=question.id,
            criteria_json=[criterion.model_dump(mode="json") for criterion in payload.rubric.criteria],
            thresholds_json=[threshold.model_dump(mode="json") for threshold in payload.rubric.thresholds],
            scoring_style=payload.rubric.scoring_style.value,
            status=payload.question.status.value,
        )
    )
    session.add(
        ExpectedAnswer(
            question_id=question.id,
            answer_text=payload.expected_answer.answer_text,
            answer_outline_json=payload.expected_answer.answer_outline,
            key_points_json=payload.expected_answer.key_points,
            acceptable_variants_json=payload.expected_answer.acceptable_variants,
        )
    )
    for mistake in payload.common_mistakes:
        session.add(
            CommonMistake(
                question_id=question.id,
                mistake_text=mistake.mistake_text,
                why_it_is_wrong=mistake.why_it_is_wrong,
                remediation_hint=mistake.remediation_hint,
            )
        )

    session.commit()
    session.refresh(question)
    return get_authored_question_bundle(session, str(question.id))


def list_authored_question_summaries(session: Session) -> list[AuthoredQuestionSummary]:
    authored_questions = session.scalars(
        select(Question).where(Question.external_id.is_(None)).order_by(Question.created_at.desc())
    ).all()
    return [
        AuthoredQuestionSummary(
            id=str(question.id),
            topic_slug=question.concept.topic.slug,
            concept_slug=question.concept.slug,
            assessment_mode=question.assessment_mode.name,
            difficulty=question.difficulty,
            status=question.status,
            prompt=question.prompt,
            version=question.version,
        )
        for question in authored_questions
    ]


def get_authored_question_bundle(session: Session, question_id: str) -> AuthoredQuestionBundleRecord:
    try:
        parsed_id = uuid.UUID(question_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Unknown authored question.") from exc

    question = session.scalar(select(Question).where(Question.id == parsed_id, Question.external_id.is_(None)))
    if question is None:
        raise HTTPException(status_code=404, detail="Unknown authored question.")

    if question.rubric is None or question.expected_answer is None:
        raise HTTPException(status_code=500, detail="Authored question is missing required scoring artifacts.")

    return AuthoredQuestionBundleRecord(
        topic=TopicRecord(
            id=str(question.concept.topic.id),
            slug=question.concept.topic.slug,
            title=question.concept.topic.title,
            description=question.concept.topic.description,
            order_index=question.concept.topic.order_index,
            status=question.concept.topic.status,
        ),
        concept=ConceptRecord(
            id=str(question.concept.id),
            topic_slug=question.concept.topic.slug,
            slug=question.concept.slug,
            title=question.concept.title,
            definition=question.concept.definition,
            difficulty=question.concept.difficulty,
            prerequisites=question.concept.prerequisites_json,
            status=question.concept.status,
        ),
        assessment_mode=AssessmentModeDefinition(
            mode=question.assessment_mode.name,
            description=question.assessment_mode.description,
            scoring_style=question.assessment_mode.scoring_style,
            timing_style=question.assessment_mode.timing_style,
        ),
        question=QuestionRecord(
            id=str(question.id),
            concept_slug=question.concept.slug,
            external_id=question.external_id,
            assessment_mode=question.assessment_mode.name,
            difficulty=question.difficulty,
            author_type=question.author_type,
            status=question.status,
            prompt=question.prompt,
            context=question.context,
            payload=question.payload_json,
            version=question.version,
        ),
        rubric=RubricDefinition(
            criteria=[RubricCriterion.model_validate(item) for item in question.rubric.criteria_json],
            scoring_style=question.rubric.scoring_style,
            thresholds=question.rubric.thresholds_json,
        ),
        expected_answer=ExpectedAnswerCreate(
            answer_text=question.expected_answer.answer_text,
            answer_outline=question.expected_answer.answer_outline_json,
            key_points=question.expected_answer.key_points_json,
            acceptable_variants=question.expected_answer.acceptable_variants_json,
        ),
        common_mistakes=[
            CommonMistakeCreate(
                mistake_text=item.mistake_text,
                why_it_is_wrong=item.why_it_is_wrong,
                remediation_hint=item.remediation_hint,
            )
            for item in question.common_mistakes
        ],
    )


def _validate_bundle_contract(payload: AuthoredQuestionBundleCreate) -> None:
    concept_slug = payload.concept.slug or _slugify(payload.concept.title)
    if payload.concept.topic_slug != payload.topic.slug:
        raise HTTPException(status_code=400, detail="Concept topic_slug must match the parent topic slug.")
    if payload.question.concept_slug != concept_slug:
        raise HTTPException(status_code=400, detail="Question concept_slug must match the concept slug.")
    if payload.question.payload.prompt != payload.question.prompt:
        raise HTTPException(status_code=400, detail="Question payload prompt must match the question prompt.")


def _get_or_create_topic(session: Session, payload: AuthoredQuestionBundleCreate) -> Topic:
    topic = session.scalar(select(Topic).where(Topic.slug == payload.topic.slug))
    if topic is None:
        topic = Topic(
            slug=payload.topic.slug,
            title=payload.topic.title,
            description=payload.topic.description,
            order_index=payload.topic.order_index,
            status=payload.topic.status.value,
        )
        session.add(topic)
        session.flush()
        return topic

    topic.title = payload.topic.title
    topic.description = payload.topic.description
    topic.order_index = payload.topic.order_index
    topic.status = payload.topic.status.value
    session.flush()
    return topic


def _get_or_create_concept(session: Session, payload: AuthoredQuestionBundleCreate, topic_id) -> Concept:
    concept_slug = payload.concept.slug or _slugify(payload.concept.title)
    concept = session.scalar(select(Concept).where(Concept.slug == concept_slug))
    if concept is None:
        concept = Concept(
            topic_id=topic_id,
            slug=concept_slug,
            title=payload.concept.title,
            definition=payload.concept.definition,
            difficulty=payload.concept.difficulty.value,
            prerequisites_json=payload.concept.prerequisites,
            status=payload.concept.status.value,
        )
        session.add(concept)
        session.flush()
        return concept

    concept.topic_id = topic_id
    concept.title = payload.concept.title
    concept.definition = payload.concept.definition
    concept.difficulty = payload.concept.difficulty.value
    concept.prerequisites_json = payload.concept.prerequisites
    concept.status = payload.concept.status.value
    session.flush()
    return concept


def _get_or_create_assessment_mode(session: Session, mode_name: str) -> AssessmentMode:
    for definition in build_reference_assessment_modes():
        existing = session.scalar(select(AssessmentMode).where(AssessmentMode.name == definition.mode.value))
        if existing is None:
            existing = AssessmentMode(
                name=definition.mode.value,
                description=definition.description,
                scoring_style=definition.scoring_style.value,
                timing_style=definition.timing_style.value,
            )
            session.add(existing)
            session.flush()

    assessment_mode = session.scalar(select(AssessmentMode).where(AssessmentMode.name == mode_name))
    if assessment_mode is None:
        raise HTTPException(status_code=400, detail="Unknown assessment mode.")
    return assessment_mode


def _slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "untitled"
