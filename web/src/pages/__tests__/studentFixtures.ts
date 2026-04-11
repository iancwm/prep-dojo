import { mapBundleToStudentQuestion } from "../../data/demoSession";
import type {
  AttemptSubmitResult,
  AuthoredQuestionBundleRecord,
  PracticeSessionRecord,
} from "../../types/api";
import type { StudentAnswerDraft, StudentResult } from "../../types/student";

export const studentSessionId = "session-123";
export const studentQuestionId = "question-123";
export const studentResponseText = "I would frame the tradeoff, quantify the risk, and name the next action.";

export const studentBundle: AuthoredQuestionBundleRecord = {
  topic: {
    id: "topic-1",
    slug: "finance",
    title: "Finance",
    description: "Practice finance interview prompts.",
    order_index: 1,
    status: "published",
  },
  concept: {
    id: "concept-1",
    topic_slug: "finance",
    slug: "runway",
    title: "Cash runway",
    definition: "How long the company can operate before running out of cash.",
    difficulty: "intermediate",
    prerequisites: [],
    status: "published",
  },
  assessment_mode: {
    mode: "short_answer",
    description: "Short answer practice for a finance interview prompt.",
    scoring_style: "rubric",
    timing_style: "timed",
  },
  question: {
    id: studentQuestionId,
    concept_slug: "runway",
    external_id: "finance-runway-01",
    assessment_mode: "short_answer",
    difficulty: "intermediate",
    author_type: "human",
    status: "published",
    prompt: "How would you explain runway risk to a founder?",
    context: "The founder wants a concise explanation that still feels practical.",
    payload: {
      question_type: "short_answer",
      prompt: "How would you explain runway risk to a founder?",
      context: "The founder wants a concise explanation that still feels practical.",
      max_duration_seconds: 90,
      response_guidance: ["Define runway plainly.", "Quantify the risk.", "Close with a next step."],
    },
    version: 1,
  },
  rubric: {
    scoring_style: "rubric",
    criteria: [
      {
        name: "Clarity",
        description: "Explains the concept plainly.",
        weight: 0.5,
        min_score: 0,
        max_score: 4,
        failure_signals: ["Too vague"],
        strong_response_fragments: ["plainly", "clear"],
      },
      {
        name: "Practicality",
        description: "Adds an actionable next step.",
        weight: 0.5,
        min_score: 0,
        max_score: 4,
        failure_signals: ["No next step"],
        strong_response_fragments: ["next step", "action"],
      },
    ],
    thresholds: [
      { band: "needs_review", min_percentage: 0 },
      { band: "partial", min_percentage: 50 },
      { band: "ready_for_retry", min_percentage: 75 },
      { band: "interview_ready", min_percentage: 90 },
    ],
    review_notes: "Smoke-test fixture for the student flow.",
  },
  expected_answer: {
    answer_text: "Runway is the time until cash runs out.",
    answer_outline: ["Define runway", "Quantify the time left", "Explain the tradeoff"],
    key_points: ["Time until cash runs out", "Use recent burn rate", "Call out action"],
    acceptable_variants: ["cash runway", "months of runway"],
  },
  common_mistakes: [
    {
      mistake_text: "Describes runway vaguely.",
      why_it_is_wrong: "The learner needs a concrete explanation.",
      remediation_hint: "State the time horizon and the decision it affects.",
    },
  ],
};

export const studentQuestion = mapBundleToStudentQuestion(studentBundle);

export const createdSession: PracticeSessionRecord = {
  session_id: studentSessionId,
  user_id: "candidate-1",
  source: "demo",
  status: "created",
  question_queue: [studentQuestionId],
  queued_question_count: 1,
  completed_question_count: 0,
  remaining_question_count: 1,
  current_question_id: studentQuestionId,
  started_at: "2026-04-11T08:00:00.000Z",
  completed_at: null,
  attempts: [],
};

export const startedSession: PracticeSessionRecord = {
  ...createdSession,
  status: "in_progress",
  started_at: "2026-04-11T08:01:00.000Z",
};

export const completedSession: PracticeSessionRecord = {
  ...createdSession,
  status: "completed",
  completed_question_count: 1,
  remaining_question_count: 0,
  completed_at: "2026-04-11T08:03:00.000Z",
  attempts: [
    {
      attempt_id: "attempt-1",
      question_id: studentQuestionId,
      prompt: studentBundle.question.prompt,
      response_type: "free_text",
      status: "scored",
      submitted_at: "2026-04-11T08:02:30.000Z",
      overall_score: 92,
      mastery_band: "interview_ready",
    },
  ],
};

export const submitResult: AttemptSubmitResult = {
  attempt_id: "attempt-1",
  question_id: studentQuestionId,
  session_id: studentSessionId,
  score: {
    overall_score: 92,
    mastery_band: "interview_ready",
    scoring_method: "rubric_manual",
    criterion_scores: [
      {
        criterion_name: "Clarity",
        score: 4,
        max_score: 4,
        notes: "Clear and concise.",
      },
      {
        criterion_name: "Practicality",
        score: 4,
        max_score: 4,
        notes: "Ends with a useful next step.",
      },
    ],
  },
  feedback: {
    strengths: ["Explains the concept plainly.", "Closes with a practical next step."],
    gaps: ["Could quantify the runway more precisely."],
    next_step: "Add one concrete metric to anchor the explanation.",
    remediation_hints: ["Use months of runway.", "Tie the risk to a decision."],
  },
};

export const storedResult: StudentResult = {
  sessionId: studentSessionId,
  attemptId: submitResult.attempt_id,
  question: studentQuestion,
  answer: {
    responseType: "free_text",
    content: studentResponseText,
  } satisfies StudentAnswerDraft,
  score: {
    overallScore: submitResult.score.overall_score,
    masteryBand: submitResult.score.mastery_band,
    scoringMethod: submitResult.score.scoring_method,
    criterionScores: submitResult.score.criterion_scores.map((criterion) => ({
      criterionName: criterion.criterion_name,
      score: criterion.score,
      maxScore: criterion.max_score,
      notes: criterion.notes ?? undefined,
    })),
  },
  feedback: {
    strengths: submitResult.feedback.strengths,
    gaps: submitResult.feedback.gaps,
    nextStep: submitResult.feedback.next_step,
    remediationHints: submitResult.feedback.remediation_hints,
  },
  completedAt: "2026-04-11T08:03:00.000Z",
};
