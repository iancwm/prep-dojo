# Architecture

## Overview

Prep Dojo is currently a small FastAPI service with a typed domain layer, a SQLAlchemy persistence layer, and a seeded finance interview reference catalog.

The core backend path implemented today is:

1. client submits a `StudentAttemptCreate`
2. the app resolves the stored question, rubric, expected answer, and common mistakes
3. the scoring service computes criterion scores, overall score, mastery band, and feedback
4. the persistence service stores the attempt, score, feedback, and progress update
5. the API returns the persisted attempt id plus structured results

## Application Layers

### API

File:
- [app/main.py](/Users/iancwm/git/prep-dojo/app/main.py)

Responsibilities:
- initialize the database at app startup
- expose reference read endpoints
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
- supports stored short-answer reference questions

### Persistence Workflow

File:
- [app/services/persistence.py](/Users/iancwm/git/prep-dojo/app/services/persistence.py)

Responsibilities:
- seed the reference catalog into the database on demand
- create or reuse a reference student and practice session
- persist attempts, scores, feedback, and progress
- resolve stored questions by `external_id`

## Request Flow

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
- no authored content management
- no non-reference question retrieval flow
- no UI integration

## Recommended Next Step

The architecture is ready for authored question CRUD and practice-session orchestration. The next major shift should be moving from seeded reference content to database-native authored content with the same scoring and persistence contracts.

