export type ContentStatus = "draft" | "reviewed" | "published" | "archived";

export type DifficultyLevel = "foundational" | "intermediate" | "advanced";

export type AssessmentModeType =
  | "multiple_choice"
  | "short_answer"
  | "oral_recall"
  | "case_prompt"
  | "modeling_exercise";

export type ScoringStyle = "automatic" | "rubric" | "manual" | "hybrid";

export type TimingStyle = "untimed" | "timed" | "live";

export type MasteryBand = "needs_review" | "partial" | "ready_for_retry" | "interview_ready";

export type AttemptStatus = "created" | "submitted" | "scored" | "needs_followup" | "complete";

export type ScoringMethod = "automatic" | "rubric_manual" | "rubric_ai" | "hybrid";

export interface TopicCreate {
  slug: string;
  title: string;
  description: string;
  order_index: number;
  status: ContentStatus;
}

export interface TopicRecord extends TopicCreate {
  id: string;
}

export interface TopicUpdate {
  title: string;
  description: string;
  order_index: number;
  status: ContentStatus;
}

export interface ConceptCreate {
  topic_slug: string;
  slug?: string | null;
  title: string;
  definition: string;
  difficulty: DifficultyLevel;
  prerequisites: string[];
  status: ContentStatus;
}

export interface ConceptRecord {
  id: string;
  topic_slug: string;
  slug: string;
  title: string;
  definition: string;
  difficulty: DifficultyLevel;
  prerequisites: string[];
  status: ContentStatus;
}

export interface ConceptUpdate {
  topic_slug: string;
  title: string;
  definition: string;
  difficulty: DifficultyLevel;
  prerequisites: string[];
  status: ContentStatus;
}

export interface AssessmentModeDefinition {
  mode: AssessmentModeType;
  description: string;
  scoring_style: ScoringStyle;
  timing_style: TimingStyle;
}

export interface RubricCriterion {
  name: string;
  description: string;
  weight: number;
  min_score: number;
  max_score: number;
  failure_signals: string[];
  strong_response_fragments: string[];
}

export interface MasteryThreshold {
  band: MasteryBand;
  min_percentage: number;
}

export interface RubricDefinition {
  criteria: RubricCriterion[];
  scoring_style: ScoringStyle;
  thresholds: MasteryThreshold[];
  review_notes?: string | null;
}

export interface MCQOption {
  id: string;
  label: string;
  rationale?: string | null;
}

export interface MCQSinglePayload {
  question_type: "mcq_single";
  prompt: string;
  options: MCQOption[];
  correct_option_id: string;
  explanation: string;
}

export interface ShortAnswerPayload {
  question_type: "short_answer";
  prompt: string;
  context?: string | null;
  max_duration_seconds?: number | null;
  response_guidance: string[];
}

export interface OralRecallPayload {
  question_type: "oral_recall";
  prompt: string;
  cue?: string | null;
  target_duration_seconds?: number | null;
}

export type QuestionPayload = MCQSinglePayload | ShortAnswerPayload | OralRecallPayload;

export interface QuestionCreate {
  concept_slug: string;
  external_id?: string | null;
  assessment_mode: AssessmentModeType;
  difficulty: DifficultyLevel;
  author_type: "human" | "llm" | "assisted";
  status: ContentStatus;
  prompt: string;
  context?: string | null;
  payload: QuestionPayload;
}

export interface QuestionRecord {
  id: string;
  concept_slug: string;
  external_id?: string | null;
  assessment_mode: AssessmentModeType;
  difficulty: DifficultyLevel;
  author_type: "human" | "llm" | "assisted";
  status: ContentStatus;
  prompt: string;
  context?: string | null;
  payload: QuestionPayload;
  version: number;
}

export interface ExpectedAnswerCreate {
  answer_text: string;
  answer_outline: string[];
  key_points: string[];
  acceptable_variants: string[];
}

export interface CommonMistakeCreate {
  mistake_text: string;
  why_it_is_wrong: string;
  remediation_hint: string;
}

export interface AuthoredQuestionBundleCreate {
  topic: TopicCreate;
  concept: ConceptCreate;
  question: QuestionCreate;
  rubric: RubricDefinition;
  expected_answer: ExpectedAnswerCreate;
  common_mistakes: CommonMistakeCreate[];
}

export interface AuthoredQuestionBundleRecord {
  topic: TopicRecord;
  concept: ConceptRecord;
  assessment_mode: AssessmentModeDefinition;
  question: QuestionRecord;
  rubric: RubricDefinition;
  expected_answer: ExpectedAnswerCreate;
  common_mistakes: CommonMistakeCreate[];
}

export interface ContentStatusTransitionRequest {
  status: ContentStatus;
  review_notes?: string | null;
}

export interface ContentStatusTransitionResult {
  question_id: string;
  previous_status: ContentStatus;
  current_status: ContentStatus;
  review_notes?: string | null;
}

export interface AuthoredQuestionSummary {
  id: string;
  topic_slug: string;
  concept_slug: string;
  assessment_mode: AssessmentModeType;
  difficulty: DifficultyLevel;
  status: ContentStatus;
  prompt: string;
  version: number;
}

export interface PracticeSessionCreate {
  session_id?: string | null;
  source: string;
  question_queue: string[];
}

export type PracticeSessionStatus = "created" | "in_progress" | "completed";

export interface PracticeSessionListFilters {
  status?: PracticeSessionStatus | null;
  source?: string | null;
  started_after?: string | null;
  started_before?: string | null;
  current_question_id?: string | null;
  has_remaining?: boolean | null;
}

export interface PracticeSessionSummary {
  session_id: string;
  source: string;
  status: PracticeSessionStatus;
  question_queue: string[];
  queued_question_count: number;
  completed_question_count: number;
  remaining_question_count: number;
  current_question_id: string | null;
  started_at: string;
  completed_at: string | null;
  attempt_count: number;
}

export interface PracticeSessionAttemptSummary {
  attempt_id: string;
  question_id: string;
  prompt: string;
  response_type: string;
  status: string;
  submitted_at: string;
  overall_score: number | null;
  mastery_band: MasteryBand | null;
}

export interface PracticeSessionRecord {
  session_id: string;
  user_id: string;
  source: string;
  status: PracticeSessionStatus;
  question_queue: string[];
  queued_question_count: number;
  completed_question_count: number;
  remaining_question_count: number;
  current_question_id: string | null;
  started_at: string;
  completed_at: string | null;
  attempts: PracticeSessionAttemptSummary[];
}

export interface QuestionComposerDraft extends AuthoredQuestionBundleCreate {}

export interface MultipleChoiceResponse {
  response_type: "multiple_choice";
  selected_option_id: string;
}

export interface FreeTextResponse {
  response_type: "free_text";
  content: string;
}

export interface OralTranscriptResponse {
  response_type: "oral_transcript";
  transcript: string;
  duration_seconds?: number | null;
}

export type AttemptResponse = MultipleChoiceResponse | FreeTextResponse | OralTranscriptResponse;

export interface CriterionScore {
  criterion_name: string;
  score: number;
  max_score: number;
  notes?: string | null;
}

export interface ScoreResult {
  overall_score: number;
  mastery_band: MasteryBand;
  scoring_method: ScoringMethod;
  criterion_scores: CriterionScore[];
}

export interface FeedbackResult {
  strengths: string[];
  gaps: string[];
  next_step: string;
  remediation_hints: string[];
}

export interface StudentAttemptCreate {
  question_id: string;
  session_id: string;
  response: AttemptResponse;
  status?: AttemptStatus;
}

export interface AttemptSubmitResult {
  attempt_id: string;
  question_id: string;
  session_id: string;
  score: ScoreResult;
  feedback: FeedbackResult;
}
