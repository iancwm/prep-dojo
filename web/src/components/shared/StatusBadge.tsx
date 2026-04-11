import type { ContentStatus, MasteryBand, PracticeSessionStatus } from "../../types/api";
import { describeStatus } from "../../utils/demo";

type BadgeTone = ContentStatus | PracticeSessionStatus | MasteryBand | "neutral" | "soft";

interface StatusBadgeProps {
  tone: BadgeTone;
  label?: string;
}

export function StatusBadge({ tone, label }: StatusBadgeProps) {
  const classes = ["badge"];
  const toneClassMap: Record<string, string> = {
    draft: "badge-draft",
    reviewed: "badge-reviewed",
    published: "badge-published",
    archived: "badge-archived",
    created: "badge-created",
    in_progress: "badge-in_progress",
    completed: "badge-completed",
    needs_review: "badge-draft",
    partial: "badge-created",
    ready_for_retry: "badge-reviewed",
    interview_ready: "badge-published",
    neutral: "badge-soft",
    soft: "badge-soft",
  };

  classes.push(toneClassMap[tone] ?? "badge-soft");

  return <span className={classes.join(" ")}>{label ?? describeStatus(tone)}</span>;
}
