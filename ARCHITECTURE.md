# Architecture

## Overview

Prep Dojo is currently a small FastAPI service with a typed domain layer, a SQLAlchemy persistence layer, a seeded finance interview reference catalog, an authored question lifecycle, and first-class practice session APIs.

The core backend path implemented today is:

1. client submits a `StudentAttemptCreate`
2. the app resolves the stored question, rubric, expected answer, and common mistakes
3. the scoring service computes criterion scores, overall score, mastery band, and feedback
4. the persistence service stores the attempt, score, feedback, and progress update
5. the API returns the persisted attempt id plus structured results

Current limitation in that flow:
- the attempt row is first persisted as `submitted`
- scoring and feedback are stored immediately
- the attempt row is finalized as `complete` in the same persistence path

## Application Layers

### API

File:
- [app/main.py](/Users/iancwm/git/prep-dojo/app/main.py)

Responsibilities:
- initialize the database at app startup
- expose reference read endpoints
- expose practice-session create/list/get endpoints
- expose authored create/list/get endpoints
- expose authored lifecycle transition endpoints
- expose authored submit endpoints
- expose reference submit endpoints
- translate request payloads into typed domain models

### Domain Contracts

File:
- [app/schemas/domain.py](/Users/iancwm/git/prep-dojo/app/schemas/domain.py)

Responsibilities:
- define Pydantic models for authored content and student interactions
- enforce discriminated unions for question payloads and student responses
- define rubric and scoring result structures

Key contracts:
- `AuthoredQuestionBundleCreate`
- `AuthoredQuestionBundleRecord`
- `ContentStatusTransitionRequest`
- `ContentStatusTransitionResult`
- `PracticeSessionCreate`
- `PracticeSessionRecord`
- `QuestionCreate`
- `RubricDefinition`
- `StudentAttemptCreate`
- `ScoreResult`
- `FeedbackResult`

### Persistence Model

Files:
- [app/db/models.py](/Users/iancwm/git/prep-dojo/app/db/models.py)
- [app/db/session.py](/Users/iancwm/git/prep-dojo/app/db/session.py)

Responsibilities:
- define relational tables for users, topics, concepts, questions, rubrics, answers, attempts, scores, feedback, and progress
- keep flexible payloads in JSON while preserving relational links for ownership and lifecycle
- provide the default local SQLite engine and session factory

Current database behavior:
- SQLite by default for local execution
- JSON columns use a SQLite-safe JSON type and switch to JSONB on PostgreSQL
- schema is created via `Base.metadata.create_all()` at startup

### Seed Catalog

File:
- [app/seeds/reference_data.py](/Users/iancwm/git/prep-dojo/app/seeds/reference_data.py)

Responsibilities:
- provide the seeded valuation module
- define two stored reference questions
- define rubric, expected answer, common mistakes, and sample attempts

Current seeded concept:
- `Enterprise Value vs Equity Value`

Current seeded question ids:
- `sample-question-enterprise-value`
- `sample-question-when-equity-value-matters`

### Authoring

File:
- [app/services/authoring.py](/Users/iancwm/git/prep-dojo/app/services/authoring.py)

Responsibilities:
- validate authored question-bundle creation payloads
- create or update the parent topic and concept
- ensure assessment modes exist in the database
- persist the authored question, rubric, expected answer, and common mistakes
- list and fetch authored question bundles by database id
- support authored question retrieval for DB-native submit flows
- enforce lifecycle transitions across draft, reviewed, published, and archived

### Scoring

File:
- [app/services/scoring.py](/Users/iancwm/git/prep-dojo/app/services/scoring.py)

Responsibilities:
- score a free-text student response against stored rubric data
- compute per-criterion scores
- compute weighted overall score
- map score to mastery band
- generate structured feedback

Current scoring model:
- heuristic, not LLM-based
- uses rubric criterion names, strong fragments, expected key points, expected outline, and common mistakes
- supports stored short-answer, oral-transcript, and multiple-choice questions

### Practice Sessions

File:
- [app/services/practice_sessions.py](/Users/iancwm/git/prep-dojo/app/services/practice_sessions.py)

Responsibilities:
- create named practice sessions before attempt submission
- list recent practice sessions
- return a session read model with attempt history and scores
- preserve `client_session_id` as the external session identifier

### Persistence Workflow

File:
- [app/services/persistence.py](/Users/iancwm/git/prep-dojo/app/services/persistence.py)

Responsibilities:
- seed the reference catalog into the database on demand
- create or reuse a reference student and practice session
- persist attempts, scores, feedback, and progress
- resolve stored questions by `external_id`
- persist rubric lineage on the score row via `rubric_id` and `rubric_version`

## Request Flow

### Authored Question Create

Route:
- `POST /api/v1/authored/questions`

Flow:
- FastAPI validates the payload as `AuthoredQuestionBundleCreate`
- authoring service validates bundle consistency across topic, concept, and question
- topic, concept, and assessment mode are created or reused
- question, rubric, expected answer, and common mistakes are persisted together
- response returns the stored authored bundle with database ids

### Authored Question Submit

Route:
- `POST /api/v1/authored/questions/{question_id}/submit`

Flow:
- FastAPI validates the request as `StudentAttemptCreate`
- persistence layer resolves the authored question by UUID
- submission is allowed only when the authored question and rubric are both published
- scoring runs against the stored rubric and expected-answer records
- attempt, score, feedback, and module progress are written to the DB
- response returns `attempt_id`, `question_id`, `session_id`, `score`, and `feedback`

### Authored Lifecycle Transition

Route:
- `POST /api/v1/authored/questions/{question_id}/status`

Flow:
- FastAPI validates the payload as `ContentStatusTransitionRequest`
- authoring service validates the requested transition against the current lifecycle state
- when moving to `reviewed`, review notes are required
- question and rubric status are updated together
- concept and topic statuses are promoted upward on review/publish so published content is distinguishable from draft parents

### Attempt Lifecycle

Current persisted states:
- `submitted` at row creation during a submit request
- `complete` after score and feedback are written

Desired explicit states:
- `created`
- `submitted`
- `scored`
- `needs_followup`
- `complete`

Current implementation:
- synchronous scoring paths move attempts from `submitted` to `complete` inside one request
- the reserved `created`, `scored`, and `needs_followup` states remain available for future async or mentor-reviewed flows

### Practice Session Read

Routes:
- `POST /api/v1/practice-sessions`
- `GET /api/v1/practice-sessions`
- `GET /api/v1/practice-sessions/{session_id}`

Flow:
- create route provisions or reuses a named session
- list route returns session summaries with source and attempt counts
- detail route returns attempt history, question prompts, scores, and mastery bands for that session

### Generic Reference Submit

Route:
- `POST /api/v1/reference/questions/{question_external_id}/submit`

Flow:
- FastAPI validates the request as `StudentAttemptCreate`
- persistence layer ensures the seeded reference catalog exists in the DB
- the question is resolved by `external_id`
- scoring runs against the stored rubric and expected-answer records
- attempt, score, feedback, and module progress are written to the DB
- response returns `attempt_id`, `question_id`, `session_id`, `score`, and `feedback`

## Current Data Model Notes

Stable relational entities:
- `topics`
- `concepts`
- `assessment_modes`
- `questions`
- `rubrics`
- `expected_answers`
- `common_mistakes`
- `practice_sessions`
- `student_attempts`
- `scores`
- `feedback`
- `module_progress`

Flexible JSON-backed fields:
- `payload_json`
- `criteria_json`
- `thresholds_json`
- `response_json`
- `rubric_breakdown_json`
- `feedback_json`
- `concept_mastery_json`

## Testing

Files:
- [tests/test_domain_contracts.py](/Users/iancwm/git/prep-dojo/tests/test_domain_contracts.py)
- [tests/test_persistence.py](/Users/iancwm/git/prep-dojo/tests/test_persistence.py)

Coverage today:
- schema contract validation
- seeded reference content validity
- authored bundle creation and retrieval
- authored lifecycle transition and publish enforcement
- authored bundle submission and persistence
- authored multiple-choice scoring
- practice-session creation and history retrieval
- scoring behavior for both stored reference questions
- endpoint behavior
- persistence into a temporary SQLite database

Current passing command:

```bash
./.venv/bin/pytest tests
```

## Known Gaps

- no migration layer yet
- no async DB path
- no auth or user identity beyond a seeded reference student
- no role-aware ownership enforcement around lifecycle actions
- oral scoring is still transcript-as-text, not true speech or delivery evaluation
- no dedicated history table for intermediate attempt lifecycle events
- no UI integration

## Recommended Next Step

The next major shift should be adding role-aware permissions and UI workflows around the lifecycle actions that now exist, plus richer session orchestration such as timing, completion, and queued question sets.
