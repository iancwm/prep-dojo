import type {
  AttemptSubmitResult,
  AuthoredQuestionBundleRecord,
  PracticeSessionRecord,
  PracticeSessionStatus,
} from "../types/api";
import type { StudentAnswerDraft, StudentQuestion, StudentResult, StudentSession } from "../types/student";

const RESULT_CACHE_PREFIX = "prep-dojo.practice.result";

export function mapBundleToStudentQuestion(bundle: AuthoredQuestionBundleRecord): StudentQuestion {
  const { question } = bundle;
  const payload = question.payload;

  if (payload.question_type === "mcq_single") {
    return {
      id: question.id,
      title: bundle.concept.title,
      prompt: payload.prompt,
      context: question.context ?? undefined,
      assessmentMode: question.assessment_mode,
      responseType: "multiple_choice",
      cue: payload.explanation,
      options: payload.options.map((option) => ({
        id: option.id,
        label: option.label,
        rationale: option.rationale ?? undefined,
      })),
    };
  }

  if (payload.question_type === "oral_recall") {
    return {
      id: question.id,
      title: bundle.concept.title,
      prompt: payload.prompt,
      context: question.context ?? undefined,
      assessmentMode: question.assessment_mode,
      responseType: "oral_transcript",
      cue: payload.cue ?? undefined,
      targetDurationSeconds: payload.target_duration_seconds ?? undefined,
    };
  }

  return {
    id: question.id,
    title: bundle.concept.title,
    prompt: payload.prompt,
    context: payload.context ?? question.context ?? undefined,
    assessmentMode: question.assessment_mode,
    responseType: "free_text",
    responseGuidance: payload.response_guidance,
    targetDurationSeconds: payload.max_duration_seconds ?? undefined,
  };
}

export function buildStudentSession(
  session: PracticeSessionRecord,
  question: StudentQuestion,
): StudentSession {
  return {
    sessionId: session.session_id,
    source: session.source,
    title: "Finance interview practice",
    subtitle: "A short, high-trust practice loop driven by authored content.",
    status: session.status,
    questionQueue: [question],
    currentQuestionId: session.current_question_id ?? question.id,
    startedAt: session.started_at,
    completedAt: session.completed_at,
    attempts: session.attempts.map((attempt) => ({
      attemptId: attempt.attempt_id,
      questionId: attempt.question_id,
      prompt: attempt.prompt,
      responseType: normalizeResponseType(attempt.response_type),
      submittedAt: attempt.submitted_at,
      overallScore: attempt.overall_score ?? 0,
      masteryBand: attempt.mastery_band ?? "needs_review",
    })),
    learnerLabel: "Candidate 01",
  };
}

export function createInitialDraft(question: StudentQuestion): StudentAnswerDraft {
  return { responseType: question.responseType };
}

export function buildStudentResult(
  sessionId: string,
  question: StudentQuestion,
  answer: StudentAnswerDraft,
  result: AttemptSubmitResult,
): StudentResult {
  return {
    sessionId,
    attemptId: result.attempt_id,
    question,
    answer,
    score: {
      overallScore: result.score.overall_score,
      masteryBand: result.score.mastery_band,
      scoringMethod: result.score.scoring_method,
      criterionScores: result.score.criterion_scores.map((criterion) => ({
        criterionName: criterion.criterion_name,
        score: criterion.score,
        maxScore: criterion.max_score,
        notes: criterion.notes ?? undefined,
      })),
    },
    feedback: result.feedback,
    completedAt: new Date().toISOString(),
  };
}

export function saveStudentResult(result: StudentResult): void {
  window.sessionStorage.setItem(resultCacheKey(result.sessionId), JSON.stringify(result));
}

export function loadStudentResult(sessionId: string): StudentResult | null {
  const raw = window.sessionStorage.getItem(resultCacheKey(sessionId));
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as StudentResult;
  } catch {
    return null;
  }
}

export function formatBandLabel(band: StudentResult["score"]["masteryBand"]): string {
  switch (band) {
    case "interview_ready":
      return "Interview ready";
    case "ready_for_retry":
      return "Ready for retry";
    case "partial":
      return "Partial";
    case "needs_review":
      return "Needs review";
  }
}

export function formatStatusLabel(status: PracticeSessionStatus): string {
  switch (status) {
    case "created":
      return "Ready";
    case "in_progress":
      return "In progress";
    case "completed":
      return "Completed";
  }
}

function resultCacheKey(sessionId: string): string {
  return `${RESULT_CACHE_PREFIX}.${sessionId}`;
}

function normalizeResponseType(value: string): StudentQuestion["responseType"] {
  if (value === "multiple_choice") {
    return "multiple_choice";
  }

  if (value === "oral_transcript") {
    return "oral_transcript";
  }

  return "free_text";
}
