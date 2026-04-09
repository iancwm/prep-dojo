# Prep Dojo

Backend foundation for the SMU finance interview prep engine.

The project currently implements a narrow but real backend slice:
- typed domain contracts for topics, concepts, questions, rubrics, attempts, scores, and feedback
- a FastAPI app with reference endpoints
- seeded finance interview questions under a valuation module
- scoring for free-text answers against stored rubric data
- persistence of attempts, scores, feedback, and module progress into a local database

## Current State

This is not yet a full product. It is a validated backend skeleton with a working reference flow.

What exists today:
- two seeded reference questions for the `Enterprise Value vs Equity Value` concept
- generic reference question routes
- a write path that accepts an attempt, scores it, persists it, and returns feedback
- local SQLite storage by default
- tests covering schema validation, scoring, API behavior, and persistence

What does not exist yet:
- authored question creation flows
- authentication and role-based access
- Alembic migrations
- production-grade database configuration
- student-facing UI
- mentor review workflows beyond seeded content

## Quick Start

Requirements:
- Python 3.11+
- `uv`

Install dependencies:

```bash
uv sync --extra dev
```

Run the app:

```bash
./.venv/bin/uvicorn app.main:app --reload
```

Run tests:

```bash
./.venv/bin/pytest tests
```

## Runtime Behavior

On startup, the app initializes the database schema using SQLAlchemy metadata.

Default database:
- `sqlite:///./prep_dojo.db`

Override with:
- `DATABASE_URL`

The local database file is ignored in git.

## Implemented Endpoints

Health:
- `GET /healthz`

Reference metadata:
- `GET /api/v1/reference/assessment-modes`
- `GET /api/v1/reference/modules/valuation-enterprise-value`
- `GET /api/v1/reference/modules/valuation-enterprise-value/progress`
- `GET /api/v1/reference/questions`
- `GET /api/v1/reference/questions/{question_external_id}`

Reference scoring:
- `POST /api/v1/reference/modules/valuation-enterprise-value/submit`
- `POST /api/v1/reference/questions/{question_external_id}/submit`

## Project Layout

- `app/main.py`
  FastAPI entrypoint and route definitions.
- `app/core/enums.py`
  Shared domain enums.
- `app/schemas/domain.py`
  Pydantic contracts for the backend model.
- `app/db/models.py`
  SQLAlchemy models.
- `app/db/session.py`
  Engine and session setup.
- `app/seeds/reference_data.py`
  Seeded valuation module and reference questions.
- `app/services/scoring.py`
  Scoring logic for stored rubric-backed questions.
- `app/services/persistence.py`
  Catalog seeding and database persistence for attempts/results.
- `tests/`
  Contract, API, and persistence tests.
- `docs/`
  Product and sprint documentation.

## Known Constraints

- The current scoring logic is still heuristic. It is driven by stored rubric data, but it is not a true semantic evaluator yet.
- The “reference” question set is seeded code, not authored content from a CMS or admin flow.
- The generic question routes are only generic across stored reference questions, not across arbitrary new authored questions.

## Next Likely Steps

- add authored question creation and retrieval flows
- introduce Alembic and real migration management
- replace seeded-only catalog assumptions with database-native question authoring
- add practice-session APIs that work beyond the reference module

