import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createAuthoredQuestion } from "../api/authored";
import { fallbackAssessmentModes, listAssessmentModes } from "../api/reference";
import type {
  AssessmentModeDefinition,
  AuthoredQuestionBundleCreate,
  QuestionComposerDraft,
} from "../types/api";
import { buildComposerSeed, prettyDateTime } from "../utils/demo";
import { OperatorFrame } from "../components/operator/OperatorFrame";
import { QuestionComposerForm } from "../components/operator/QuestionComposerForm";
import { Button } from "../components/shared/Button";
import { ErrorPanel } from "../components/shared/ErrorPanel";
import { SectionCard } from "../components/shared/SectionCard";

export function QuestionComposerPage() {
  const navigate = useNavigate();
  const [draft, setDraft] = useState<QuestionComposerDraft>(() => buildComposerSeed());
  const [modes, setModes] = useState<AssessmentModeDefinition[]>(fallbackAssessmentModes);
  const [loadingModes, setLoadingModes] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [modeError, setModeError] = useState<string | null>(null);

  const loadModes = async () => {
    setLoadingModes(true);
    setModeError(null);
    try {
      const nextModes = await listAssessmentModes();
      setModes(nextModes);
    } catch (cause) {
      setModes(fallbackAssessmentModes);
      setModeError(
        cause instanceof Error
          ? `Backend mode definitions were unavailable, using built-in defaults. ${cause.message}`
          : "Backend mode definitions were unavailable, using built-in defaults."
      );
    } finally {
      setLoadingModes(false);
    }
  };

  useEffect(() => {
    let alive = true;
    const load = async () => {
      setLoadingModes(true);
      try {
        const nextModes = await listAssessmentModes();
        if (alive) {
          setModes(nextModes);
          setModeError(null);
        }
      } catch (cause) {
        if (alive) {
          setModes(fallbackAssessmentModes);
          setModeError(
            cause instanceof Error
              ? `Backend mode definitions were unavailable, using built-in defaults. ${cause.message}`
              : "Backend mode definitions were unavailable, using built-in defaults."
          );
        }
      } finally {
        if (alive) {
          setLoadingModes(false);
        }
      }
    };

    void load();
    return () => {
      alive = false;
    };
  }, []);

  const submit = async () => {
    setSubmitting(true);
    setSubmitError(null);
    try {
      const created = await createAuthoredQuestion(draft as AuthoredQuestionBundleCreate);
      navigate(`/operator/questions/${created.question.id}/review`);
    } catch (cause) {
      setSubmitError(cause instanceof Error ? cause.message : "Unable to create authored question.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <OperatorFrame>
      <div className="workspace">
        <section className="page-hero">
          <div className="eyebrow">Question composer</div>
          <h1>Author one believable question that carries the whole demo.</h1>
          <p>
            Keep the shape tight. The point is to create content that feels rigorous enough for operator review
            and vivid enough for the practice story that follows.
          </p>
          <div className="page-actions">
            <Button type="button" variant="secondary" onClick={() => setDraft(buildComposerSeed())}>
              Reset to demo seed
            </Button>
          </div>
        </section>

        {submitError ? <ErrorPanel message={submitError} actionLabel="Try again" onAction={submit} /> : null}

        <div className="grid-2">
          <QuestionComposerForm value={draft} onChange={setDraft} onSubmit={submit} submitting={submitting} />

          <div className="preview-panel">
            <SectionCard eyebrow="Mode notes" title="Assessment modes available">
              <div className="mini-list">
                {loadingModes ? (
                  <div className="mini-list-item">
                    <div>
                      <strong>Loading from backend</strong>
                      <span>Refreshing the latest assessment-mode metadata.</span>
                    </div>
                  </div>
                ) : null}

                {modeError ? (
                  <div className="mini-list-item">
                    <div>
                      <strong>Using built-in defaults</strong>
                      <span>{modeError}</span>
                    </div>
                    <Button type="button" variant="ghost" onClick={() => void loadModes()}>
                      Retry
                    </Button>
                  </div>
                ) : null}

                {modes.length > 0 ? (
                  modes.map((mode) => (
                    <div key={mode.mode} className="mini-list-item">
                      <div>
                        <strong>{mode.mode}</strong>
                        <span>{mode.description}</span>
                      </div>
                    </div>
                  ))
                ) : !loadingModes ? (
                  <div className="mini-list-item">
                    <div>
                      <strong>No modes available</strong>
                      <span>The composer can still use the inline mode selector once mode definitions are loaded.</span>
                    </div>
                  </div>
                ) : null}
              </div>
            </SectionCard>

            <SectionCard eyebrow="Live preview" title="What the operator will publish">
              <div className="stack-16">
                <div className="quote-box stack-8">
                  <div className="code-line">
                    {draft.topic.slug} / {draft.concept.slug}
                  </div>
                  <strong style={{ fontFamily: "var(--font-display)", fontSize: "1.2rem" }}>
                    {draft.question.prompt}
                  </strong>
                  <p className="muted">{draft.question.context}</p>
                </div>
                <div className="stack-8">
                  <strong>Rubric</strong>
                  <p className="muted">
                    {draft.rubric.criteria.length} criteria, {draft.rubric.thresholds.length} thresholds, review notes:
                    {draft.rubric.review_notes ? ` ${draft.rubric.review_notes}` : " not set"}
                  </p>
                </div>
                <div className="stack-8">
                  <strong>Expected answer</strong>
                  <p className="muted">
                    {draft.expected_answer.key_points.length} key points and {draft.common_mistakes.length} coaching
                    moments.
                  </p>
                </div>
                <div className="inline-metric">Seeded at {prettyDateTime(new Date().toISOString())}</div>
              </div>
            </SectionCard>
          </div>
        </div>
      </div>
    </OperatorFrame>
  );
}
