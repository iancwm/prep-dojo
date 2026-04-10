import { requestJson, toQueryString } from "./client";
import type {
  AttemptSubmitResult,
  AuthoredQuestionBundleCreate,
  AuthoredQuestionBundleRecord,
  AuthoredQuestionSummary,
  ConceptCreate,
  ConceptRecord,
  ContentStatusTransitionRequest,
  ContentStatusTransitionResult,
  StudentAttemptCreate,
  TopicCreate,
  TopicRecord,
} from "../types/api";

const operatorHeaders = {
  "X-User-Role": "academic",
};

export function listAuthoredQuestions(filters: {
  status?: string | null;
  topic_slug?: string | null;
  concept_slug?: string | null;
} = {}): Promise<AuthoredQuestionSummary[]> {
  return requestJson<AuthoredQuestionSummary[]>(
    `/api/v1/authored/questions${toQueryString(filters)}`,
    {
      headers: operatorHeaders,
    },
    { requestLabel: "Loading authored questions" }
  );
}

export function getAuthoredQuestion(questionId: string): Promise<AuthoredQuestionBundleRecord> {
  return requestJson<AuthoredQuestionBundleRecord>(
    `/api/v1/authored/questions/${questionId}`,
    {
      headers: operatorHeaders,
    },
    { requestLabel: `Loading authored question ${questionId}` }
  );
}

export function createAuthoredQuestion(payload: AuthoredQuestionBundleCreate): Promise<AuthoredQuestionBundleRecord> {
  return requestJson<AuthoredQuestionBundleRecord>(
    "/api/v1/authored/questions",
    {
      method: "POST",
      headers: operatorHeaders,
      body: JSON.stringify(payload),
    },
    { requestLabel: "Creating authored question bundle" }
  );
}

export function transitionAuthoredQuestionStatus(
  questionId: string,
  payload: ContentStatusTransitionRequest
): Promise<ContentStatusTransitionResult> {
  return requestJson<ContentStatusTransitionResult>(`/api/v1/authored/questions/${questionId}/status`, {
    method: "POST",
    headers: operatorHeaders,
    body: JSON.stringify(payload),
  }, { requestLabel: `Updating status for question ${questionId}` });
}

export function submitAuthoredQuestionAttempt(
  questionId: string,
  payload: StudentAttemptCreate
): Promise<AttemptSubmitResult> {
  return requestJson<AttemptSubmitResult>(`/api/v1/authored/questions/${questionId}/submit`, {
    method: "POST",
    body: JSON.stringify(payload),
  }, { requestLabel: `Submitting attempt for question ${questionId}` });
}

export function listTopics(params: { status?: string | null; include_archived?: boolean } = {}): Promise<TopicRecord[]> {
  return requestJson<TopicRecord[]>(`/api/v1/authored/topics${toQueryString(params)}`, {
    headers: operatorHeaders,
  }, { requestLabel: "Loading authored topics" });
}

export function createTopic(payload: TopicCreate): Promise<TopicRecord> {
  return requestJson<TopicRecord>(
    "/api/v1/authored/topics",
    {
      method: "POST",
      headers: operatorHeaders,
      body: JSON.stringify(payload),
    },
    { requestLabel: `Creating topic ${payload.slug}` }
  );
}

export function listConcepts(params: {
  topic_slug?: string | null;
  status?: string | null;
  include_archived?: boolean;
} = {}): Promise<ConceptRecord[]> {
  return requestJson<ConceptRecord[]>(`/api/v1/authored/concepts${toQueryString(params)}`, {
    headers: operatorHeaders,
  }, { requestLabel: "Loading authored concepts" });
}

export function createConcept(payload: ConceptCreate): Promise<ConceptRecord> {
  return requestJson<ConceptRecord>(
    "/api/v1/authored/concepts",
    {
      method: "POST",
      headers: operatorHeaders,
      body: JSON.stringify(payload),
    },
    { requestLabel: `Creating concept ${payload.slug ?? payload.title}` }
  );
}
