# Sprint 2 Spec: Pilot Readiness and Content Operations

Source inputs:
- [Sprint 1 Spec](/home/iancwm/git/prep-dojo/docs/sprint-1-conceptual-model-and-assessment-framework.md)
- [Architecture](/home/iancwm/git/prep-dojo/ARCHITECTURE.md)
- [SMU Finance Interview Prep Engine](/home/iancwm/git/prep-dojo/docs/smu-finance-interview-prep-engine.md)

## Sprint Goal

Convert the Sprint 1 backend foundation into a pilot-ready platform for internal SMU testing.

Sprint 2 focuses on operational correctness, content throughput, and role safety, not UI polish.

## Target Outcome

By the end of Sprint 2:
- database schema changes are managed through Alembic migrations
- the API enforces role-aware auth for authored and review actions
- authored content can be managed beyond single question bundles
- session lifecycle supports realistic practice sequencing and completion
- deployment/readiness docs are actionable for a first internal pilot

## In Scope

- Alembic setup and baseline migration chain
- lightweight auth + role guardrails (`student`, `academic`, `career`, `admin`)
- authored topic/concept CRUD needed for content operations
- stricter authored review/publish controls
- richer practice session lifecycle (`created`, `in_progress`, `completed`)
- pilot readiness documentation and runbook updates

## Out of Scope

- student-facing frontend
- advanced analytics dashboards
- LLM semantic scoring overhaul
- full mentor marketplace or external distribution workflows

## Workstreams

Current Sprint 2 progress:
- migrations foundation landed
- role-aware authored route guards landed
- practice-session lifecycle and ordered queue support landed
- explicit session start/complete endpoints landed
- authored topic/concept CRUD landed
- authored question list filters landed
- authored topic/concept visibility filters landed
- authored question edit/versioning landed
- publish-readiness validation landed
- mode-specific publish validation landed
- rubric contracts now enforce unique criterion names, sorted and unique thresholds, and a 0-percent floor
- practice-session list filtering by `status`, `source`, `started_after`, `started_before`, `current_question_id`, and `has_remaining` landed, with invalid status returning `422`
- README aligned to the implemented Sprint 2 surface
- pilot smoke-test checklist and local simulation sequence documented

## 1) Data and Migration Reliability

Deliverables:
- add Alembic configuration and migration env
- create initial migration from current SQLAlchemy schema
- replace startup `create_all()` dependency with migration-first workflow for non-local envs

Acceptance:
- `just test` passes with migrated schema
- new developer can bootstrap DB with migrations only

## 2) Auth and Role Enforcement

Deliverables:
- add auth identity contract and request context dependency
- enforce permissions for authored endpoints and status transitions
- allow student-only submission flows for attempts

Acceptance:
- unauthorized/forbidden cases covered in API tests
- review/publish cannot be executed by student role

## 3) Authoring Operations Expansion

Deliverables:
- add authored topic and concept management endpoints
- add archived visibility controls for topic and concept lists
- add authored question update/versioning behavior with review-state reset
- support listing/filtering authored questions by status/topic/concept
- tighten validation for publish readiness (rubric + expected answer completeness + rubric contract quality)

Acceptance:
- academic/career/admin can manage topic and concept entities without seed edits
- archived topics and concepts are hidden by default but can be explicitly listed for ops workflows
- edited reviewed questions return to draft and increment question/rubric versions
- published or archived questions cannot be edited
- publish fails with clear errors when required authored artifacts are missing
- rubric contracts reject duplicate criterion names, duplicate or unsorted thresholds, and missing 0-percent floor

## 4) Practice Session Lifecycle

Deliverables:
- introduce explicit session state transitions
- support ordered question queue on session creation
- capture completion timestamp and summary metrics
- expose explicit session start/complete endpoints
- expose practice-session list filters for `status`, `source`, `started_after`, `started_before`, `current_question_id`, and `has_remaining`

Acceptance:
- session read model shows lifecycle state and progress counters
- tests cover normal and invalid transition paths
- session list rejects invalid status filters with `422`
- session list supports operator triage by start-time window, current question, and remaining queue presence

## 5) Pilot Operations Readiness

Deliverables:
- update README and architecture docs for Sprint 2 workflows
- update deployment readiness checklist with migration/auth requirements
- define pilot smoke-test checklist (health, auth, authoring, submit, session close)
- document a local rehearsal sequence that bootstraps the app, exercises authored content, submits an attempt, and closes the session

Acceptance:
- one command sequence for local pilot simulation is documented
- known constraints are explicitly listed for stakeholders

Smoke-test checklist:
1. `just bootstrap`
2. `just migrate`
3. `just up`
4. `curl http://127.0.0.1:8000/healthz`
5. `curl http://127.0.0.1:8000/api/v1/reference/assessment-modes`
6. Create a topic and concept with `X-User-Role: academic`
7. Create an authored question bundle, then transition it `draft -> reviewed -> published`
8. Create a practice session with `source=pilot-smoke` and the published question in `question_queue`
9. Start the session, submit the authored attempt, and verify the session detail counters
10. Complete the session and confirm the completed filter returns the session
11. `just down`
12. `just teardown-local` if you want a clean SQLite reset

## Suggested Sequence

1. Migrations foundation
2. Auth primitives and role guards
3. Authoring operations expansion
4. Session lifecycle enhancements
5. Documentation and smoke-test hardening

## Test Strategy

- unit tests for role checks, lifecycle transitions, and validation rules
- API tests for new/changed endpoints and forbidden paths
- persistence tests validating migration-backed schema and relational integrity
- regression pass on existing reference and authored submit flows

## Definition of Done

Sprint 2 is complete when:
- migration-first persistence is working and tested
- role enforcement protects authored/review workflows
- authored operations are sufficient for non-seed content growth
- session lifecycle supports start-to-finish practice execution
- docs provide a reliable pilot runbook for internal users

## Risk Register

- migration drift risk while schema evolves quickly
- auth scope creep into full identity platform
- lifecycle complexity causing regressions in existing submit path

Mitigation:
- land migrations in small PRs
- keep auth minimal and role-claim based for this sprint
- maintain backward-compatible response fields where possible

## Remaining Sprint 2 Backlog

1. No remaining Sprint 2 work in the practice-session filter slice.
