import type {
  AuthoredQuestionBundleCreate,
  QuestionComposerDraft,
  PracticeSessionCreate,
  AssessmentModeType,
  QuestionPayload,
} from "../types/api";

export function slugify(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/-{2,}/g, "-");
}

export function prettyDateTime(value: string | null | undefined): string {
  if (!value) {
    return "Not yet";
  }

  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) {
    return value;
  }

  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function prettyPercent(value: number): string {
  return `${value.toFixed(0)}%`;
}

export function uniqueSuffix(): string {
  return Math.random().toString(36).slice(2, 7);
}

export function splitLines(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function joinLines(values: string[]): string {
  return values.join("\n");
}

export function buildComposerSeed(): QuestionComposerDraft {
  const suffix = uniqueSuffix();
  return {
    topic: {
      slug: `valuation-${suffix}`,
      title: "Valuation Interview Practice",
      description: "A focused topic for enterprise value and equity value recall.",
      order_index: 10,
      status: "draft",
    },
    concept: {
      topic_slug: `valuation-${suffix}`,
      slug: `enterprise-value-${suffix}`,
      title: "Enterprise Value vs Equity Value",
      definition: "Explain how enterprise value bridges to equity value and why the distinction matters.",
      difficulty: "intermediate",
      prerequisites: ["basic-financial-statements", "net-debt-basics"],
      status: "draft",
    },
    question: {
      concept_slug: `enterprise-value-${suffix}`,
      external_id: null,
      assessment_mode: "short_answer",
      difficulty: "intermediate",
      author_type: "human",
      status: "draft",
      prompt:
        "Walk me through the difference between enterprise value and equity value. What adjustments bridge the two, and why does that matter in a live interview?",
      context:
        "Use a crisp interview-style answer that shows definitions, intuition, and one practical example.",
      payload: {
        question_type: "short_answer",
        prompt:
          "Walk me through the difference between enterprise value and equity value. What adjustments bridge the two, and why does that matter in a live interview?",
        context:
          "Use a crisp interview-style answer that shows definitions, intuition, and one practical example.",
        max_duration_seconds: 90,
        response_guidance: [
          "Define enterprise value and equity value cleanly.",
          "Mention why debt, cash, and minority interest change the bridge.",
          "Close with the interview implication: valuation and deal context.",
        ],
      },
    },
    rubric: {
      scoring_style: "rubric",
      criteria: [
        {
          name: "Definition clarity",
          description: "States the two concepts accurately and distinguishes them early.",
          weight: 1,
          min_score: 0,
          max_score: 2,
          failure_signals: ["Confuses EV with market cap", "Jumps to examples without definitions"],
          strong_response_fragments: ["enterprise value", "equity value", "market capitalization"],
        },
        {
          name: "Bridge mechanics",
          description: "Explains the adjustments that move between EV and equity value.",
          weight: 1,
          min_score: 0,
          max_score: 2,
          failure_signals: ["Forgets debt or cash", "Omits why the bridge exists"],
          strong_response_fragments: ["net debt", "cash and debt", "minority interest"],
        },
        {
          name: "Interview relevance",
          description: "Connects the concept to how a candidate would use it in practice.",
          weight: 1,
          min_score: 0,
          max_score: 2,
          failure_signals: ["Stays abstract", "Does not tie back to real valuation work"],
          strong_response_fragments: ["in an interview", "deal context", "valuation use case"],
        },
      ],
      thresholds: [
        { band: "needs_review", min_percentage: 0 },
        { band: "partial", min_percentage: 55 },
        { band: "ready_for_retry", min_percentage: 75 },
        { band: "interview_ready", min_percentage: 90 },
      ],
      review_notes: "Starter rubric for a pilot demo. Tighten wording before a live cohort.",
    },
    expected_answer: {
      answer_text:
        "Enterprise value is the value of the entire operating business, while equity value is the value of the shareholders' stake. The bridge usually starts with market capitalization and then adjusts for net debt, minority interest, and other claims so that the interviewer can compare the company's operating value to the value of the stock.",
      answer_outline: [
        "Define enterprise value and equity value.",
        "Describe the bridge from market cap to enterprise value.",
        "Name the common adjustments: debt, cash, and other claims.",
      ],
      key_points: [
        "EV captures the whole operating business.",
        "Equity value is what belongs to shareholders.",
        "Net debt is the most common bridge adjustment.",
      ],
      acceptable_variants: [
        "Enterprise value looks at the entire firm, equity value looks at the owners' share.",
        "In interview language, EV is the operating value and equity value is the stock value.",
      ],
    },
    common_mistakes: [
      {
        mistake_text: "Treating enterprise value and market capitalization as the same thing.",
        why_it_is_wrong: "It skips the bridge and misses the debt and cash adjustments.",
        remediation_hint: "Call out the bridge explicitly before giving an example.",
      },
      {
        mistake_text: "Listing adjustments without explaining why they matter.",
        why_it_is_wrong: "The answer sounds memorized instead of interview-ready.",
        remediation_hint: "Tie each adjustment back to operating value versus ownership value.",
      },
    ],
  };
}

export function createPayloadForMode(
  mode: AssessmentModeType,
  prompt: string,
  context: string
): QuestionPayload {
  if (mode === "multiple_choice") {
    return {
      question_type: "mcq_single",
      prompt,
      options: [
        { id: "a", label: "Enterprise value", rationale: "Includes debt and cash adjustments." },
        { id: "b", label: "Equity value", rationale: "Ignores the operating claims on the business." },
        { id: "c", label: "Market capitalization", rationale: "Only captures the share price times shares outstanding." },
      ],
      correct_option_id: "a",
      explanation: "Enterprise value is the full operating value before claims are distributed to equity holders.",
    };
  }

  if (mode === "oral_recall") {
    return {
      question_type: "oral_recall",
      prompt,
      cue: context,
      target_duration_seconds: 75,
    };
  }

  return {
    question_type: "short_answer",
    prompt,
    context,
    max_duration_seconds: 90,
    response_guidance: [
      "Define both terms cleanly.",
      "Explain the bridge from equity value to enterprise value.",
      "Tie the answer to interview usefulness.",
    ],
  };
}

export function buildDemoSessionCreate(questionId: string): PracticeSessionCreate {
  return {
    source: "demo",
    question_queue: [questionId],
  };
}

export function describeStatus(status: string): string {
  return status
    .split("_")
    .map((item) => item.charAt(0).toUpperCase() + item.slice(1))
    .join(" ");
}
