import { Link } from "react-router-dom";
import type { AuthoredQuestionSummary } from "../../types/api";
import { StatusBadge } from "../shared/StatusBadge";

interface QuestionSummaryCardProps {
  question: AuthoredQuestionSummary;
}

export function QuestionSummaryCard({ question }: QuestionSummaryCardProps) {
  return (
    <div className="list-item">
      <div className="stack-8">
        <div className="kicker-row">
          <StatusBadge tone={question.status} />
          <span className="inline-metric">{question.assessment_mode}</span>
          <span className="inline-metric">{question.difficulty}</span>
          <span className="inline-metric">v{question.version}</span>
        </div>
        <div className="stack-8">
          <h3>{question.prompt}</h3>
          <p>
            {question.topic_slug} / {question.concept_slug}
          </p>
        </div>
      </div>
      <div className="stack-8" style={{ alignItems: "flex-end" }}>
        <span className="muted">Version {question.version}</span>
        <Link className="button button-secondary" to={`/operator/questions/${question.id}/review`}>
          Review
        </Link>
      </div>
    </div>
  );
}
