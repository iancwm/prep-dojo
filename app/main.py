from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.auth import require_mentor_like_role
from app.core.settings import get_settings
from app.db.session import get_session, init_db
from app.schemas.domain import (
    AuthoredQuestionListFilters,
    AuthoredQuestionBundleCreate,
    AuthoredQuestionBundleUpdate,
    ConceptListFilters,
    ConceptCreate,
    ConceptUpdate,
    ContentStatusTransitionRequest,
    PracticeSessionListFilters,
    PracticeSessionCreate,
    PracticeSessionStatus,
    PracticeSessionTransitionRequest,
    StudentAttemptCreate,
    TopicListFilters,
    TopicCreate,
    TopicUpdate,
    build_reference_assessment_modes,
)
from app.seeds.reference_data import (
    PRIMARY_REFERENCE_QUESTION_ID,
    SECONDARY_REFERENCE_QUESTION_ID,
    build_reference_question_catalog,
    get_reference_follow_up_question_bundle,
    get_reference_module,
    get_reference_progress_snapshot,
)
from app.services.authoring import (
    archive_concept,
    archive_topic,
    create_concept,
    create_authored_question_bundle,
    create_topic,
    get_authored_question_bundle,
    list_concepts,
    list_authored_question_summaries,
    list_topics,
    transition_authored_question_status,
    update_authored_question_bundle,
    update_concept,
    update_topic,
)
from app.services.practice_sessions import (
    complete_practice_session,
    create_practice_session_record,
    get_practice_session_record,
    list_practice_session_summaries,
    start_practice_session,
)
from app.services.persistence import ensure_reference_catalog, persist_authored_attempt, persist_reference_attempt

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    description=settings.app.description,
    lifespan=lifespan,
)


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/reference/assessment-modes")
def list_assessment_modes() -> list[dict[str, str]]:
    return [mode.model_dump(mode="json") for mode in build_reference_assessment_modes()]


@app.get("/api/v1/reference/modules/valuation-enterprise-value")
def get_valuation_reference_module() -> dict:
    return get_reference_module().model_dump(mode="json")


@app.get("/api/v1/reference/modules/valuation-enterprise-value/progress")
def get_valuation_reference_progress() -> dict[str, str]:
    return get_reference_progress_snapshot()


@app.get("/api/v1/reference/questions")
def list_reference_questions() -> list[dict]:
    return [item.model_dump(mode="json") for item in build_reference_question_catalog()]


@app.get("/api/v1/reference/questions/{question_external_id}")
def get_reference_question(question_external_id: str, session: Session = Depends(get_session)) -> dict:
    ensure_reference_catalog(session)
    if question_external_id == PRIMARY_REFERENCE_QUESTION_ID:
        return get_reference_module().question_bundle.model_dump(mode="json")
    if question_external_id == SECONDARY_REFERENCE_QUESTION_ID:
        return get_reference_follow_up_question_bundle().model_dump(mode="json")
    raise HTTPException(status_code=404, detail="Unknown reference question.")


@app.post("/api/v1/practice-sessions", status_code=status.HTTP_201_CREATED)
def create_practice_session(payload: PracticeSessionCreate, session: Session = Depends(get_session)) -> dict:
    return create_practice_session_record(session, payload).model_dump(mode="json")


@app.get("/api/v1/practice-sessions")
def list_practice_sessions(
    status: PracticeSessionStatus | None = None,
    source: str | None = None,
    started_after: str | None = None,
    started_before: str | None = None,
    current_question_id: str | None = None,
    has_remaining: bool | None = None,
    session: Session = Depends(get_session),
) -> list[dict]:
    filters = PracticeSessionListFilters.model_validate(
        {
            "status": status,
            "source": source,
            "started_after": started_after,
            "started_before": started_before,
            "current_question_id": current_question_id,
            "has_remaining": has_remaining,
        }
    )
    return [item.model_dump(mode="json") for item in list_practice_session_summaries(session, filters=filters)]


@app.get("/api/v1/practice-sessions/{session_id}")
def get_practice_session(session_id: str, session: Session = Depends(get_session)) -> dict:
    return get_practice_session_record(session, session_id).model_dump(mode="json")


@app.post("/api/v1/practice-sessions/{session_id}/start")
def start_practice_session_route(
    session_id: str,
    payload: PracticeSessionTransitionRequest,
    session: Session = Depends(get_session),
) -> dict:
    if payload.status != "in_progress":
        raise HTTPException(status_code=400, detail="Start endpoint only accepts `in_progress` status.")
    return start_practice_session(session, session_id).model_dump(mode="json")


@app.post("/api/v1/practice-sessions/{session_id}/complete")
def complete_practice_session_route(
    session_id: str,
    payload: PracticeSessionTransitionRequest,
    session: Session = Depends(get_session),
) -> dict:
    if payload.status != "completed":
        raise HTTPException(status_code=400, detail="Complete endpoint only accepts `completed` status.")
    return complete_practice_session(session, session_id).model_dump(mode="json")


@app.post("/api/v1/authored/questions", status_code=status.HTTP_201_CREATED)
def create_authored_question(
    payload: AuthoredQuestionBundleCreate,
    _: None = Depends(require_mentor_like_role),
    session: Session = Depends(get_session),
) -> dict:
    return create_authored_question_bundle(session, payload).model_dump(mode="json")


@app.post("/api/v1/authored/topics", status_code=status.HTTP_201_CREATED)
def create_authored_topic(
    payload: TopicCreate,
    _: None = Depends(require_mentor_like_role),
    session: Session = Depends(get_session),
) -> dict:
    return create_topic(session, payload).model_dump(mode="json")


@app.get("/api/v1/authored/topics")
def list_authored_topics(
    status: str | None = None,
    include_archived: bool = False,
    _: None = Depends(require_mentor_like_role),
    session: Session = Depends(get_session),
) -> list[dict]:
    filters = TopicListFilters.model_validate({"status": status, "include_archived": include_archived})
    return [item.model_dump(mode="json") for item in list_topics(session, filters=filters)]


@app.put("/api/v1/authored/topics/{topic_slug}")
def update_authored_topic(
    topic_slug: str,
    payload: TopicUpdate,
    _: None = Depends(require_mentor_like_role),
    session: Session = Depends(get_session),
) -> dict:
    return update_topic(session, topic_slug, payload).model_dump(mode="json")


@app.post("/api/v1/authored/topics/{topic_slug}/archive")
def archive_authored_topic(
    topic_slug: str,
    _: None = Depends(require_mentor_like_role),
    session: Session = Depends(get_session),
) -> dict:
    return archive_topic(session, topic_slug).model_dump(mode="json")


@app.post("/api/v1/authored/concepts", status_code=status.HTTP_201_CREATED)
def create_authored_concept(
    payload: ConceptCreate,
    _: None = Depends(require_mentor_like_role),
    session: Session = Depends(get_session),
) -> dict:
    return create_concept(session, payload).model_dump(mode="json")


@app.get("/api/v1/authored/concepts")
def list_authored_concepts(
    topic_slug: str | None = None,
    status: str | None = None,
    include_archived: bool = False,
    _: None = Depends(require_mentor_like_role),
    session: Session = Depends(get_session),
) -> list[dict]:
    filters = ConceptListFilters.model_validate(
        {
            "topic_slug": topic_slug,
            "status": status,
            "include_archived": include_archived,
        }
    )
    return [item.model_dump(mode="json") for item in list_concepts(session, filters=filters)]


@app.put("/api/v1/authored/concepts/{concept_slug}")
def update_authored_concept(
    concept_slug: str,
    payload: ConceptUpdate,
    _: None = Depends(require_mentor_like_role),
    session: Session = Depends(get_session),
) -> dict:
    return update_concept(session, concept_slug, payload).model_dump(mode="json")


@app.post("/api/v1/authored/concepts/{concept_slug}/archive")
def archive_authored_concept(
    concept_slug: str,
    _: None = Depends(require_mentor_like_role),
    session: Session = Depends(get_session),
) -> dict:
    return archive_concept(session, concept_slug).model_dump(mode="json")


@app.get("/api/v1/authored/questions")
def list_authored_questions(
    status_filter: str | None = None,
    topic_slug: str | None = None,
    concept_slug: str | None = None,
    _: None = Depends(require_mentor_like_role),
    session: Session = Depends(get_session),
) -> list[dict]:
    try:
        filters = AuthoredQuestionListFilters.model_validate(
            {
                "status": status_filter,
                "topic_slug": topic_slug,
                "concept_slug": concept_slug,
            }
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    return [item.model_dump(mode="json") for item in list_authored_question_summaries(session, filters=filters)]


@app.get("/api/v1/authored/questions/{question_id}")
def get_authored_question(
    question_id: str,
    _: None = Depends(require_mentor_like_role),
    session: Session = Depends(get_session),
) -> dict:
    return get_authored_question_bundle(session, question_id).model_dump(mode="json")


@app.put("/api/v1/authored/questions/{question_id}")
def update_authored_question(
    question_id: str,
    payload: AuthoredQuestionBundleUpdate,
    _: None = Depends(require_mentor_like_role),
    session: Session = Depends(get_session),
) -> dict:
    return update_authored_question_bundle(session, question_id, payload).model_dump(mode="json")


@app.post("/api/v1/authored/questions/{question_id}/status")
def update_authored_question_status(
    question_id: str,
    payload: ContentStatusTransitionRequest,
    _: None = Depends(require_mentor_like_role),
    session: Session = Depends(get_session),
) -> dict:
    return transition_authored_question_status(session, question_id, payload).model_dump(mode="json")


@app.post("/api/v1/authored/questions/{question_id}/submit")
def submit_authored_question_attempt(
    question_id: str,
    attempt: StudentAttemptCreate,
    session: Session = Depends(get_session),
) -> dict:
    if attempt.question_id != question_id:
        raise HTTPException(status_code=400, detail="Path question id does not match payload question id.")

    result = persist_authored_attempt(session, question_id, attempt)
    return {
        "attempt_id": result.attempt_id,
        "question_id": result.question_id,
        "session_id": result.session_id,
        "score": result.score.model_dump(mode="json"),
        "feedback": result.feedback.model_dump(mode="json"),
    }


@app.post("/api/v1/reference/modules/valuation-enterprise-value/submit")
def submit_valuation_reference_attempt(attempt: StudentAttemptCreate, session: Session = Depends(get_session)) -> dict:
    result = persist_reference_attempt(session, attempt)
    return {
        "attempt_id": result.attempt_id,
        "question_id": result.question_id,
        "session_id": result.session_id,
        "score": result.score.model_dump(mode="json"),
        "feedback": result.feedback.model_dump(mode="json"),
    }


@app.post("/api/v1/reference/questions/{question_external_id}/submit")
def submit_reference_question_attempt(
    question_external_id: str,
    attempt: StudentAttemptCreate,
    session: Session = Depends(get_session),
) -> dict:
    if attempt.question_id != question_external_id:
        raise HTTPException(status_code=400, detail="Path question id does not match payload question id.")

    result = persist_reference_attempt(session, attempt)
    return {
        "attempt_id": result.attempt_id,
        "question_id": result.question_id,
        "session_id": result.session_id,
        "score": result.score.model_dump(mode="json"),
        "feedback": result.feedback.model_dump(mode="json"),
    }
