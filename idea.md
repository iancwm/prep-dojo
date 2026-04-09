# 🧱 Agent-Ready Specification: SMU Finance Interview Prep Prototype

*Structured for direct ingestion by coding agents (Cursor, Claude, Copilot, Devin, etc.). Clear boundaries, explicit contracts, zero ambiguity.*

---

## 📦 1. Tech Stack (Agent-Optimized)

| Layer | Technology | Version/Config | Why for Agents |
|-------|------------|----------------|----------------|
| **Backend API** | FastAPI | Python 3.11+, `pydantic` v2, `uvicorn` | Native Pydantic integration, auto-docs, async-ready, highly deterministic |
| **AI Orchestration** | `instructor` + `litellm` | `pip install instructor litellm` | Guarantees schema-compliant JSON, auto-retry on validation fail, provider-agnostic |
| **Database** | PostgreSQL | 15+, JSONB for question payload, SQLAlchemy 2.0 async | Relational metadata + flexible JSON storage, Moodle-compatible |
| **Migrations** | Alembic | `alembic init alembic` | Version-controlled schema, agent-friendly CLI |
| **Frontend** | React + TypeScript | Vite, Tailwind, shadcn/ui, React Query, Zustand | Component-driven, strong typing, predictable state flow |
| **Auth** | JWT (HS256) | `python-jose` + middleware | Role-based (`student`, `academic`, `career`, `admin`), swappable to OIDC/LTI later |
| **Testing** | `pytest` + `httpx` + `playwright` | Fixtures + golden-set JSON | Deterministic validation of AI outputs & UI flows |
| **Infra** | Docker Compose | `docker-compose.yml` with 3 services | One-command local dev, reproducible for agents |

---

## 🌐 2. System Architecture & Data Flow

```
┌─────────────┐     ┌──────────────────────┐     ┌──────────────┐
│   React UI  │────▶│   FastAPI Backend    │────▶│ PostgreSQL   │
│ (Student +  │     │ • /api/v1/generate   │     │ • questions  │
│  Admin)     │◀────│ • /api/v1/reviews    │◀────│ • users      │
└─────────────┘     │ • /api/v1/practice   │     │ • sessions   │
                    │ • /api/v1/analytics  │     │ • audit_logs │
                    └────────┬─────────────┘     └──────────────┘
                             │
                    ┌────────▼─────────────┐
                    │   AI Generation      │
                    │ • instructor + LLM   │
                    │ • Pydantic validation│
                    │ • Retry on schema fail│
                    └──────────────────────┘
```

**Data Boundary Rule:** 
- `questions` table stores **one JSONB column** per question (`data jsonb`) validated against the `FinanceQuestion` Pydantic model.
- All relational metadata (status, reviewer IDs, timestamps) lives in normalized tables.
- Agents must **never** bypass Pydantic validation for DB inserts.

---

## 🧑‍🎓 3. User Journey: Student

| Step | UI State | Action | API Call | Data Flow |
|------|----------|--------|----------|-----------|
| 1 | Login → Dashboard | View readiness score, weak domains, recommended practice | `GET /api/v1/analytics/student/me` | Fetches `session_responses` aggregates |
| 2 | Session Config | Select role tags, difficulty, question count, mode (timed/practice) | N/A (client state) | Stores config in Zustand |
| 3 | Practice Start | Click "Begin Session" | `POST /api/v1/practice/sessions` | Returns `session_id` + array of published questions |
| 4 | Question Render | Displays prompt, options/input, explanation toggle | N/A | Client caches questions locally |
| 5 | Submit Answer | Select option / type answer / upload calc → Submit | `POST /api/v1/practice/sessions/{id}/submit` | Validates response, auto-grades, returns `feedback` + `is_correct` |
| 6 | Feedback View | Shows correct/incorrect, explanation, teaching note, reference | N/A | Displays `explanations` from question JSON |
| 7 | Session End | Completes all questions → "Finish" | `PATCH /api/v1/practice/sessions/{id}/complete` | Updates `completed_at`, recalculates readiness score |
| 8 | Review Loop | Spaced repetition surfaces weak areas in next session | `GET /api/v1/practice/recommendations` | Filters by `bloom_level`, `domain`, past accuracy |

**Agent Guardrail:** Student UI never calls `/generate` or `/reviews`. Only `/practice/*` and `/analytics/*`.

---

## 👨‍🏫 4. User Journey: Admin / Reviewer (Academic + Career)

| Step | UI State | Action | API Call | Data Flow |
|------|----------|--------|----------|-----------|
| 1 | Login → Review Queue | See tabs: `draft`, `pending_academic`, `pending_career`, `approved`, `rejected` | `GET /api/v1/reviews/queue` | Filters by user role + status |
| 2 | Generate Draft | Select type, domain, difficulty → "Generate" | `POST /api/v1/questions/generate` | Returns validated `FinanceQuestion` with `status: draft` |
| 3 | Edit & Refine | Inline edit prompt, options, explanations, metadata | `PATCH /api/v1/questions/{id}` | Updates `data` JSONB, version bump |
| 4 | Academic Review | Verify technical accuracy → "Approve Technical" | `PATCH /api/v1/reviews/{id}` | Sets `status: pending_career`, logs `academic_reviewer_id` |
| 5 | Career Review | Verify interview realism → "Approve Realism" | `PATCH /api/v1/reviews/{id}` | Sets `status: published`, logs `career_reviewer_id` |
| 6 | Rejection/Revision | Add comment → "Request Revision" | `PATCH /api/v1/reviews/{id}` | Sets `status: revision_requested`, preserves edit history |
| 7 | Publish | Automatically available to student bank | Background trigger | `status: published` → visible in `/practice` queries |
| 8 | Monitor & Iterate | View accuracy rates, student feedback, flag low-performing questions | `GET /api/v1/analytics/questions/{id}` | Triggers prompt refinement queue |

**Agent Guardrail:** Approval requires **two distinct role tokens**. One approval cannot advance status alone. State machine enforced in DB + Pydantic.

---

## 🔌 5. Core API Contracts (Agent-Ready)

### `POST /api/v1/questions/generate`
```json
// Request
{
  "question_type": "mcq_single",
  "domain": {"primary": "valuation", "subdomains": ["wacc"]},
  "difficulty": "intermediate",
  "role_tags": ["investment_banking_analyst"]
}

// Response (200)
{ "id": "uuid", "status": "draft", "data": { /* full FinanceQuestion JSON */ } }
```

### `PATCH /api/v1/reviews/{question_id}`
```json
// Request
{
  "action": "approve" | "reject",
  "reviewer_role": "academic" | "career",
  "comments": "string (optional)"
}

// Response (200)
{ "id": "uuid", "status": "pending_career", "governance": { "reviewed_by": [...] } }
```

### `POST /api/v1/practice/sessions`
```json
// Request
{ "role_tags": ["credit_research"], "difficulty": "foundational", "count": 10 }

// Response (200)
{ "session_id": "uuid", "questions": [ { "id": "...", "prompt": {...}, "options": [...] } ] }
```

### `POST /api/v1/practice/sessions/{id}/submit`
```json
// Request
{ "question_id": "uuid", "response": { "selected_option_ids": ["B"] } }

// Response (200)
{ "is_correct": true, "feedback": { "explanation": "...", "teaching_note": "..." } }
```

---

## 🗄️ 6. Database Schema (Normalized + JSONB)

```sql
-- Core tables (Alembic will generate)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  role VARCHAR(20) CHECK (role IN ('student', 'academic', 'career', 'admin')),
  email VARCHAR(255) UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  data JSONB NOT NULL, -- Validated FinanceQuestion payload
  status VARCHAR(20) CHECK (status IN ('draft', 'pending_academic', 'pending_career', 'published', 'revision_requested', 'archived')),
  version INT DEFAULT 1,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
  reviewer_id UUID REFERENCES users(id),
  reviewer_role VARCHAR(20),
  action VARCHAR(20),
  comments TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE practice_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  config JSONB,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  score NUMERIC(5,2)
);

CREATE TABLE session_responses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES practice_sessions(id) ON DELETE CASCADE,
  question_id UUID REFERENCES questions(id),
  response_data JSONB,
  is_correct BOOLEAN,
  feedback_shown BOOLEAN DEFAULT FALSE,
  submitted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type VARCHAR(50),
  entity_id UUID,
  action VARCHAR(50),
  actor_id UUID REFERENCES users(id),
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  metadata JSONB
);
```

---

## 🤖 7. Agent Generation Blueprint

### 📐 How to Prompt Coding Agents (Copy-Paste Ready)

**Phase 1: Foundation**
```
Generate a Python 3.11 FastAPI project with:
- Pydantic v2 model matching the FinanceQuestion schema (discriminated union on question_type)
- PostgreSQL + SQLAlchemy 2.0 async setup with Alembic
- JWT middleware enforcing role-based access (student, academic, career)
- Return only: /models, /db, /core, /main.py
```

**Phase 2: AI Generation Service**
```
Create /services/generate.py using instructor + litellm.
- Accept domain/difficulty/type → call LLM → return validated FinanceQuestion
- Implement auto-retry (max 3) on Pydantic ValidationError
- Log prompt_hash, response_hash, model, timestamp to audit_logs
- Return only the service + unit tests using golden-set fixtures
```

**Phase 3: Review Workflow API**
```
Implement /routers/reviews.py and /routers/questions.py:
- POST /questions/generate → saves as status: draft
- GET /reviews/queue → filters by role + status
- PATCH /reviews/{id} → enforces 2-role approval state machine
- Use SQLAlchemy async, Pydantic response models, 200/400/403 status codes
```

**Phase 4: Practice Engine**
```
Implement /routers/practice.py:
- POST /sessions → samples published questions, returns masked data (no explanations)
- POST /sessions/{id}/submit → auto-grades, returns feedback, saves response
- Enforce role=student only. Log to session_responses
```

**Phase 5: Frontend Scaffolding**
```
Generate Vite + React + TypeScript + Tailwind + shadcn/ui project:
- /src/pages/ReviewQueue.tsx (tabs, inline edit, approve/reject buttons)
- /src/pages/PracticeSession.tsx (question render, submit, feedback toggle)
- React Query hooks for all /api/v1/* endpoints
- Zustand store for auth + session state
```

### 🛡️ Agent Guardrails
1. **Never** store unvalidated JSON in DB. Pydantic must run before insert.
2. **Never** bypass role checks. Middleware must verify JWT claims.
3. **Always** use explicit HTTP status codes. No `200` for validation failures.
4. **Always** version questions on edit. Append to `version_history` in JSON.
5. **Always** mock LLM responses in tests. Use `golden_set/` fixtures.

---

## ✅ Next Step

Pick **one** to generate first. I'll output production-ready, agent-consumable code:
1. `Pydantic models + Alembic setup` (DB foundation)
2. `instructor + LLM generation service + retry logic`
3. `FastAPI routers for review workflow + state machine`
4. `React Review Queue UI + React Query hooks`

Tell me your starting point, and I'll deliver the exact files, configs, and test fixtures your coding agents need to run immediately. 🛠️
