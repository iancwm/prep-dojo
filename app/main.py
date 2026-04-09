from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.db.session import get_session, init_db
from app.schemas.domain import StudentAttemptCreate, build_reference_assessment_modes
from app.seeds.reference_data import get_reference_module, get_reference_progress_snapshot
from app.services.persistence import persist_reference_attempt


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
