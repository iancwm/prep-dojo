from fastapi import FastAPI

from app.schemas.domain import build_reference_assessment_modes
from app.seeds.reference_data import get_reference_module, get_reference_progress_snapshot

app = FastAPI(
    title="Prep Dojo",
    version="0.1.0",
    description="Foundational backend contracts for the SMU finance interview prep engine.",
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
