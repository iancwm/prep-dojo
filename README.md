# Prep Dojo

Backend foundation for the SMU finance interview prep engine.

The project currently implements a narrow but real backend slice:
- typed domain contracts for topics, concepts, questions, rubrics, attempts, scores, and feedback
- a FastAPI app with reference endpoints
- seeded finance interview questions under a valuation module
- scoring for free-text answers against stored rubric data
- persistence of attempts, scores, feedback, and module progress into a local database
- a Vite + React demo frontend for operator and student workflows

## Current State

This is not yet a full product. It is a validated backend skeleton with a working reference flow.

What exists today:
- two seeded reference questions for the `Enterprise Value vs Equity Value` concept
- generic reference question routes
- first-class practice session create/list/get routes, with list filtering by `status`, `source`, `started_after`, `started_before`, `current_question_id`, and `has_remaining`
- explicit practice-session start/complete routes
- a write path that accepts an attempt, scores it, persists it, and returns feedback
- authored question bundle creation and retrieval routes backed by the database
- authored topic and concept management routes for content operations
- lightweight role-claim guards on authored routes via `X-User-Role`
- authored status-transition workflow for `draft -> reviewed -> published`
- authored question editing with version bumps for question and rubric payloads
- authored question list filtering by status, topic, and concept
- authored topic/concept list filters with archived content hidden by default and opt-in visibility
- rubric contracts that enforce unique criterion names, sorted and unique thresholds, and a 0-percent floor
- authored question submission and scoring for rubric-backed free-text, oral-transcript, and multiple-choice answers
- publish-readiness validation for rubric and expected-answer completeness
- mode-specific publish validation for multiple-choice and oral-recall payloads
- Alembic migrations with a migration-first runtime mode for non-local environments
- explicit attempt submission and scoring flow, with stored scores carrying rubric lineage and attempts ending in `complete`
- centralized runtime configuration in `config/` with env overrides
- `justfile` automation for local bootstrap, startup, testing, and teardown
- local SQLite storage by default
- tests covering schema validation, scoring, API behavior, and persistence
- a frontend demo app under `web/` for the guided create -> practice -> review story

What does not exist yet:
- full login/session-based authentication and identity-provider integration
- production-grade database configuration
- production-ready frontend auth and operator ergonomics

## Quick Start

Requirements:
- Python 3.11+
- `uv`
- Node.js 20+

Install dependencies:

```bash
just bootstrap
```

`just bootstrap` is idempotent. It installs Python and frontend deps, ensures the local runtime config exists, and backfills any newly added local-dev keys without overwriting your existing values.

If you prefer to install manually:

```bash
uv sync --extra dev
just web-install
```

The `justfile` uses `/bin/bash`, so the commands work in environments that do not have `/bin/zsh`.

Run the backend:

```bash
just up
```

The local setup now reads its vital runtime values from:
- [config/local-dev.yaml.example](/home/iancwm/git/prep-dojo/config/local-dev.yaml.example) as the checked-in template
- `config/local-dev.yaml` as your local editable file, created automatically by `just bootstrap`

Repeated local lifecycle commands are safe:
- `just bootstrap` preserves your existing local overrides
- `just up` clears stale PID files before restarting
- `just down` succeeds even when nothing is running
- `just teardown-local` removes only local runtime artifacts and tolerates missing files

Useful local commands:

```bash
just local-config
just status
just logs
```

Run tests:

```bash
just test
```

Run migrations:

```bash
just migrate
```

Run the frontend demo:

```bash
just web-dev
```

If you need a different local port or local DB path, edit `config/local-dev.yaml` once and the backend, frontend proxy, migrate flow, config inspection, and teardown commands will all follow it.

Run the frontend smoke tests:

```bash
just web-test
```

The frontend test baseline uses Vitest plus Testing Library and currently covers:
- operator review, publish, and demo-session creation
- student session start, answer submission, and result rendering
- result-page fallback and return flow

Build the frontend from the repo root:

```bash
just web-build
```

Typecheck the frontend:

```bash
just web-typecheck
```

Preview the production frontend build:

```bash
just web-preview
```

You can still run the frontend directly inside `web/` if you prefer:

```bash
cd web
npm install
npm run dev
```

Frontend dev server:
- `http://127.0.0.1:5173`

The backend now allows local frontend origins for Vite dev and preview.
The frontend dev proxy follows the backend target derived from `config/local-dev.yaml`.

## Runtime Behavior

On startup, the app initializes the database schema only when `DATABASE_INIT_MODE=metadata`.

Use `DATABASE_INIT_MODE=migrations` for migration-first environments and run:
- `just migrate`

Default database:
- `sqlite:///./prep_dojo.db`

Override with:
- `DATABASE_URL`
- `DATABASE_INIT_MODE`
- `APP_CONFIG_PATH`
- env vars from [.env.example](/home/iancwm/git/prep-dojo/.env.example)
- local runtime defaults from `config/local-dev.yaml`

The local database file is ignored in git.

## Automation

Main local commands:
- `just bootstrap`
- `just config`
- `just local-config`
- `just up`
- `just down`
- `just restart`
- `just status`
- `just logs`
- `just migrate`
- `just test`
- `just web-install`
- `just web-dev`
- `just web-build`
- `just web-test`
- `just web-typecheck`
- `just web-preview`
- `just teardown-local`
- `just cloud-readiness`

## Implemented Endpoints

Health:
- `GET /healthz`
- `GET /readyz`

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
- `POST /api/v1/authored/topics`
- `GET /api/v1/authored/topics` with `status` and `include_archived` filters
- `PUT /api/v1/authored/topics/{topic_slug}`
- `POST /api/v1/authored/concepts`
- `GET /api/v1/authored/concepts` with `topic_slug`, `status`, and `include_archived` filters
- `PUT /api/v1/authored/concepts/{concept_slug}`
- `POST /api/v1/authored/questions`
- `GET /api/v1/authored/questions`
- `GET /api/v1/authored/questions/{question_id}`
- `PUT /api/v1/authored/questions/{question_id}`
- `POST /api/v1/authored/questions/{question_id}/status`
- `POST /api/v1/authored/questions/{question_id}/submit`

Practice sessions:
- `POST /api/v1/practice-sessions`
- `GET /api/v1/practice-sessions` with `status`, `source`, `started_after`, `started_before`, `current_question_id`, and `has_remaining` filters; invalid status returns `422`
- `GET /api/v1/practice-sessions/{session_id}`
- `POST /api/v1/practice-sessions/{session_id}/start`
- `POST /api/v1/practice-sessions/{session_id}/complete`

## Project Layout

- `app/main.py`
  FastAPI entrypoint, route definitions, readiness endpoint, and request observability hooks.
- `app/core/enums.py`
  Shared domain enums.
- `app/core/settings.py`
  Runtime settings loader backed by `config/app.toml` and env overrides.
- `app/cli.py`
  Runtime CLI used by the `justfile`.
- `app/schemas/domain.py`
  Pydantic contracts for the backend model.
- `app/db/models.py`
  SQLAlchemy models.
- `app/db/session.py`
  Engine, session setup, and schema-init mode handling.
- `alembic/`
  Migration environment and version history.
- `alembic.ini`
  Alembic configuration entrypoint.
- `app/seeds/reference_data.py`
  Seeded valuation module and reference questions.
- `app/services/scoring.py`
  Scoring logic for stored rubric-backed questions.
- `app/services/persistence.py`
  Catalog seeding and database persistence for attempts/results.
- `app/services/practice_sessions.py`
  Practice session creation and session-history read models.
- `config/`
  Runtime and deployment-oriented configuration files.
- `justfile`
  Local automation for bootstrap, startup, test, and teardown.
- `tests/`
  Contract, API, and persistence tests.
- `docs/`
  Product and sprint documentation.
- `web/`
  Demo frontend for operator authoring, student practice, and result review.

## Known Constraints

- The current scoring logic is still heuristic. It is driven by stored rubric data, but it is not a true semantic evaluator yet.
- Authored content is protected by lightweight role-claim guards, but there is still no full login/session-based auth or admin UI around it.
- The scoring path now supports stored free-text, oral-transcript, and multiple-choice responses, but the oral path is still heuristic text scoring rather than true spoken-answer evaluation.
- Authored questions must be published before they can be submitted.
- Published or archived authored questions cannot be edited; editing a reviewed question sends it back to draft for re-review.
- The attempt lifecycle is explicit for synchronous scoring, but the reserved `created`, `scored`, and `needs_followup` states are not yet used by a manual-review or async-scoring flow.
- Production deployment is still pre-release and lacks a cloud entrypoint/manifest; see [docs/cloud-deployment-readiness.md](/home/iancwm/git/prep-dojo/docs/cloud-deployment-readiness.md).

## Next Likely Steps

- deepen the frontend beyond the guided demo path
- add fuller auth and user identity handling for the frontend
- add richer session lifecycle controls such as timing and async/manual-review handoff
- add a production deployment entrypoint and platform manifest

## Sprint 3 Kickoff

Active sprint focus:
- observability baseline for faster debugging
- runtime and deployment safety without platform overreach
- data-model guardrails on the highest-risk workflow seams
- developer-facing docs that match the real system

Sprint 3 working spec:
- [docs/sprint-3-hardening-observability-and-developer-baseline.md](/home/iancwm/git/prep-dojo/docs/sprint-3-hardening-observability-and-developer-baseline.md)

## Sprint 2 Pilot Smoke-Test

Use this as the local pilot simulation sequence before an internal rehearsal.

Prereqs:
- `APP_CONFIG_PATH=config/app.toml`
- local API base URL: `http://127.0.0.1:8001`
- mentor-like role header for authored routes: `X-User-Role: academic`
- student requests omit `X-User-Role` entirely

1. Bootstrap the local stack:
   - `just bootstrap`
   - `just migrate`
   - `just up`
2. Confirm the app is alive:
   - `curl http://127.0.0.1:8001/healthz`
   - `curl http://127.0.0.1:8001/readyz`
   - `curl http://127.0.0.1:8001/api/v1/reference/assessment-modes`
3. Smoke the authored content surface as a mentor-like user:
   - create a topic with `POST /api/v1/authored/topics`
   - create a concept with `POST /api/v1/authored/concepts`
   - create a question bundle with `POST /api/v1/authored/questions`
   - fetch it back with `GET /api/v1/authored/questions/{question_id}`
   - move it through `POST /api/v1/authored/questions/{question_id}/status` to `reviewed`
   - move it through the same endpoint to `published`
   - verify it appears in `GET /api/v1/authored/questions`
4. Smoke the practice-session flow as a student:
   - create a session with `POST /api/v1/practice-sessions`
   - use a `source` like `pilot-smoke`
   - include a `question_queue` with at least the published authored question id
   - check `GET /api/v1/practice-sessions?status=created&source=pilot-smoke`
   - use `started_after`, `started_before`, `current_question_id`, and `has_remaining` filters to narrow operator triage when needed
   - start it with `POST /api/v1/practice-sessions/{session_id}/start`
   - submit the authored attempt with `POST /api/v1/authored/questions/{question_id}/submit`
   - inspect `GET /api/v1/practice-sessions/{session_id}` for queue counts and `current_question_id`
   - complete it with `POST /api/v1/practice-sessions/{session_id}/complete`
   - confirm `GET /api/v1/practice-sessions?status=completed&source=pilot-smoke`
5. Clean up after the rehearsal:
   - `just down`
   - `just teardown-local` if you want to reset the local SQLite database

## Sprint 3 Hardening Checks

Use this short checklist when you want confidence that the local developer baseline is healthy before deeper feature work.

1. Confirm runtime config and migration mode:
   - `just config`
   - `python -m app.cli check-readiness`
2. Confirm liveness and readiness:
   - `curl http://127.0.0.1:8001/healthz`
   - `curl http://127.0.0.1:8001/readyz`
3. Confirm the backend test baseline:
   - `just test`
4. Confirm the frontend still compiles against the current API shape:
   - `just web-build`
5. Confirm the frontend smoke tests still pass:
   - `just web-test`
5. If you are using a non-development environment value, sanity-check that reload is off and DB init mode resolves to migrations:
   - `APP_ENV=production python -m app.cli show-config`

Sprint 2 working spec:
- [docs/sprint-2-pilot-readiness-and-content-operations.md](/home/iancwm/git/prep-dojo/docs/sprint-2-pilot-readiness-and-content-operations.md)
