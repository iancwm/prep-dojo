from __future__ import annotations

import re
import uuid

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import AssessmentMode, CommonMistake, Concept, ExpectedAnswer, Question, Rubric, Topic
from app.schemas.domain import (
    AssessmentModeDefinition,
    AuthoredQuestionListFilters,
    AuthoredQuestionBundleCreate,
    AuthoredQuestionBundleRecord,
    AuthoredQuestionBundleUpdate,
    AuthoredQuestionSummary,
    CommonMistakeCreate,
    ConceptArchiveResult,
    ConceptRecord,
    ConceptCreate,
    ConceptUpdate,
    ContentStatusTransitionRequest,
    ContentStatusTransitionResult,
    ExpectedAnswerCreate,
    QuestionRecord,
    QuestionUpdate,
    RubricCriterion,
    RubricDefinition,
    TopicListFilters,
    TopicArchiveResult,
    TopicRecord,
    TopicCreate,
    TopicUpdate,
    ConceptListFilters,
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


def list_authored_question_summaries(
    session: Session,
    filters: AuthoredQuestionListFilters | None = None,
) -> list[AuthoredQuestionSummary]:
    stmt = select(Question).where(Question.external_id.is_(None))
    if filters is not None:
        if filters.status is not None:
            stmt = stmt.where(Question.status == filters.status.value)
        if filters.topic_slug is not None:
            stmt = stmt.join(Concept, Question.concept_id == Concept.id).join(Topic, Concept.topic_id == Topic.id)
            stmt = stmt.where(Topic.slug == filters.topic_slug)
        elif filters.concept_slug is not None:
            stmt = stmt.join(Concept, Question.concept_id == Concept.id)
        if filters.concept_slug is not None:
            stmt = stmt.where(Concept.slug == filters.concept_slug)

    authored_questions = session.scalars(stmt.order_by(Question.created_at.desc())).all()
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


def create_topic(session: Session, payload: TopicCreate) -> TopicRecord:
    topic = session.scalar(select(Topic).where(Topic.slug == payload.slug))
    if topic is not None:
        raise HTTPException(status_code=409, detail="Topic slug already exists.")

    topic = Topic(
        slug=payload.slug,
        title=payload.title,
        description=payload.description,
        order_index=payload.order_index,
        status=payload.status.value,
    )
    session.add(topic)
    session.commit()
    session.refresh(topic)
    return _topic_record(topic)


def list_topics(session: Session, filters: TopicListFilters | None = None) -> list[TopicRecord]:
    stmt = select(Topic)
    if filters is not None:
        if filters.status is not None:
            stmt = stmt.where(Topic.status == filters.status.value)
        elif not filters.include_archived:
            stmt = stmt.where(Topic.status != "archived")
    topics = session.scalars(stmt.order_by(Topic.order_index.asc(), Topic.title.asc())).all()
    return [_topic_record(topic) for topic in topics]


def update_topic(session: Session, topic_slug: str, payload: TopicUpdate) -> TopicRecord:
    topic = _get_topic_row(session, topic_slug)
    _validate_collection_status_transition(topic.status, payload.status.value, "topic")
    topic.title = payload.title
    topic.description = payload.description
    topic.order_index = payload.order_index
    topic.status = payload.status.value
    session.commit()
    session.refresh(topic)
    return _topic_record(topic)


def archive_topic(session: Session, topic_slug: str) -> TopicArchiveResult:
    topic = _get_topic_row(session, topic_slug)
    previous_status = topic.status

    archived_concept_count = 0
    archived_question_count = 0
    for concept in topic.concepts:
        concept_was_archived, concept_question_count = _archive_concept_tree(concept)
        archived_concept_count += int(concept_was_archived)
        archived_question_count += concept_question_count

    topic.status = "archived"
    session.commit()
    return TopicArchiveResult(
        topic_slug=topic.slug,
        previous_status=previous_status,
        current_status="archived",
        archived_concept_count=archived_concept_count,
        archived_question_count=archived_question_count,
    )


def create_concept(session: Session, payload: ConceptCreate) -> ConceptRecord:
    topic = _get_topic_row(session, payload.topic_slug)
    concept_slug = payload.slug or _slugify(payload.title)
    concept = session.scalar(select(Concept).where(Concept.slug == concept_slug))
    if concept is not None:
        raise HTTPException(status_code=409, detail="Concept slug already exists.")

    concept = Concept(
        topic_id=topic.id,
        slug=concept_slug,
        title=payload.title,
        definition=payload.definition,
        difficulty=payload.difficulty.value,
        prerequisites_json=payload.prerequisites,
        status=payload.status.value,
    )
    session.add(concept)
    session.commit()
    session.refresh(concept)
    return _concept_record(concept)


def list_concepts(session: Session, filters: ConceptListFilters | None = None) -> list[ConceptRecord]:
    stmt = select(Concept)
    if filters is not None:
        if filters.topic_slug is not None:
            stmt = stmt.join(Topic, Concept.topic_id == Topic.id).where(Topic.slug == filters.topic_slug)
        if filters.status is not None:
            stmt = stmt.where(Concept.status == filters.status.value)
        elif not filters.include_archived:
            stmt = stmt.where(Concept.status != "archived")
    concepts = session.scalars(stmt.order_by(Concept.title.asc())).all()
    return [_concept_record(concept) for concept in concepts]


def update_concept(session: Session, concept_slug: str, payload: ConceptUpdate) -> ConceptRecord:
    concept = _get_concept_row(session, concept_slug)
    topic = _get_topic_row(session, payload.topic_slug)
    _validate_collection_status_transition(concept.status, payload.status.value, "concept")
    concept.topic_id = topic.id
    concept.title = payload.title
    concept.definition = payload.definition
    concept.difficulty = payload.difficulty.value
    concept.prerequisites_json = payload.prerequisites
    concept.status = payload.status.value
    session.commit()
    session.refresh(concept)
    return _concept_record(concept)


def archive_concept(session: Session, concept_slug: str) -> ConceptArchiveResult:
    concept = _get_concept_row(session, concept_slug)
    previous_status = concept.status
    _, archived_question_count = _archive_concept_tree(concept)
    session.commit()
    return ConceptArchiveResult(
        concept_slug=concept.slug,
        previous_status=previous_status,
        current_status="archived",
        archived_question_count=archived_question_count,
    )


def transition_authored_question_status(
    session: Session,
    question_id: str,
    payload: ContentStatusTransitionRequest,
) -> ContentStatusTransitionResult:
    question = _get_authored_question_row(session, question_id)
    if question.rubric is None:
        raise HTTPException(status_code=500, detail="Authored question is missing rubric state.")

    previous_status = question.status
    _validate_status_transition(question.status, payload.status.value)
    if payload.status.value == "reviewed" and not payload.review_notes:
        raise HTTPException(status_code=400, detail="Review notes are required when marking content as reviewed.")
    if payload.status.value == "published":
        _validate_publish_readiness(question)

    question.status = payload.status.value
    question.rubric.status = payload.status.value
    if payload.review_notes is not None:
        question.rubric.review_notes = payload.review_notes
    _promote_parent_statuses(question, payload.status.value)

    session.commit()
    return ContentStatusTransitionResult(
        question_id=str(question.id),
        previous_status=previous_status,
        current_status=payload.status,
        review_notes=payload.review_notes,
    )


def update_authored_question_bundle(
    session: Session,
    question_id: str,
    payload: AuthoredQuestionBundleUpdate,
) -> AuthoredQuestionBundleRecord:
    _validate_question_update_contract(payload.question)

    question = _get_authored_question_row(session, question_id)
    if question.rubric is None or question.expected_answer is None:
        raise HTTPException(status_code=500, detail="Authored question is missing required scoring artifacts.")
    if question.status in {"published", "archived"}:
        raise HTTPException(status_code=400, detail="Published or archived authored questions cannot be edited.")

    concept = _get_concept_row(session, payload.question.concept_slug)
    assessment_mode = _get_or_create_assessment_mode(session, payload.question.assessment_mode.value)

    question.concept_id = concept.id
    question.assessment_mode_id = assessment_mode.id
    question.difficulty = payload.question.difficulty.value
    question.prompt = payload.question.prompt
    question.context = payload.question.context
    question.payload_json = payload.question.payload.model_dump(mode="json")
    question.version += 1

    question.rubric.criteria_json = [criterion.model_dump(mode="json") for criterion in payload.rubric.criteria]
    question.rubric.thresholds_json = [threshold.model_dump(mode="json") for threshold in payload.rubric.thresholds]
    question.rubric.scoring_style = payload.rubric.scoring_style.value
    question.rubric.review_notes = payload.rubric.review_notes
    question.rubric.version += 1

    question.expected_answer.answer_text = payload.expected_answer.answer_text
    question.expected_answer.answer_outline_json = payload.expected_answer.answer_outline
    question.expected_answer.key_points_json = payload.expected_answer.key_points
    question.expected_answer.acceptable_variants_json = payload.expected_answer.acceptable_variants

    session.execute(delete(CommonMistake).where(CommonMistake.question_id == question.id))
    session.flush()
    for mistake in payload.common_mistakes:
        session.add(
            CommonMistake(
                question_id=question.id,
                mistake_text=mistake.mistake_text,
                why_it_is_wrong=mistake.why_it_is_wrong,
                remediation_hint=mistake.remediation_hint,
            )
        )

    if question.status == "reviewed":
        question.status = "draft"
        question.rubric.status = "draft"
        question.rubric.review_notes = None

    session.commit()
    session.refresh(question)
    return get_authored_question_bundle(session, str(question.id))


def get_authored_question_bundle(session: Session, question_id: str) -> AuthoredQuestionBundleRecord:
    question = _get_authored_question_row(session, question_id)
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
            review_notes=question.rubric.review_notes,
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


def _validate_question_update_contract(payload: QuestionUpdate) -> None:
    if payload.payload.prompt != payload.prompt:
        raise HTTPException(status_code=400, detail="Question payload prompt must match the question prompt.")


def _get_authored_question_row(session: Session, question_id: str) -> Question:
    try:
        parsed_id = uuid.UUID(question_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Unknown authored question.") from exc

    question = session.scalar(select(Question).where(Question.id == parsed_id, Question.external_id.is_(None)))
    if question is None:
        raise HTTPException(status_code=404, detail="Unknown authored question.")
    return question


def _archive_concept_tree(concept: Concept) -> tuple[bool, int]:
    concept_was_archived = concept.status != "archived"
    concept.status = "archived"

    archived_question_count = 0
    for question in concept.questions:
        if question.status != "archived":
            archived_question_count += 1
        question.status = "archived"
        if question.rubric is not None:
            question.rubric.status = "archived"

    return concept_was_archived, archived_question_count


def _validate_status_transition(current_status: str, target_status: str) -> None:
    allowed_transitions = {
        "draft": {"reviewed", "archived"},
        "reviewed": {"draft", "published", "archived"},
        "published": {"archived"},
        "archived": set(),
    }
    if target_status == current_status:
        return
    if target_status not in allowed_transitions.get(current_status, set()):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition authored question from `{current_status}` to `{target_status}`.",
        )


def _validate_collection_status_transition(current_status: str, target_status: str, entity_name: str) -> None:
    allowed_transitions = {
        "draft": {"reviewed", "archived"},
        "reviewed": {"draft", "archived"},
        "published": {"archived"},
        "archived": set(),
    }
    if target_status == current_status:
        return
    if target_status not in allowed_transitions.get(current_status, set()):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition {entity_name} from `{current_status}` to `{target_status}`.",
        )


def _validate_publish_readiness(question: Question) -> None:
    if question.rubric is None or question.expected_answer is None:
        raise HTTPException(status_code=400, detail="Question must have rubric and expected answer before publishing.")
    if not question.rubric.criteria_json:
        raise HTTPException(status_code=400, detail="Rubric must contain at least one criterion before publishing.")
    if not question.rubric.thresholds_json:
        raise HTTPException(status_code=400, detail="Rubric must contain at least one threshold before publishing.")
    if not question.expected_answer.answer_text.strip():
        raise HTTPException(status_code=400, detail="Expected answer text is required before publishing.")
    if not question.expected_answer.key_points_json:
        raise HTTPException(status_code=400, detail="Expected answer key points are required before publishing.")
    _validate_mode_specific_publish_readiness(question)


def _validate_mode_specific_publish_readiness(question: Question) -> None:
    payload = question.payload_json
    question_type = payload.get("question_type")

    if question_type == "mcq_single":
        options = payload.get("options") or []
        correct_option_id = payload.get("correct_option_id")
        explanation = (payload.get("explanation") or "").strip()
        if len(options) < 2:
            raise HTTPException(status_code=400, detail="Multiple-choice questions need at least two options before publishing.")
        option_ids = [item.get("id") for item in options if isinstance(item, dict)]
        if len(option_ids) != len(set(option_ids)):
            raise HTTPException(status_code=400, detail="Multiple-choice option ids must be unique before publishing.")
        if not correct_option_id or correct_option_id not in option_ids:
            raise HTTPException(status_code=400, detail="Multiple-choice questions need a valid correct option before publishing.")
        if not explanation:
            raise HTTPException(status_code=400, detail="Multiple-choice questions need an explanation before publishing.")
        return

    if question_type == "oral_recall":
        target_duration_seconds = payload.get("target_duration_seconds")
        if target_duration_seconds is None:
            raise HTTPException(status_code=400, detail="Oral recall questions need a target duration before publishing.")


def _promote_parent_statuses(question: Question, target_status: str) -> None:
    if target_status not in {"reviewed", "published"}:
        return

    promotion_rank = {"draft": 0, "reviewed": 1, "published": 2}
    concept = question.concept
    topic = concept.topic

    if promotion_rank.get(concept.status, 0) < promotion_rank[target_status]:
        concept.status = target_status
    if promotion_rank.get(topic.status, 0) < promotion_rank[target_status]:
        topic.status = target_status


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


def _get_topic_row(session: Session, topic_slug: str) -> Topic:
    topic = session.scalar(select(Topic).where(Topic.slug == topic_slug))
    if topic is None:
        raise HTTPException(status_code=404, detail="Unknown topic.")
    return topic


def _get_concept_row(session: Session, concept_slug: str) -> Concept:
    concept = session.scalar(select(Concept).where(Concept.slug == concept_slug))
    if concept is None:
        raise HTTPException(status_code=404, detail="Unknown concept.")
    return concept


def _topic_record(topic: Topic) -> TopicRecord:
    return TopicRecord(
        id=str(topic.id),
        slug=topic.slug,
        title=topic.title,
        description=topic.description,
        order_index=topic.order_index,
        status=topic.status,
    )


def _concept_record(concept: Concept) -> ConceptRecord:
    return ConceptRecord(
        id=str(concept.id),
        topic_slug=concept.topic.slug,
        slug=concept.slug,
        title=concept.title,
        definition=concept.definition,
        difficulty=concept.difficulty,
        prerequisites=concept.prerequisites_json,
        status=concept.status,
    )
