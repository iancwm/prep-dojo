from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "student"
    ACADEMIC = "academic"
    CAREER = "career"
    ADMIN = "admin"


class ContentStatus(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DifficultyLevel(StrEnum):
    FOUNDATIONAL = "foundational"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class AssessmentModeType(StrEnum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    ORAL_RECALL = "oral_recall"
    CASE_PROMPT = "case_prompt"
    MODELING_EXERCISE = "modeling_exercise"


class ScoringStyle(StrEnum):
    AUTOMATIC = "automatic"
    RUBRIC = "rubric"
    MANUAL = "manual"
    HYBRID = "hybrid"


class TimingStyle(StrEnum):
    UNTIMED = "untimed"
    TIMED = "timed"
    LIVE = "live"


class AuthorType(StrEnum):
    HUMAN = "human"
    LLM = "llm"
    ASSISTED = "assisted"


class AttemptStatus(StrEnum):
    CREATED = "created"
    SUBMITTED = "submitted"
    SCORED = "scored"
    NEEDS_FOLLOWUP = "needs_followup"
    COMPLETE = "complete"


class ProgressStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    WEAK = "weak"
    STRONG = "strong"
    MASTERED = "mastered"


class MasteryBand(StrEnum):
    NEEDS_REVIEW = "needs_review"
    PARTIAL = "partial"
    READY_FOR_RETRY = "ready_for_retry"
    INTERVIEW_READY = "interview_ready"


class ScoringMethod(StrEnum):
    RUBRIC_MANUAL = "rubric_manual"
    RUBRIC_AI = "rubric_ai"
    HYBRID = "hybrid"

