from fastapi import FastAPI

from app.schemas.domain import build_reference_assessment_modes

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

