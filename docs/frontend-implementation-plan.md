# Frontend Implementation Plan

Date: 2026-04-10
Source design:
- [docs/frontend-demo-admin-and-user-experience.md](/home/iancwm/git/prep-dojo/docs/frontend-demo-admin-and-user-experience.md)

## Goal

Build a demo-quality frontend that proves the full loop:

1. operator creates and publishes a question
2. student practices it
3. the system scores it
4. the operator can see the session reflected back in the system

This plan is intentionally narrow. It optimizes for a believable product demo, not full admin coverage.

## Recommended Technical Shape

Assumption:
- create a separate frontend app inside this repo
- connect it to the existing FastAPI backend over HTTP
- use real Sprint 2 API routes for the core demo path

Recommended stack:
- React
- Vite
- TypeScript
- React Router
- lightweight fetch client, no heavy data layer required yet
- plain CSS or CSS modules with shared design tokens

Why this shape:
- fastest path to a sharp prototype
- easy to iterate on visually
- low ceremony
- no need for SSR for this demo

## App Structure

Suggested new directory:
- `web/`

Suggested layout:

```text
web/
  src/
    app/
      router.tsx
      providers.tsx
    api/
      client.ts
      authored.ts
      practiceSessions.ts
      reference.ts
    components/
      layout/
      operator/
      student/
      shared/
    pages/
      LandingPage.tsx
      OperatorHomePage.tsx
      QuestionComposerPage.tsx
      ReviewPublishPage.tsx
      StudentSessionPage.tsx
      ResultPage.tsx
    styles/
      tokens.css
      app.css
    types/
      api.ts
    utils/
      demo.ts
```

## Route Plan

Keep the route surface small and intentional.

### Public / Demo Routes

- `/`
  - landing page
  - product framing
  - links into operator and student story

### Operator Routes

- `/operator`
  - operator home
  - show recent authored questions and recent sessions
  - quick actions for create and review

- `/operator/questions/new`
  - question composer
  - topic, concept, prompt, rubric, expected answer, common mistakes

- `/operator/questions/:questionId/review`
  - content summary
  - review notes
  - transition to `reviewed`
  - transition to `published`

- `/operator/sessions/:sessionId`
  - compact session detail
  - session status
  - queue counts
  - score summary after student completion

### Student Routes

- `/practice/:sessionId`
  - ready, active, and completed session states
  - start session
  - answer active question
  - navigate to result

- `/practice/:sessionId/result`
  - score
  - mastery band
  - criterion breakdown
  - next-step copy

## Data Flow Plan

### Operator Story

#### Operator Home

Backend calls:
- `GET /api/v1/authored/questions`
- `GET /api/v1/practice-sessions?source=demo`

Role header:
- `X-User-Role: academic`

Use this page to:
- show recently created questions
- deep-link to review/publish
- deep-link to recently completed demo sessions

#### Question Composer

Backend calls:
- `POST /api/v1/authored/topics`
- `POST /api/v1/authored/concepts`
- `POST /api/v1/authored/questions`

Implementation note:
- for V1, the composer can create topic and concept inline
- if topic or concept already exists, we can handle duplicate responses gracefully or prefetch lists later

Output:
- created `question_id`
- redirect to review page

#### Review and Publish

Backend calls:
- `GET /api/v1/authored/questions/{question_id}`
- `POST /api/v1/authored/questions/{question_id}/status`

Transitions:
- `draft -> reviewed`
- `reviewed -> published`

UX note:
- make review notes required in the reviewed step
- visually separate “ready for quality check” from “live for students”

### Student Story

#### Create Session

This can happen from one of two places:
- from operator flow after publish
- from landing page demo CTA

Backend call:
- `POST /api/v1/practice-sessions`

Suggested payload:
- `source: "demo"`
- `question_queue: [published_question_id]`

#### Start Session

Backend call:
- `POST /api/v1/practice-sessions/{session_id}/start`

#### Submit Answer

Backend call:
- `POST /api/v1/authored/questions/{question_id}/submit`

Expected result:
- `attempt_id`
- `score`
- `feedback`
- `session_id`

#### Read Updated Session

Backend calls:
- `GET /api/v1/practice-sessions/{session_id}`
- `POST /api/v1/practice-sessions/{session_id}/complete`

## State Management

Keep it simple.

Recommended local state split:
- router state for ids and navigation
- page-level request state for fetch, save, submit
- one shared demo context for:
  - current persona
  - latest created question id
  - latest created session id

Do not add a complex global state library yet.

## Type Strategy

The backend already has typed Pydantic contracts. For the frontend, start with hand-authored TypeScript interfaces for only the shapes we use in the demo.

Needed client types:
- `AuthoredQuestionSummary`
- `AuthoredQuestionRecord`
- `PracticeSessionRecord`
- `StudentAttemptSubmitResult`
- `ScoreResult`
- `FeedbackResult`

Later, if the frontend grows, we can introduce generated OpenAPI types.

## UI Component Plan

### Shared

- `AppShell`
- `TopNav`
- `FlowStepper`
- `StatusBadge`
- `EmptyState`
- `LoadingBlock`
- `ErrorPanel`
- `PrimaryButton`
- `SecondaryButton`
- `Field`
- `TextArea`
- `SectionCard`

### Operator

- `QuestionList`
- `QuestionSummaryCard`
- `QuestionComposerForm`
- `RubricEditor`
- `ExpectedAnswerEditor`
- `CommonMistakesEditor`
- `ReviewChecklist`
- `PublishPanel`
- `SessionTriageList`
- `SessionSummaryCard`

### Student

- `SessionIntroCard`
- `QuestionPrompt`
- `AnswerComposer`
- `ProgressHeader`
- `ScoreHero`
- `CriterionBreakdown`
- `FeedbackPanel`
- `NextStepCard`

## Design System Guidance

The frontend should feel intentional, not default SaaS.

### Visual Goals

- serious and high-trust
- editorial rather than enterprise
- crisp hierarchy around question prompts and feedback
- warm but not playful

### Design Tokens

Start with CSS variables for:
- background
- surface
- text
- muted text
- accent
- success
- warning
- border
- shadow
- radius
- spacing scale

### Typography

Use a more expressive serif or humanist pairing for headlines with a clean sans for UI copy.

The core requirement:
- question prompts must feel important
- score/results must feel analytical

## Demo Choreography

This matters as much as the screens.

Recommended live sequence:

1. open landing page
2. enter operator home
3. create one question
4. move it through review and publish
5. create a demo practice session
6. switch to student practice route
7. start session
8. submit answer
9. show result screen
10. jump back to operator session detail

This sequence should be accessible through obvious buttons, not hidden navigation.

## What To Stub

Safe to stub in V1:
- real login
- role management UI
- topic/concept management pages beyond inline creation
- archive workflows
- deep filtering UI for every available backend filter

Keep real:
- authored question create
- review transition
- publish transition
- practice-session creation
- start session
- submit answer
- complete session
- session detail readback

## Error Handling Plan

Must-have UI behaviors:
- visible loading state for every network step
- inline validation for composer fields
- clear error messages when publish validation fails
- retry action on failed submission

Important operator cases:
- duplicate slug creation
- publish blocked by incomplete rubric or expected-answer fields
- forbidden operator action if role header is missing

Important student cases:
- missing session
- submit before session start
- invalid answer payload

## Delivery Phases

### Phase 1: Frontend Scaffold

Deliverables:
- `web/` app scaffold
- router
- app shell
- design tokens
- API client setup

Acceptance:
- app boots locally
- can hit backend health and list authored questions

### Phase 2: Operator Flow

Deliverables:
- operator home
- question composer
- review/publish page

Acceptance:
- can create a topic, concept, and question
- can move question to reviewed and published

### Phase 3: Student Flow

Deliverables:
- session create trigger
- session workspace
- answer submit flow
- result screen

Acceptance:
- can complete one full student practice path against a published question

### Phase 4: Loop Closure

Deliverables:
- operator session detail page
- linked navigation between result and session detail
- polish for transitions and copy

Acceptance:
- presenter can run the full demo without manual API calls

### Phase 5: Demo Polish

Deliverables:
- visual refinement
- seeded copy/content for the happy path
- rough-edge fixes from a dry run

Acceptance:
- demo is understandable in under 60 seconds

## Testing Plan

For the frontend prototype:

- unit tests for API helpers and key form validation
- integration tests for:
  - create question flow
  - review/publish flow
  - student session submit flow
- one demo-path smoke test

Suggested tools:
- Vitest
- React Testing Library
- Playwright later if needed

## Open Decisions

These are the only decisions we may want to lock before implementation:

1. Vite React app versus Next.js app
2. CSS modules versus plain global CSS with tokens
3. whether to seed one canonical demo question automatically for faster rehearsals

My recommendation:
- Vite
- plain CSS plus tokens
- yes, keep one canonical demo question path available

## Immediate Next Step

Implement Phase 1 and Phase 2 first.

That gets us from zero frontend to a believable operator-driven story quickly, while keeping the student flow close behind instead of lost in a big rewrite.
