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
- first-class practice session create/list/get routes
- a write path that accepts an attempt, scores it, persists it, and returns feedback
- authored question bundle creation and retrieval routes backed by the database
- authored status-transition workflow for `draft -> reviewed -> published`
- authored question submission and scoring for rubric-backed free-text, oral-transcript, and multiple-choice answers
- explicit attempt submission and scoring flow, with stored scores carrying rubric lineage and attempts ending in `complete`
- local SQLite storage by default
- tests covering schema validation, scoring, API behavior, and persistence

What does not exist yet:
- authentication and role-based access
- Alembic migrations
- production-grade database configuration
- student-facing UI
- mentor review workflows beyond minimal content creation

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

Authored content:
- `POST /api/v1/authored/questions`
- `GET /api/v1/authored/questions`
- `GET /api/v1/authored/questions/{question_id}`
- `POST /api/v1/authored/questions/{question_id}/status`
- `POST /api/v1/authored/questions/{question_id}/submit`

Practice sessions:
- `POST /api/v1/practice-sessions`
- `GET /api/v1/practice-sessions`
- `GET /api/v1/practice-sessions/{session_id}`

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
- `app/services/practice_sessions.py`
  Practice session creation and session-history read models.
- `tests/`
  Contract, API, and persistence tests.
- `docs/`
  Product and sprint documentation.

## Known Constraints

- The current scoring logic is still heuristic. It is driven by stored rubric data, but it is not a true semantic evaluator yet.
- Authored content can now be stored and moved through a review/publish workflow, but there is still no auth or admin UI around it.
- The scoring path now supports stored free-text, oral-transcript, and multiple-choice responses, but the oral path is still heuristic text scoring rather than true spoken-answer evaluation.
- Authored questions must be published before they can be submitted.
- The attempt lifecycle is explicit for synchronous scoring, but the reserved `created`, `scored`, and `needs_followup` states are not yet used by a manual-review or async-scoring flow.

## Next Likely Steps

- introduce Alembic and real migration management
- add authored topic and concept management beyond question-bundle creation
- add role-aware permissions around review and publishing actions
- add richer session lifecycle controls such as completion, timing, and ordered question queues
