import { requestJson } from "./client";
import type { AssessmentModeDefinition } from "../types/api";

export const fallbackAssessmentModes: AssessmentModeDefinition[] = [
  {
    mode: "multiple_choice",
    description: "Low-latency factual and applied recall with one correct option.",
    scoring_style: "automatic",
    timing_style: "timed",
  },
  {
    mode: "short_answer",
    description: "Written explanation scored against a rubric.",
    scoring_style: "rubric",
    timing_style: "timed",
  },
  {
    mode: "oral_recall",
    description: "Spoken interview-style recall judged on correctness and clarity.",
    scoring_style: "hybrid",
    timing_style: "live",
  },
  {
    mode: "case_prompt",
    description: "Scenario-based reasoning that tests application under pressure.",
    scoring_style: "rubric",
    timing_style: "timed",
  },
  {
    mode: "modeling_exercise",
    description: "Applied finance task scored on output and reasoning.",
    scoring_style: "manual",
    timing_style: "live",
  },
];

export function listAssessmentModes(): Promise<AssessmentModeDefinition[]> {
  return requestJson<AssessmentModeDefinition[]>(
    "/api/v1/reference/assessment-modes",
    {},
    { requestLabel: "Loading assessment mode definitions" }
  );
}
