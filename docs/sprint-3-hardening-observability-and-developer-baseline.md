# Sprint 3 Spec: Hardening, Observability, and Developer Baseline

Source inputs:
- [Sprint 2 Spec](/home/iancwm/git/prep-dojo/docs/sprint-2-pilot-readiness-and-content-operations.md)
- [Architecture](/home/iancwm/git/prep-dojo/ARCHITECTURE.md)
- [Cloud Deployment Readiness](/home/iancwm/git/prep-dojo/docs/cloud-deployment-readiness.md)
- [SMU Finance Interview Prep Engine](/home/iancwm/git/prep-dojo/docs/smu-finance-interview-prep-engine.md)

## Sprint Goal

Make the application easier to debug, safer to deploy, and less fragile for everyday developers.

Sprint 3 is not about hyperscale infrastructure.

It is about getting the repo to a "good enough baseline" where:
- developers can understand failures quickly
- local and non-local runtime behavior is less surprising
- the data model has fewer sharp edges in the most important workflows
- deployment assumptions are written down and safer by default

## Target Outcome

By the end of Sprint 3:
- API requests and failures are observable enough to debug real issues quickly
- the app has a clearer distinction between development and non-development runtime behavior
- the highest-risk data-model seams have explicit guardrails or documented follow-up paths
- deployment/readiness docs describe the system that actually exists today

## Scope

### In Scope
- observability baseline for API requests and failures
- runtime and deployment hardening that reduces surprise in non-local environments
- data-model and workflow guardrails for the highest-risk existing seams
- documentation updates for developer operations and deployment readiness

### Out of Scope
- Kubernetes, service mesh, distributed tracing, or cloud-native platform work
- large-scale analytics pipelines
- full identity platform
- broad schema redesign or wholesale JSON-to-relational migration
- performance work for internet-scale traffic

## Product Principle

This sprint should optimize for the biggest wins at the lowest effort.

That means:
- prefer request logging over a full observability platform
- prefer readiness checks over complex orchestration
- prefer auditability for key workflows over perfect event sourcing
- prefer small data-model guardrails over broad schema rewrites

## Prioritization Heuristic

Use this order:

1. makes debugging faster
2. reduces deployment mistakes
3. lowers the chance of silent bad state
4. improves docs so new developers stop guessing

If a task does not help one of those four, it is probably not Sprint 3.

## Workstreams

## 1) Observability Baseline

Why this is first:
- current observability is too weak for efficient debugging
- this is a high-win, relatively low-effort slice

Deliverables:
- add request middleware that records method, path, status, duration, and request id
- add structured log output for handled errors and unexpected exceptions
- add request-id propagation in responses so frontend and backend logs can be correlated
- add a lightweight readiness endpoint beyond `/healthz`
- improve frontend-facing API error copy so failed backend calls are identifiable by purpose

Acceptance:
- every API request produces one structured access log entry
- 4xx and 5xx responses are logged with request id and route context
- `/readyz` fails when the DB cannot be reached
- frontend error copy identifies which backend action failed

Low-effort / high-win rationale:
- this is boring engineering, but it pays off immediately
- it reduces time-to-debug for every future sprint

## 2) Runtime and Deployment Safety

Why this is second:
- current config shape is good, but too development-first
- the main risk is accidental deployment with dev assumptions

Deliverables:
- define environment-aware runtime expectations for development vs non-development
- ensure non-development paths prefer migrations over metadata schema creation
- add explicit docs and checks for production-safe server settings like `reload = false`
- refresh deployment readiness documentation to match the current migration-aware codebase
- clarify frontend deployment expectations for same-origin or proxied operation

Acceptance:
- non-development config paths are documented and sanity-checked
- migration-first startup behavior is the documented default for non-local environments
- deployment docs no longer claim Alembic is missing
- frontend and backend runtime assumptions are both documented

Low-effort / high-win rationale:
- this is mostly config, guardrails, and docs
- it prevents avoidable rollout mistakes without building a platform team

## 3) Data Model Guardrails

Why this is third:
- the model is good enough for product iteration, but some seams need tightening
- the goal is not to redesign it, only to reduce the most dangerous ambiguity

Deliverables:
- document which JSON fields are intentionally flexible and which are technical debt
- add audit-friendly metadata for authored workflow transitions where practical
- tighten invariants around practice-session and attempt workflows
- make reference-user and real-user assumptions more explicit in docs and code comments
- identify the next data-model normalization candidates without implementing a full migration campaign

Acceptance:
- the highest-risk workflow invariants are documented and covered by tests
- authored transition paths have clearer traceability than "state changed somehow"
- the team has an explicit shortlist of JSON-heavy areas that should be normalized later

Low-effort / high-win rationale:
- small guardrails now are much cheaper than debugging messy historical state later

## 4) Developer Operations and Documentation

Why this matters:
- the repo has grown enough that developer confusion is now a real cost
- docs are partially stale and new contributors will make wrong assumptions

Deliverables:
- update `README.md` for current backend + frontend + local workflow reality
- refresh `ARCHITECTURE.md` to match Sprint 2 and Sprint 3-era behavior
- refresh `docs/cloud-deployment-readiness.md`
- add a short hardening checklist for local developer validation
- document what "good enough for pilot" means versus what still blocks production

Acceptance:
- a new developer can bootstrap backend and frontend from the docs without guesswork
- architecture and deployment docs no longer contradict the codebase
- current constraints are explicit, not tribal knowledge

## Suggested Sequence

1. Observability baseline
2. Runtime and deployment safety
3. Data model guardrails
4. Documentation refresh

This order matters.

Observability makes every later change easier to validate.

## Ticket-Ready Backlog

### P0

1. Add request-id middleware, structured access logs, and structured exception logs
2. Add `/readyz` with database connectivity check
3. Make non-development runtime paths explicitly migration-first
4. Refresh `docs/cloud-deployment-readiness.md` so it reflects the real codebase

### P1

5. Add authored transition audit metadata or event logging for review/publish/archive actions
6. Document JSON-field intent and normalization candidates in `ARCHITECTURE.md`
7. Add a small hardening checklist to `README.md` for local developer validation

### P2

8. Tighten attempt/session invariants and add regression tests around the sharpest workflow edges
9. Clarify seeded reference-user assumptions versus future real-user identity handling

## Parallel Ticket Chunks

These tickets are intentionally split to minimize file overlap so they can be worked in parallel.

### Ticket S3-1: Request Observability Baseline

Goal:
- make backend request failures easier to trace during development and pilot use

Primary ownership:
- `app/core/observability.py`
- `tests/test_observability.py`

Integration touchpoints:
- `app/main.py`

Deliverables:
- request-id generation
- request timing capture
- structured access logs
- structured exception logs usable in local and non-local environments

### Ticket S3-2: Readiness and Runtime Safety

Goal:
- reduce surprise between development and non-development runtime behavior

Primary ownership:
- `app/db/session.py`
- `app/core/settings.py`
- `app/cli.py`
- `docs/cloud-deployment-readiness.md`
- `tests/test_db_session.py`

Integration touchpoints:
- `app/main.py`

Deliverables:
- database readiness check support
- clearer runtime-mode helpers
- safer documented defaults for non-development operation
- refreshed deployment-readiness documentation

### Ticket S3-3: Authoring Audit and Data Guardrails

Goal:
- add low-cost traceability to the highest-risk authored workflow transitions

Primary ownership:
- `app/db/models.py`
- `app/services/authoring.py`
- `app/schemas/domain.py`
- `alembic/versions/*`
- `tests/test_authoring_operations.py`

Integration touchpoints:
- `app/main.py` only if response wiring changes are required

Deliverables:
- audit-friendly metadata for authored question review/publish/archive transitions
- migration support for any new audit fields or tables
- tests proving transition traceability

### Main-Agent Integration Slice

Reserved for the main agent:
- `app/main.py`
- final wiring between middleware, readiness route, and supporting helpers
- test execution and conflict resolution

## Test Strategy

- unit tests for request-id generation, readiness logic, and runtime guards
- API tests for readiness and error-path logging behavior where feasible
- regression tests for authored transition traceability and attempt/session invariants
- one local developer smoke path covering:
  - backend startup
  - frontend startup
  - readiness check
  - authored create/review/publish flow
  - practice submit flow

## Definition of Done

Sprint 3 is complete when:
- the app is materially easier to debug than it was at the end of Sprint 2
- non-local deployment behavior is safer and less ambiguous
- the highest-risk current data-model seams have explicit guardrails
- developer-facing docs describe the system honestly

## Risk Register

- observability work grows into platform work
- data-model cleanup turns into an unbounded redesign
- deployment hardening drifts into premature infra engineering

Mitigation:
- keep tooling lightweight
- harden only the paths already in use
- document later normalization work instead of boiling the ocean

## Explicit Non-Goals

Sprint 3 should not produce:
- Kubernetes manifests
- distributed tracing stacks
- multi-region anything
- event-driven microservices
- a total relational remodel of the content schema

If a task smells like "what would a hyperscale company do," it is probably out of scope.

## Success Test

At the end of Sprint 3, a developer should be able to answer these questions quickly:

1. Why did this request fail?
2. Is the app actually ready to serve traffic?
3. Which runtime mode am I in?
4. Which current data-model shortcuts are acceptable, and which are future cleanup items?

If the sprint does not improve those answers, it missed the point.
