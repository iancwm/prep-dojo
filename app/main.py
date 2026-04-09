from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_session, init_db
from app.schemas.domain import (
    AuthoredQuestionBundleCreate,
    PracticeSessionCreate,
    StudentAttemptCreate,
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
    create_authored_question_bundle,
    get_authored_question_bundle,
    list_authored_question_summaries,
)
from app.services.practice_sessions import (
    create_practice_session_record,
    get_practice_session_record,
    list_practice_session_summaries,
)
from app.services.persistence import ensure_reference_catalog, persist_authored_attempt, persist_reference_attempt


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Prep Dojo",
    version="0.1.0",
    description="Foundational backend contracts for the SMU finance interview prep engine.",
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
def list_practice_sessions(session: Session = Depends(get_session)) -> list[dict]:
    return [item.model_dump(mode="json") for item in list_practice_session_summaries(session)]


@app.get("/api/v1/practice-sessions/{session_id}")
def get_practice_session(session_id: str, session: Session = Depends(get_session)) -> dict:
    return get_practice_session_record(session, session_id).model_dump(mode="json")


@app.post("/api/v1/authored/questions", status_code=status.HTTP_201_CREATED)
def create_authored_question(
    payload: AuthoredQuestionBundleCreate,
    session: Session = Depends(get_session),
) -> dict:
    return create_authored_question_bundle(session, payload).model_dump(mode="json")


@app.get("/api/v1/authored/questions")
def list_authored_questions(session: Session = Depends(get_session)) -> list[dict]:
    return [item.model_dump(mode="json") for item in list_authored_question_summaries(session)]


@app.get("/api/v1/authored/questions/{question_id}")
def get_authored_question(question_id: str, session: Session = Depends(get_session)) -> dict:
    return get_authored_question_bundle(session, question_id).model_dump(mode="json")


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
