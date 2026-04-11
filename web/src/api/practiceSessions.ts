import { requestJson, toQueryString } from "./client";
import type {
  PracticeSessionCreate,
  PracticeSessionListFilters,
  PracticeSessionRecord,
  PracticeSessionSummary,
} from "../types/api";

export function listPracticeSessions(filters: PracticeSessionListFilters = {}): Promise<PracticeSessionSummary[]> {
  return requestJson<PracticeSessionSummary[]>(
    `/api/v1/practice-sessions${toQueryString(filters)}`,
    {},
    { requestLabel: "Loading practice sessions" }
  );
}

export function getPracticeSession(sessionId: string): Promise<PracticeSessionRecord> {
  return requestJson<PracticeSessionRecord>(
    `/api/v1/practice-sessions/${sessionId}`,
    {},
    { requestLabel: `Loading practice session ${sessionId}` }
  );
}

export function createPracticeSession(payload: PracticeSessionCreate): Promise<PracticeSessionRecord> {
  return requestJson<PracticeSessionRecord>(
    "/api/v1/practice-sessions",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    { requestLabel: "Creating practice session" }
  );
}

export function startPracticeSession(sessionId: string): Promise<PracticeSessionRecord> {
  return requestJson<PracticeSessionRecord>(
    `/api/v1/practice-sessions/${sessionId}/start`,
    {
      method: "POST",
      body: JSON.stringify({ status: "in_progress" }),
    },
    { requestLabel: `Starting practice session ${sessionId}` }
  );
}

export function completePracticeSession(sessionId: string): Promise<PracticeSessionRecord> {
  return requestJson<PracticeSessionRecord>(
    `/api/v1/practice-sessions/${sessionId}/complete`,
    {
      method: "POST",
      body: JSON.stringify({ status: "completed" }),
    },
    { requestLabel: `Completing practice session ${sessionId}` }
  );
}
