import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { completePracticeSession, getPracticeSession, startPracticeSession } from "../api/practiceSessions";
import type { PracticeSessionRecord } from "../types/api";
import { prettyDateTime } from "../utils/demo";
import { OperatorFrame } from "../components/operator/OperatorFrame";
import { Button } from "../components/shared/Button";
import { ErrorPanel } from "../components/shared/ErrorPanel";
import { LoadingBlock } from "../components/shared/LoadingBlock";
import { SectionCard } from "../components/shared/SectionCard";
import { StatusBadge } from "../components/shared/StatusBadge";

export function OperatorSessionDetailPage() {
  const params = useParams();
  const sessionId = params.sessionId ?? "";
  const [session, setSession] = useState<PracticeSessionRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSession = async () => {
    setLoading(true);
    setError(null);
    try {
      const nextSession = await getPracticeSession(sessionId);
      setSession(nextSession);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load session.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!sessionId) {
      setError("Missing session id.");
      setLoading(false);
      return;
    }
    void loadSession();
  }, [sessionId]);

  const start = async () => {
    setBusy(true);
    setError(null);
    try {
      const nextSession = await startPracticeSession(sessionId);
      setSession(nextSession);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to start the session.");
    } finally {
      setBusy(false);
    }
  };

  const complete = async () => {
    setBusy(true);
    setError(null);
    try {
      const nextSession = await completePracticeSession(sessionId);
      setSession(nextSession);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to complete the session.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <OperatorFrame>
      <div className="workspace">
        <section className="page-hero">
          <div className="kicker-row">
            <StatusBadge tone={session?.status ?? "created"} />
            <span className="inline-metric">Session triage</span>
            <span className="inline-metric">{sessionId.slice(0, 8)}</span>
          </div>
          <h1>See the session as the system sees it.</h1>
          <p>
            This page keeps the operational view narrow: status, queue, attempts, and the few controls an operator
            needs to prove the loop is real.
          </p>
          <div className="page-actions">
            <Link className="button button-secondary" to="/operator">
              Back to operator home
            </Link>
            <Link className="button button-secondary" to={`/practice/${sessionId}`}>
              Open learner view
            </Link>
            <Button type="button" variant="secondary" onClick={() => void loadSession()}>
              Refresh session
            </Button>
          </div>
        </section>

        {error ? <ErrorPanel message={error} actionLabel="Retry" onAction={() => void loadSession()} /> : null}

        {loading ? <LoadingBlock /> : null}

        {session ? (
          <div className="two-column">
            <div className="section-stack">
              <SectionCard eyebrow="Session summary" title={session.session_id}>
                <div className="metric-grid" style={{ gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
                  <div className="metric-card">
                    <strong>{session.status}</strong>
                    <span>Status</span>
                    <small className="muted">Lifecycle state from the backend.</small>
                  </div>
                  <div className="metric-card">
                    <strong>{session.remaining_question_count}</strong>
                    <span>Remaining</span>
                    <small className="muted">Questions left in the queue.</small>
                  </div>
                  <div className="metric-card">
                    <strong>{session.attempts.length}</strong>
                    <span>Attempts</span>
                    <small className="muted">Captured responses for this session.</small>
                  </div>
                </div>
                <div className="kicker-row">
                  <span className="inline-metric">Source: {session.source}</span>
                  <span className="inline-metric">Started: {prettyDateTime(session.started_at)}</span>
                  <span className="inline-metric">Completed: {prettyDateTime(session.completed_at)}</span>
                </div>
              </SectionCard>

              <SectionCard eyebrow="Attempt feed" title="What happened in the session">
                <div className="stack-12">
                  {session.attempts.length > 0 ? (
                    session.attempts.map((attempt) => (
                      <div key={attempt.attempt_id} className="mini-list-item">
                        <div>
                          <strong>{attempt.prompt}</strong>
                          <span>
                            {attempt.response_type} / {prettyDateTime(attempt.submitted_at)}
                          </span>
                        </div>
                        <div className="stack-8" style={{ alignItems: "flex-end" }}>
                          <StatusBadge tone={attempt.mastery_band ?? "soft"} label={attempt.mastery_band ?? "pending"} />
                          <span className="inline-metric">
                            {attempt.overall_score ?? 0}
                          </span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="quote-box stack-8">
                      <strong>No attempts yet</strong>
                      <p className="muted">
                        The session is created, but no learner submission has been captured yet.
                      </p>
                    </div>
                  )}
                </div>
              </SectionCard>
            </div>

            <div className="section-stack">
              <SectionCard eyebrow="Queue" title="Questions waiting inside the session">
                <div className="mini-list">
                  {session.question_queue.length > 0 ? (
                    session.question_queue.map((questionId) => (
                      <div key={questionId} className="mini-list-item">
                        <div>
                          <strong>{questionId}</strong>
                          <span>
                            {session.current_question_id === questionId ? "Current question" : "Queued question"}
                          </span>
                        </div>
                        <Link className="button button-secondary" to={`/operator/questions/${questionId}/review`}>
                          Open
                        </Link>
                      </div>
                    ))
                  ) : (
                    <div className="quote-box stack-8">
                      <strong>Empty queue</strong>
                      <p className="muted">This session does not have any queued question ids yet.</p>
                    </div>
                  )}
                </div>
              </SectionCard>

              <SectionCard eyebrow="Triage controls" title="Move the session through its lifecycle">
                <div className="stack-12">
                  <p className="muted">
                    These controls are intentionally small. They show that the operator can confirm the session state
                    without turning this page into a full admin console.
                  </p>
                  <div className="page-actions">
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => void start()}
                      disabled={busy || session.status !== "created"}
                    >
                      {busy ? "Updating..." : "Start session"}
                    </Button>
                    <Button
                      type="button"
                      onClick={() => void complete()}
                      disabled={busy || session.status === "completed" || (session.status === "created" && session.attempts.length === 0)}
                    >
                      {busy ? "Updating..." : "Mark complete"}
                    </Button>
                  </div>
                  <div className="timeline">
                    <div className="timeline-item">
                      <strong>Status</strong>
                      <small>{session.status}</small>
                    </div>
                    <div className="timeline-item">
                      <strong>Queue size</strong>
                      <small>
                        {session.queued_question_count} queued, {session.completed_question_count} completed
                      </small>
                    </div>
                    <div className="timeline-item">
                      <strong>Completion</strong>
                      <small>{session.completed_at ? prettyDateTime(session.completed_at) : "Not yet completed"}</small>
                    </div>
                  </div>
                </div>
              </SectionCard>
            </div>
          </div>
        ) : null}
      </div>
    </OperatorFrame>
  );
}
