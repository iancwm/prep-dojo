import { Link } from "react-router-dom";
import type { PracticeSessionSummary } from "../../types/api";
import { prettyDateTime } from "../../utils/demo";
import { StatusBadge } from "../shared/StatusBadge";

interface SessionSummaryCardProps {
  session: PracticeSessionSummary;
}

export function SessionSummaryCard({ session }: SessionSummaryCardProps) {
  const current = session.current_question_id ?? "Waiting for queue";

  return (
    <div className="list-item">
      <div className="stack-8">
        <div className="kicker-row">
          <StatusBadge tone={session.status} />
          <span className="inline-metric">{session.source}</span>
          <span className="inline-metric">{session.remaining_question_count} remaining</span>
          <span className="inline-metric">{session.attempt_count} attempts</span>
        </div>
        <div className="stack-8">
          <h3>{session.session_id}</h3>
          <p>
            Current question: {current}
            <br />
            Started: {prettyDateTime(session.started_at)}
            {session.completed_at ? <>, completed: {prettyDateTime(session.completed_at)}</> : null}
          </p>
        </div>
      </div>
      <div className="stack-8" style={{ alignItems: "flex-end" }}>
        <Link className="button button-secondary" to={`/operator/sessions/${session.session_id}`}>
          Open
        </Link>
      </div>
    </div>
  );
}

