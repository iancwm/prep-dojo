# Sprint 1 Spec: Conceptual Model and Assessment Framework

Source inputs:
- [idea.md](/Users/iancwm/git/prep-dojo/idea.md)
- [SMU Finance Interview Prep Engine](/Users/iancwm/git/prep-dojo/docs/smu-finance-interview-prep-engine.md)

## Sprint Goal

Define the engine before defining the content.

Sprint 1 should produce the conceptual data model and assessment framework for the SMU finance interview prep system. The point is to make the system structurally correct before any large-scale content work or UI polish begins.

This sprint is not about building a big library of questions. It is about making sure the product can represent:
- what a topic is
- what a concept is
- what kinds of assessment modes exist
- how an answer is judged
- how feedback is stored
- how a student progresses through material

## Outcome

Sprint 1 has effectively been completed as a backend foundation.

Shipped against this spec:
- Pydantic domain contracts
- SQLAlchemy persistence models
- local DB initialization
- seeded valuation module and question catalog
- authored question-bundle creation and retrieval
- authored question submission for stored free-text prompts
- rubric-backed scoring
- persistence of attempts, scores, feedback, sessions, and progress

Still deferred from the larger roadmap:
- authored content management
- auth and role enforcement
- migrations
- UI flows

## Why This Sprint Exists

The original idea document already points at the right implementation shape:
- FastAPI backend
- Pydantic models
- PostgreSQL with JSONB for flexible payloads
- a review workflow
- practice sessions

That stack is useful only if the core model is sound. If the system cannot clearly represent a question, a rubric, a student attempt, and a scoring outcome, everything else will become messy later.

This sprint protects against that.

## Scope

### In Scope
- Core entity model
- Assessment framework taxonomy
- Question and answer contracts
- Rubric structure
- State transitions for authored content and student attempts
- One end-to-end worked example
- Invariants the implementation must preserve

### Out of Scope
- Full student-facing UI
- Large content production
- Automated question generation
- Analytics dashboards
- Production authentication
- Multi-role approval flows beyond the minimum needed to validate the model

## Design Principles

1. Structure first, content second.
2. Separate authored truth from student interaction data.
3. Keep metadata relational, keep flexible payloads in JSONB.
4. Every answer must be judged against an explicit rubric.
5. The model should support mentor-authored content and LLM-assisted generation, but not depend on either one.

## Conceptual Data Model

### Core Entities

#### `Topic`
A high-level area students study.

Examples:
- Corporate finance
- Valuation
- Financial statements
- Modeling
- Interview fit

Fields:
- `id`
- `slug`
- `title`
- `description`
- `order_index`
- `status`

#### `Concept`
A smaller unit inside a topic.

Examples:
- Enterprise value
- EBITDA
- Accretion/dilution
- Three-statement links
- WACC

Fields:
- `id`
- `topic_id`
- `title`
- `definition`
- `difficulty`
- `prerequisites`
- `status`

#### `AssessmentMode`
The way a concept is tested.

Examples:
- multiple choice
- short answer
- oral recall
- case prompt
- modeling exercise

Fields:
- `id`
- `name`
- `description`
- `scoring_style`
- `timing_style`

#### `Question`
A specific prompt attached to a concept and assessment mode.

Fields:
- `id`
- `concept_id`
- `assessment_mode_id`
- `prompt`
- `context`
- `difficulty`
- `status`
- `author_type`
- `author_id`
- `payload_json`

`payload_json` is where question-specific shape lives. That is the JSONB part from the original idea.

#### `Rubric`
The scoring structure for a question.

Fields:
- `id`
- `question_id`
- `criteria_json`
- `scoring_scale`
- `weighting`
- `review_notes`
- `status`

#### `ExpectedAnswer`
The canonical answer or answer shape.

Fields:
- `id`
- `question_id`
- `answer_text`
- `answer_outline`
- `key_points`
- `acceptable_variants`

#### `CommonMistake`
Known failure patterns for a question or concept.

Fields:
- `id`
- `question_id`
- `mistake_text`
- `why_it_is_wrong`
- `remediation_hint`

#### `StudentAttempt`
A student’s response to a question.

Fields:
- `id`
- `student_id`
- `question_id`
- `session_id`
- `response_json`
- `submitted_at`
- `status`

#### `Score`
The outcome of evaluating an attempt.

Fields:
- `id`
- `attempt_id`
- `overall_score`
- `rubric_breakdown_json`
- `scored_by`
- `scored_at`
- `scoring_method`

#### `Feedback`
The feedback shown to the student.

Fields:
- `id`
- `attempt_id`
- `strengths`
- `gaps`
- `next_step`
- `feedback_json`

#### `ModuleProgress`
The student’s progression through a topic/module.

Fields:
- `id`
- `student_id`
- `topic_id`
- `concept_mastery_json`
- `last_seen_at`
- `progress_status`

## Assessment Framework

The assessment framework should separate three questions:

1. Did the student know the fact?
2. Did the student explain the reasoning?
3. Did the student apply the concept in the right recruiting context?

That gives the system a way to score beyond “right or wrong.”

### Assessment Dimensions

- **Recall**: Can the student retrieve the core fact or definition?
- **Reasoning**: Can the student explain why the answer is true?
- **Application**: Can the student use the concept in interview context?
- **Clarity**: Is the answer structured and legible under pressure?
- **Completeness**: Did the student hit the required points?

Not every mode uses every dimension. A short-answer theory question may use all five. A multiple-choice question may only use recall and application.

### Rubric Shape

Each rubric should contain:
- criterion name
- criterion description
- weight
- scoring range
- failure signals
- sample strong response fragments

This should be stored as structured JSON, not prose alone, so the scoring engine can use it consistently.

### Scoring Output

Every evaluated attempt should produce:
- overall score
- per-criterion scores
- pass/fail or mastery band
- feedback text
- remediation hint
- next action

Example mastery bands:
- `needs_review`
- `partial`
- `ready_for_retry`
- `interview_ready`

## State Model

### Content Lifecycle
- `draft`
- `reviewed`
- `published`
- `archived`

### Student Attempt Lifecycle
- `created`
- `submitted`
- `scored`
- `needs_followup`
- `complete`

### Progress Lifecycle
- `not_started`
- `in_progress`
- `weak`
- `strong`
- `mastered`

## Data Boundaries

### Authored By Humans
- topic definitions
- concept definitions
- assessment mode definitions
- rubrics
- expected answers
- common mistakes

### May Be Assisted By LLMs
- draft question variations
- draft explanations
- draft remediation hints

### Must Be Student-Owned
- attempts
- scores
- feedback history
- progress state

### Must Be System-Derived
- mastery band
- question sequence recommendations
- progress summaries

## Feasible Sprint Deliverables

Sprint 1 should output:
- an entity diagram or schema draft
- rubric taxonomy
- question/answer contract
- state transition map
- one worked example covering one topic and one assessment mode
- a short list of invariants for implementation

## Delivery Status

- `entity diagram or schema draft`
  Delivered as typed domain and SQLAlchemy models.
- `rubric taxonomy`
  Delivered in seeded rubric data and scoring contracts.
- `question/answer contract`
  Delivered.
- `state transition map`
  Partially delivered through persisted statuses and module progress.
- `one worked example`
  Delivered as the valuation reference flow.
- `implementation invariants`
  Reflected in tests and model constraints.

## Invariants

1. A question must always belong to a concept.
2. A concept must always belong to a topic.
3. Every question must have a rubric.
4. Every scored attempt must reference the rubric version used.
5. Student attempts must never overwrite canonical answers.
6. Published content must be distinguishable from draft content.
7. JSONB payloads must still be validated by an explicit schema.

## Worked Example

Topic: Valuation

Concept: Enterprise value versus equity value

Assessment mode: short answer

Question:
“Explain why enterprise value is used in valuation multiples and when it is more informative than equity value.”

Rubric dimensions:
- recall: defines EV and equity value correctly
- reasoning: explains capital structure differences
- application: ties answer to interview or recruiting context
- clarity: answer is concise and structured

Expected answer:
- EV captures the value of the operating business
- equity value reflects what belongs to shareholders
- EV is better for operating comparisons because it normalizes capital structure
- the student should say when each metric is useful

Common mistake:
- mixing up EV with market cap
- giving a definition without explaining why interviewers care

Feedback example:
- strong: correct definition and useful comparison
- gap: omitted why capital structure matters
- next step: answer again in 30 seconds, out loud

## Acceptance Criteria

Sprint 1 is done when:
- the core data model is explicit and internally consistent
- the assessment rubric can evaluate at least one concrete question type
- the state model supports content and student progression
- the system can represent student attempts without blurring them into canonical content
- one example finance question can be mapped cleanly through the whole model

## Acceptance Check

- Core data model
  Met.
- Rubric evaluates a concrete question type
  Met for stored short-answer questions.
- State model supports content and student progression
  Met at the reference-flow level.
- Student attempts are separate from canonical content
  Met.
- One example finance question maps cleanly through the full model
  Exceeded. There are now two stored reference questions.

## Next Sprint Input

Once this sprint is complete, the next step is implementation of the minimum backend schema and one API path for:
- fetching a practice question
- submitting an answer
- returning structured feedback

That is the first executable slice.

## Current Next Step

The project has already moved past the first executable slice. The next meaningful sprint is:
- replace seeded-only content assumptions with authored question creation and retrieval
- add migration management
- define the first non-reference practice-session workflow
