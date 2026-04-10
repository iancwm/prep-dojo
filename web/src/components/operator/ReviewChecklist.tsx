import type { AuthoredQuestionBundleRecord } from "../../types/api";
import { StatusBadge } from "../shared/StatusBadge";

interface ReviewChecklistProps {
  bundle: AuthoredQuestionBundleRecord;
}

interface ChecklistItem {
  label: string;
  detail: string;
  ok: boolean;
}

function checklistItems(bundle: AuthoredQuestionBundleRecord): ChecklistItem[] {
  const criteria = bundle.rubric.criteria ?? [];
  const thresholds = bundle.rubric.thresholds ?? [];
  const question = bundle.question;

  return [
    {
      label: "Topic and concept ready",
      detail: `${bundle.topic.slug} / ${bundle.concept.slug}`,
      ok: Boolean(bundle.topic.title && bundle.concept.title),
    },
    {
      label: "Question prompt wired",
      detail: question.prompt,
      ok: question.prompt.trim().length > 0 && question.payload.prompt === question.prompt,
    },
    {
      label: "Rubric coverage",
      detail: `${criteria.length} criteria, ${thresholds.length} thresholds`,
      ok: criteria.length >= 2 && thresholds.length >= 3,
    },
    {
      label: "Threshold floor",
      detail: thresholds.length ? `Starts at ${thresholds[0].min_percentage}%` : "No thresholds",
      ok: thresholds.length > 0 && thresholds[0].min_percentage === 0,
    },
    {
      label: "Expected answer shaped",
      detail: `${bundle.expected_answer.key_points.length} key points`,
      ok: bundle.expected_answer.answer_text.trim().length > 0 && bundle.expected_answer.key_points.length > 0,
    },
    {
      label: "Common mistakes captured",
      detail: `${bundle.common_mistakes.length} coaching reminders`,
      ok: bundle.common_mistakes.length > 0,
    },
  ];
}

export function ReviewChecklist({ bundle }: ReviewChecklistProps) {
  const items = checklistItems(bundle);

  return (
    <div className="stack-12">
      {items.map((item) => (
        <div key={item.label} className="mini-list-item">
          <div>
            <strong>{item.label}</strong>
            <span>{item.detail}</span>
          </div>
          <StatusBadge tone={item.ok ? "published" : "draft"} label={item.ok ? "Ready" : "Needs work"} />
        </div>
      ))}
    </div>
  );
}

