import type { MasteryBand, ScoreResult } from "./api";

export type SessionStatus = "created" | "in_progress" | "completed";

export type StudentResponseType = "free_text" | "multiple_choice" | "oral_transcript";

export type StudentAssessmentMode =
  | "multiple_choice"
  | "short_answer"
  | "oral_recall"
  | "case_prompt"
  | "modeling_exercise";

export interface StudentQuestionOption {
  id: string;
  label: string;
  rationale?: string;
}

export interface StudentQuestion {
  id: string;
  title: string;
  prompt: string;
  context?: string;
  assessmentMode: StudentAssessmentMode;
  responseType: StudentResponseType;
  cue?: string;
  options?: StudentQuestionOption[];
  responseGuidance?: string[];
  targetDurationSeconds?: number;
}

export interface StudentAttemptSummary {
  attemptId: string;
  questionId: string;
  prompt: string;
  responseType: StudentResponseType;
  submittedAt: string;
  overallScore: number;
  masteryBand: MasteryBand;
}

export interface StudentCriterionScore {
  criterionName: string;
  score: number;
  maxScore: number;
  notes?: string | null;
}

export interface StudentAnswerDraft {
  responseType: StudentResponseType;
  selectedOptionId?: string;
  content?: string;
  transcript?: string;
  durationSeconds?: number;
}

export interface StudentSession {
  sessionId: string;
  source: string;
  title: string;
  subtitle: string;
  status: SessionStatus;
  questionQueue: StudentQuestion[];
  currentQuestionId: string | null;
  startedAt: string | null;
  completedAt: string | null;
  attempts: StudentAttemptSummary[];
  learnerLabel: string;
}

export interface StudentResult {
  sessionId: string;
  attemptId: string;
  question: StudentQuestion;
  answer: StudentAnswerDraft;
  score: {
    overallScore: ScoreResult["overall_score"];
    masteryBand: ScoreResult["mastery_band"];
    scoringMethod: ScoreResult["scoring_method"];
    criterionScores: StudentCriterionScore[];
  };
  feedback: StudentFeedbackResult;
  completedAt: string;
}

export interface StudentFeedbackResult {
  strengths: string[];
  gaps: string[];
  nextStep: string;
  remediationHints: string[];
}
