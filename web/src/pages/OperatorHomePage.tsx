import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listAuthoredQuestions } from "../api/authored";
import { listPracticeSessions } from "../api/practiceSessions";
import type { AuthoredQuestionSummary, PracticeSessionSummary } from "../types/api";
import { OperatorFrame } from "../components/operator/OperatorFrame";
import { OperatorMetricGrid } from "../components/operator/OperatorMetricGrid";
import { QuestionSummaryCard } from "../components/operator/QuestionSummaryCard";
import { SessionTriageList } from "../components/operator/SessionTriageList";
import { Button } from "../components/shared/Button";
import { ErrorPanel } from "../components/shared/ErrorPanel";
import { LoadingBlock } from "../components/shared/LoadingBlock";
import { SectionCard } from "../components/shared/SectionCard";
import { StatusBadge } from "../components/shared/StatusBadge";

export function OperatorHomePage() {
  const [questions, setQuestions] = useState<AuthoredQuestionSummary[]>([]);
  const [sessions, setSessions] = useState<PracticeSessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [nextQuestions, nextSessions] = await Promise.all([
        listAuthoredQuestions(),
        listPracticeSessions({ source: "demo" }),
      ]);
      setQuestions(nextQuestions);
      setSessions(nextSessions);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load operator data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const metrics = [
    {
      label: "Draft questions",
      value: String(questions.filter((item) => item.status === "draft").length),
      caption: "Waiting on review and publish.",
    },
    {
      label: "Reviewed questions",
      value: String(questions.filter((item) => item.status === "reviewed").length),
      caption: "Ready for final publication.",
    },
    {
      label: "Published questions",
      value: String(questions.filter((item) => item.status === "published").length),
      caption: "Available for practice sessions.",
    },
    {
      label: "Demo sessions",
      value: String(sessions.length),
      caption: "Loaded from the operator triage slice.",
    },
  ];

  const recentQuestions = [...questions].slice(0, 5);
  const recentSessions = [...sessions].slice(0, 4);

  return (
    <OperatorFrame>
      <div className="workspace">
        <section className="page-hero">
          <div className="kicker-row">
            <StatusBadge tone="soft" label="Operator studio" />
            <span className="inline-metric">Role: academic</span>
            <span className="inline-metric">Guided demo loop</span>
          </div>
          <h1>Run the operator side like a real practice engine.</h1>
          <p>
            This surface keeps the demo focused: create the question, review it, publish it, then watch the
            session state move when a learner uses it. No dashboard clutter. Just the parts that make the
            product feel credible.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" to="/operator/questions/new">
              Create new question
            </Link>
            <Button variant="secondary" onClick={() => void load()}>
              Refresh workspace
            </Button>
          </div>
        </section>

        <OperatorMetricGrid metrics={metrics} />

        {error ? <ErrorPanel message={error} actionLabel="Retry" onAction={() => void load()} /> : null}

        {loading ? <LoadingBlock /> : null}

        {!loading ? (
          <div className="two-column">
            <SectionCard
              eyebrow="Recent authored content"
              title="Questions in the pipeline"
              description="A narrow list that keeps the demo path visible."
              action={
                <Link className="button button-secondary" to="/operator/questions/new">
                  Open composer
                </Link>
              }
            >
              <div className="list">
                {recentQuestions.length > 0 ? (
                  recentQuestions.map((question) => (
                    <QuestionSummaryCard key={question.id} question={question} />
                  ))
                ) : (
                  <p className="muted">No authored questions loaded yet.</p>
                )}
              </div>
            </SectionCard>

            <SectionCard
              eyebrow="Demo session triage"
              title="Sessions that matter right now"
              description="Only the sessions with enough signal to support the story."
            >
              <SessionTriageList sessions={recentSessions} emptyLabel="No demo sessions found for the source filter." />
            </SectionCard>
          </div>
        ) : null}
      </div>
    </OperatorFrame>
  );
}

