import type { PracticeSessionSummary } from "../../types/api";
import { SessionSummaryCard } from "./SessionSummaryCard";
import { EmptyState } from "../shared/EmptyState";

interface SessionTriageListProps {
  sessions: PracticeSessionSummary[];
  emptyLabel?: string;
}

export function SessionTriageList({ sessions, emptyLabel = "No demo sessions yet." }: SessionTriageListProps) {
  if (sessions.length === 0) {
    return <EmptyState title="No sessions to triage" description={emptyLabel} />;
  }

  return (
    <div className="list">
      {sessions.map((session) => (
        <SessionSummaryCard key={session.session_id} session={session} />
      ))}
    </div>
  );
}

