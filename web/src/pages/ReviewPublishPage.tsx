import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { createPracticeSession } from "../api/practiceSessions";
import { getAuthoredQuestion, transitionAuthoredQuestionStatus } from "../api/authored";
import type { AuthoredQuestionBundleRecord } from "../types/api";
import { buildDemoSessionCreate } from "../utils/demo";
import { OperatorFrame } from "../components/operator/OperatorFrame";
import { ReviewChecklist } from "../components/operator/ReviewChecklist";
import { Button } from "../components/shared/Button";
import { ErrorPanel } from "../components/shared/ErrorPanel";
import { LoadingBlock } from "../components/shared/LoadingBlock";
import { SectionCard } from "../components/shared/SectionCard";
import { StatusBadge } from "../components/shared/StatusBadge";

export function ReviewPublishPage() {
  const params = useParams();
  const questionId = params.questionId ?? "";
  const navigate = useNavigate();
  const [bundle, setBundle] = useState<AuthoredQuestionBundleRecord | null>(null);
  const [reviewNotes, setReviewNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [creatingSession, setCreatingSession] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBundle = async () => {
    setLoading(true);
    setError(null);
    try {
      const nextBundle = await getAuthoredQuestion(questionId);
      setBundle(nextBundle);
      setReviewNotes(nextBundle.rubric.review_notes ?? "");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load authored question.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!questionId) {
      setError("Missing question id.");
      setLoading(false);
      return;
    }
    void loadBundle();
  }, [questionId]);

  const moveStatus = async (status: "reviewed" | "published") => {
    if (!bundle) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await transitionAuthoredQuestionStatus(questionId, {
        status,
        review_notes: reviewNotes || null,
      });
      await loadBundle();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to update question status.");
    } finally {
      setSaving(false);
    }
  };

  const createSession = async () => {
    if (!bundle) {
      return;
    }
    setCreatingSession(true);
    setError(null);
    try {
      const session = await createPracticeSession(buildDemoSessionCreate(bundle.question.id));
      navigate(`/operator/sessions/${session.session_id}`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to create demo session.");
    } finally {
      setCreatingSession(false);
    }
  };

  return (
    <OperatorFrame>
      <div className="workspace">
        <section className="page-hero">
          <div className="kicker-row">
            <StatusBadge tone={bundle?.question.status ?? "draft"} />
            <span className="inline-metric">Review and publish</span>
            <span className="inline-metric">Question {questionId.slice(0, 8)}</span>
          </div>
          <h1>Quality-control the content before it becomes part of the demo loop.</h1>
          <p>
            This is the operator checkpoint: verify the rubric, confirm the expected answer, and move the
            question through the review states with real backend state changes.
          </p>
          <div className="page-actions">
            <Link className="button button-secondary" to="/operator/questions/new">
              Create another question
            </Link>
            {bundle?.question.status === "published" ? (
              <Button type="button" onClick={createSession} disabled={creatingSession}>
                {creatingSession ? "Creating demo session..." : "Create demo session"}
              </Button>
            ) : null}
          </div>
        </section>

        {error ? <ErrorPanel message={error} actionLabel="Reload" onAction={() => void loadBundle()} /> : null}

        {loading ? <LoadingBlock /> : null}

        {bundle ? (
          <div className="two-column">
            <div className="section-stack">
              <SectionCard
                eyebrow="Question summary"
                title={`${bundle.concept.title} in ${bundle.topic.title}`}
                description={bundle.question.prompt}
              >
                <div className="stack-16">
                  <div className="kicker-row">
                    <StatusBadge tone={bundle.question.status} />
                    <StatusBadge tone="soft" label={bundle.question.assessment_mode} />
                    <span className="inline-metric">{bundle.question.difficulty}</span>
                    <span className="inline-metric">v{bundle.question.version}</span>
                  </div>
                  <p>{bundle.question.context}</p>
                  <div className="inline-grid">
                    <div className="quote-box">
                      <strong>Expected answer</strong>
                      <p className="muted">{bundle.expected_answer.answer_text}</p>
                    </div>
                    <div className="quote-box">
                      <strong>Review notes</strong>
                      <textarea
                        className="field-textarea"
                        value={reviewNotes}
                        onChange={(event) => setReviewNotes(event.target.value)}
                        placeholder="Add the operator quality note here."
                      />
                    </div>
                  </div>
                </div>
              </SectionCard>

              <SectionCard eyebrow="Rubric" title="Checks the operator can trust">
                <div className="stack-12">
                  {bundle.rubric.criteria.map((criterion) => (
                    <div key={criterion.name} className="mini-list-item">
                      <div>
                        <strong>{criterion.name}</strong>
                        <span>{criterion.description}</span>
                      </div>
                      <span className="inline-metric">
                        {criterion.min_score}-{criterion.max_score}
                      </span>
                    </div>
                  ))}
                </div>
              </SectionCard>
            </div>

            <div className="section-stack">
              <SectionCard eyebrow="Review checklist" title="Ready-to-publish guardrails">
                <ReviewChecklist bundle={bundle} />
              </SectionCard>

              <SectionCard eyebrow="Publish panel" title="Move the content forward">
                <div className="stack-16">
                  <p className="muted">
                    Use the review transition to lock in the operator's quality pass, then publish when the content
                    is ready for learners.
                  </p>
                  <div className="page-actions">
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => void moveStatus("reviewed")}
                      disabled={saving || bundle.question.status !== "draft"}
                    >
                      {saving ? "Updating..." : "Mark reviewed"}
                    </Button>
                    <Button
                      type="button"
                      onClick={() => void moveStatus("published")}
                      disabled={saving || bundle.question.status !== "reviewed"}
                    >
                      {saving ? "Updating..." : "Publish question"}
                    </Button>
                  </div>
                  {bundle.question.status === "published" ? (
                    <div className="quote-box stack-8">
                      <strong>Published and ready</strong>
                      <p className="muted">
                        The demo can now create a practice session from this question and move the loop into triage.
                      </p>
                    </div>
                  ) : null}
                </div>
              </SectionCard>
            </div>
          </div>
        ) : null}
      </div>
    </OperatorFrame>
  );
}

