import type { ChangeEvent } from "react";
import type {
  AssessmentModeType,
  QuestionComposerDraft,
  QuestionPayload,
  RubricCriterion,
  MasteryThreshold,
  CommonMistakeCreate,
} from "../../types/api";
import { createPayloadForMode, joinLines, slugify, splitLines } from "../../utils/demo";
import { Button } from "../shared/Button";
import { Field } from "../shared/Field";
import { SectionCard } from "../shared/SectionCard";

interface QuestionComposerFormProps {
  value: QuestionComposerDraft;
  onChange: (next: QuestionComposerDraft) => void;
  onSubmit: () => void;
  submitting?: boolean;
}

const assessmentModes: Array<{ value: AssessmentModeType; label: string }> = [
  { value: "short_answer", label: "Short answer" },
  { value: "oral_recall", label: "Oral recall" },
  { value: "multiple_choice", label: "Multiple choice" },
];

const defaultCriterion = (): RubricCriterion => ({
  name: "Clarity",
  description: "Explains the concept with clean interview-ready language.",
  weight: 1,
  min_score: 0,
  max_score: 2,
  failure_signals: [],
  strong_response_fragments: [],
});

const defaultThreshold = (band: MasteryThreshold["band"], min_percentage: number): MasteryThreshold => ({
  band,
  min_percentage,
});

const defaultMistake = (): CommonMistakeCreate => ({
  mistake_text: "Confuses the main concept with a surface-level synonym.",
  why_it_is_wrong: "It misses the operational distinction the interviewer is looking for.",
  remediation_hint: "Anchor the answer around the bridge, not just the definition.",
});

function clonePayloadForMode(mode: AssessmentModeType, prompt: string, context: string): QuestionPayload {
  return createPayloadForMode(mode, prompt, context);
}

export function QuestionComposerForm({
  value,
  onChange,
  onSubmit,
  submitting = false,
}: QuestionComposerFormProps) {
  const update = (patch: Partial<QuestionComposerDraft>) => {
    onChange({ ...value, ...patch });
  };

  const updateTopic = (patch: Partial<QuestionComposerDraft["topic"]>) => {
    update({ topic: { ...value.topic, ...patch } });
  };

  const updateConcept = (patch: Partial<QuestionComposerDraft["concept"]>) => {
    update({ concept: { ...value.concept, ...patch } });
  };

  const updateQuestion = (patch: Partial<QuestionComposerDraft["question"]>) => {
    update({ question: { ...value.question, ...patch } });
  };

  const updateQuestionPayload = (nextPayload: QuestionPayload) => {
    updateQuestion({
      payload: nextPayload,
    });
  };

  const updateRubric = (patch: Partial<QuestionComposerDraft["rubric"]>) => {
    update({ rubric: { ...value.rubric, ...patch } });
  };

  const updateCriterion = (index: number, patch: Partial<RubricCriterion>) => {
    const criteria = value.rubric.criteria.map((criterion, itemIndex) =>
      itemIndex === index ? { ...criterion, ...patch } : criterion
    );
    updateRubric({ criteria });
  };

  const addCriterion = () => {
    updateRubric({ criteria: [...value.rubric.criteria, defaultCriterion()] });
  };

  const removeCriterion = (index: number) => {
    updateRubric({ criteria: value.rubric.criteria.filter((_, itemIndex) => itemIndex !== index) });
  };

  const updateThreshold = (index: number, patch: Partial<MasteryThreshold>) => {
    const thresholds = value.rubric.thresholds.map((threshold, itemIndex) =>
      itemIndex === index ? { ...threshold, ...patch } : threshold
    );
    updateRubric({ thresholds });
  };

  const addThreshold = () => {
    const lastThreshold = value.rubric.thresholds[value.rubric.thresholds.length - 1];
    updateRubric({
      thresholds: [
        ...value.rubric.thresholds,
        defaultThreshold(
          "interview_ready",
          Math.min(100, lastThreshold ? lastThreshold.min_percentage : 90)
        ),
      ],
    });
  };

  const removeThreshold = (index: number) => {
    updateRubric({ thresholds: value.rubric.thresholds.filter((_, itemIndex) => itemIndex !== index) });
  };

  const updateExpectedAnswer = (patch: Partial<QuestionComposerDraft["expected_answer"]>) => {
    update({ expected_answer: { ...value.expected_answer, ...patch } });
  };

  const updateMistake = (index: number, patch: Partial<CommonMistakeCreate>) => {
    const common_mistakes = value.common_mistakes.map((mistake, itemIndex) =>
      itemIndex === index ? { ...mistake, ...patch } : mistake
    );
    update({ common_mistakes });
  };

  const addMistake = () => {
    update({ common_mistakes: [...value.common_mistakes, defaultMistake()] });
  };

  const removeMistake = (index: number) => {
    update({ common_mistakes: value.common_mistakes.filter((_, itemIndex) => itemIndex !== index) });
  };

  const handleModeChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const nextMode = event.target.value as AssessmentModeType;
    const prompt = value.question.prompt || value.question.payload.prompt;
    const context = value.question.context ?? "";
    const payload = clonePayloadForMode(nextMode, prompt, context);
    updateQuestion({
      assessment_mode: nextMode,
      payload,
    });
  };

  const handlePromptChange = (event: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
    const prompt = event.target.value;
    const payload = value.question.payload;
    updateQuestion({
      prompt,
      payload: {
        ...payload,
        prompt,
      },
    });
  };

  const handleContextChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    const context = event.target.value;
    const payload = value.question.payload;
    if (payload.question_type === "short_answer") {
      updateQuestion({
        context,
        payload: {
          ...payload,
          context,
        },
      });
      return;
    }
    updateQuestion({ context });
  };

  const payload = value.question.payload;

  return (
    <div className="form-grid">
      <SectionCard
        eyebrow="Topic + concept"
        title="Shape the operator storyline"
        description="Keep the metadata precise enough for operators to control, but not so wide that the demo loses focus."
      >
        <div className="inline-grid">
          <Field label="Topic slug" hint="Used in routing and list filtering">
            <input
              className="field-input"
              value={value.topic.slug}
              onChange={(event) =>
                onChange({
                  ...value,
                  topic: {
                    ...value.topic,
                    slug: slugify(event.target.value),
                  },
                  concept: {
                    ...value.concept,
                    topic_slug: slugify(event.target.value),
                  },
                })
              }
            />
          </Field>
          <Field label="Topic title">
            <input
              className="field-input"
              value={value.topic.title}
              onChange={(event) => updateTopic({ title: event.target.value })}
            />
          </Field>
        </div>

        <Field label="Topic description">
          <textarea
            className="field-textarea"
            value={value.topic.description}
            onChange={(event) => updateTopic({ description: event.target.value })}
          />
        </Field>

        <div className="inline-grid">
          <Field label="Concept slug" hint="Auto-derived but editable">
            <input
              className="field-input"
              value={value.concept.slug ?? ""}
              onChange={(event) =>
                onChange({
                  ...value,
                  concept: {
                    ...value.concept,
                    slug: slugify(event.target.value),
                  },
                  question: {
                    ...value.question,
                    concept_slug: slugify(event.target.value),
                  },
                })
              }
            />
          </Field>
          <Field label="Concept difficulty">
            <select
              className="field-select"
              value={value.concept.difficulty}
              onChange={(event) => updateConcept({ difficulty: event.target.value as QuestionComposerDraft["concept"]["difficulty"] })}
            >
              <option value="foundational">Foundational</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </Field>
        </div>

        <div className="inline-grid">
          <Field label="Concept title">
            <input
              className="field-input"
              value={value.concept.title}
              onChange={(event) => updateConcept({ title: event.target.value })}
            />
          </Field>
          <Field label="Prerequisites" hint="Comma separated">
            <input
              className="field-input"
              value={value.concept.prerequisites.join(", ")}
              onChange={(event) => updateConcept({ prerequisites: event.target.value.split(",").map((item) => item.trim()).filter(Boolean) })}
            />
          </Field>
        </div>

        <Field label="Concept definition">
          <textarea
            className="field-textarea"
            value={value.concept.definition}
            onChange={(event) => updateConcept({ definition: event.target.value })}
          />
        </Field>
      </SectionCard>

      <SectionCard eyebrow="Question" title="Write the prompt that the demo will carry">
        <div className="inline-grid">
          <Field label="Assessment mode">
            <select className="field-select" value={value.question.assessment_mode} onChange={handleModeChange}>
              {assessmentModes.map((mode) => (
                <option key={mode.value} value={mode.value}>
                  {mode.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Question difficulty">
            <select
              className="field-select"
              value={value.question.difficulty}
              onChange={(event) =>
                updateQuestion({ difficulty: event.target.value as QuestionComposerDraft["question"]["difficulty"] })
              }
            >
              <option value="foundational">Foundational</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </Field>
        </div>

        <Field label="Prompt">
          <textarea className="field-textarea" value={value.question.prompt} onChange={handlePromptChange} />
        </Field>

        <Field label="Context / framing">
          <textarea className="field-textarea" value={value.question.context ?? ""} onChange={handleContextChange} />
        </Field>

        <Field label="Author note">
          <input
            className="field-input"
            value={value.question.external_id ?? ""}
            onChange={(event) => updateQuestion({ external_id: event.target.value || null })}
            placeholder="Optional demo-friendly external id"
          />
        </Field>

        <div className="quote-box stack-8">
          <div className="code-line">Payload type: {payload.question_type}</div>
          {payload.question_type === "short_answer" ? (
            <div className="stack-12">
              <div className="inline-grid">
                <Field label="Max duration seconds">
                  <input
                    className="field-input"
                    type="number"
                    min={15}
                    value={payload.max_duration_seconds ?? 90}
                    onChange={(event) =>
                      updateQuestionPayload({
                        ...payload,
                        max_duration_seconds: Number(event.target.value),
                      })
                    }
                  />
                </Field>
                <Field label="Response guidance">
                  <textarea
                    className="field-textarea"
                    value={joinLines(payload.response_guidance)}
                    onChange={(event) =>
                      updateQuestionPayload({
                        ...payload,
                        response_guidance: splitLines(event.target.value),
                      })
                    }
                  />
                </Field>
              </div>
            </div>
          ) : null}
          {payload.question_type === "oral_recall" ? (
            <div className="inline-grid">
              <Field label="Cue">
                <textarea
                  className="field-textarea"
                  value={payload.cue ?? ""}
                  onChange={(event) =>
                    updateQuestionPayload({
                      ...payload,
                      cue: event.target.value,
                    })
                  }
                />
              </Field>
              <Field label="Target duration seconds">
                <input
                  className="field-input"
                  type="number"
                  min={15}
                  value={payload.target_duration_seconds ?? 75}
                  onChange={(event) =>
                    updateQuestionPayload({
                      ...payload,
                      target_duration_seconds: Number(event.target.value),
                    })
                  }
                />
              </Field>
            </div>
          ) : null}
          {payload.question_type === "mcq_single" ? (
            <div className="stack-16">
              {payload.options.map((option, index) => (
                <div key={option.id} className="surface surface-pad stack-8">
                  <div className="inline-grid">
                    <Field label={`Option ${index + 1} id`}>
                      <input
                        className="field-input"
                        value={option.id}
                      onChange={(event) => {
                        const options = payload.options.map((item, itemIndex) =>
                          itemIndex === index ? { ...item, id: event.target.value } : item
                        );
                        updateQuestionPayload({
                          ...payload,
                          options,
                        });
                      }}
                    />
                  </Field>
                    <Field label="Correct option?">
                    <button
                      type="button"
                      className={`button ${payload.correct_option_id === option.id ? "button-primary" : "button-secondary"}`}
                      onClick={() =>
                        updateQuestionPayload({
                          ...payload,
                          correct_option_id: option.id,
                        })
                      }
                    >
                      {payload.correct_option_id === option.id ? "Chosen" : "Choose"}
                    </button>
                    </Field>
                  </div>
                  <Field label="Label">
                    <input
                      className="field-input"
                      value={option.label}
                      onChange={(event) => {
                        const options = payload.options.map((item, itemIndex) =>
                          itemIndex === index ? { ...item, label: event.target.value } : item
                        );
                        updateQuestionPayload({
                          ...payload,
                          options,
                        });
                      }}
                    />
                  </Field>
                  <Field label="Rationale">
                    <textarea
                      className="field-textarea"
                      value={option.rationale ?? ""}
                      onChange={(event) => {
                        const options = payload.options.map((item, itemIndex) =>
                          itemIndex === index ? { ...item, rationale: event.target.value } : item
                        );
                        updateQuestionPayload({
                          ...payload,
                          options,
                        });
                      }}
                    />
                  </Field>
                </div>
              ))}
              <Field label="Explanation">
                <textarea
                  className="field-textarea"
                  value={payload.explanation}
                  onChange={(event) =>
                    updateQuestionPayload({
                      ...payload,
                      explanation: event.target.value,
                    })
                  }
                />
              </Field>
            </div>
          ) : null}
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Rubric"
        title="Make the review loop feel credible"
        description="The rubric should read like real operator quality control, not a hidden scoring blob."
        action={<Button type="button" variant="secondary" onClick={addCriterion}>Add criterion</Button>}
      >
        <div className="stack-16">
          <Field label="Rubric review notes">
            <textarea
              className="field-textarea"
              value={value.rubric.review_notes ?? ""}
              onChange={(event) => updateRubric({ review_notes: event.target.value })}
            />
          </Field>

          <div className="stack-12">
            {value.rubric.criteria.map((criterion, index) => (
              <div key={`${criterion.name}-${index}`} className="surface surface-pad stack-12">
                <div className="page-actions" style={{ justifyContent: "space-between" }}>
                  <strong>Criterion {index + 1}</strong>
                  <Button type="button" variant="ghost" onClick={() => removeCriterion(index)}>
                    Remove
                  </Button>
                </div>
                <div className="inline-grid">
                  <Field label="Name">
                    <input
                      className="field-input"
                      value={criterion.name}
                      onChange={(event) => updateCriterion(index, { name: event.target.value })}
                    />
                  </Field>
                  <Field label="Weight">
                    <input
                      className="field-input"
                      type="number"
                      min={0.1}
                      step={0.1}
                      value={criterion.weight}
                      onChange={(event) => updateCriterion(index, { weight: Number(event.target.value) })}
                    />
                  </Field>
                </div>
                <Field label="Description">
                  <textarea
                    className="field-textarea"
                    value={criterion.description}
                    onChange={(event) => updateCriterion(index, { description: event.target.value })}
                  />
                </Field>
                <div className="inline-grid">
                  <Field label="Min score">
                    <input
                      className="field-input"
                      type="number"
                      min={0}
                      value={criterion.min_score}
                      onChange={(event) => updateCriterion(index, { min_score: Number(event.target.value) })}
                    />
                  </Field>
                  <Field label="Max score">
                    <input
                      className="field-input"
                      type="number"
                      min={1}
                      value={criterion.max_score}
                      onChange={(event) => updateCriterion(index, { max_score: Number(event.target.value) })}
                    />
                  </Field>
                </div>
                <Field label="Failure signals" hint="One per line">
                  <textarea
                    className="field-textarea"
                    value={joinLines(criterion.failure_signals)}
                    onChange={(event) =>
                      updateCriterion(index, { failure_signals: splitLines(event.target.value) })
                    }
                  />
                </Field>
                <Field label="Strong response fragments" hint="One per line">
                  <textarea
                    className="field-textarea"
                    value={joinLines(criterion.strong_response_fragments)}
                    onChange={(event) =>
                      updateCriterion(index, { strong_response_fragments: splitLines(event.target.value) })
                    }
                  />
                </Field>
              </div>
            ))}
          </div>

          <div className="stack-12">
            <div className="page-actions" style={{ justifyContent: "space-between" }}>
              <strong>Mastery thresholds</strong>
              <Button type="button" variant="secondary" onClick={addThreshold}>
                Add threshold
              </Button>
            </div>
            {value.rubric.thresholds.map((threshold, index) => (
              <div key={`${threshold.band}-${index}`} className="inline-grid">
                <Field label="Band">
                  <select
                    className="field-select"
                    value={threshold.band}
                    onChange={(event) =>
                      updateThreshold(index, {
                        band: event.target.value as MasteryThreshold["band"],
                      })
                    }
                  >
                    <option value="needs_review">Needs review</option>
                    <option value="partial">Partial</option>
                    <option value="ready_for_retry">Ready for retry</option>
                    <option value="interview_ready">Interview ready</option>
                  </select>
                </Field>
                <Field label="Min percentage">
                  <input
                    className="field-input"
                    type="number"
                    min={0}
                    max={100}
                    value={threshold.min_percentage}
                    onChange={(event) =>
                      updateThreshold(index, { min_percentage: Number(event.target.value) })
                    }
                  />
                </Field>
                <div className="stack-8" style={{ justifyContent: "end", alignItems: "end" }}>
                  <Button type="button" variant="ghost" onClick={() => removeThreshold(index)}>
                    Remove
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </SectionCard>

      <SectionCard
        eyebrow="Expected answer"
        title="Show the answer the operator wants the system to reward"
        action={<Button type="button" variant="secondary" onClick={addMistake}>Add mistake</Button>}
      >
        <div className="stack-16">
          <Field label="Answer text">
            <textarea
              className="field-textarea"
              value={value.expected_answer.answer_text}
              onChange={(event) => updateExpectedAnswer({ answer_text: event.target.value })}
            />
          </Field>
          <div className="inline-grid">
            <Field label="Answer outline" hint="One per line">
              <textarea
                className="field-textarea"
                value={joinLines(value.expected_answer.answer_outline)}
                onChange={(event) =>
                  updateExpectedAnswer({ answer_outline: splitLines(event.target.value) })
                }
              />
            </Field>
            <Field label="Key points" hint="One per line">
              <textarea
                className="field-textarea"
                value={joinLines(value.expected_answer.key_points)}
                onChange={(event) =>
                  updateExpectedAnswer({ key_points: splitLines(event.target.value) })
                }
              />
            </Field>
          </div>
          <Field label="Acceptable variants" hint="One per line">
            <textarea
              className="field-textarea"
              value={joinLines(value.expected_answer.acceptable_variants)}
              onChange={(event) =>
                updateExpectedAnswer({ acceptable_variants: splitLines(event.target.value) })
              }
            />
          </Field>
        </div>
      </SectionCard>

      <SectionCard eyebrow="Common mistakes" title="Capture the coaching moments">
        <div className="stack-12">
          {value.common_mistakes.map((mistake, index) => (
            <div key={`${mistake.mistake_text}-${index}`} className="surface surface-pad stack-12">
              <div className="page-actions" style={{ justifyContent: "space-between" }}>
                <strong>Mistake {index + 1}</strong>
                <Button type="button" variant="ghost" onClick={() => removeMistake(index)}>
                  Remove
                </Button>
              </div>
              <Field label="Mistake text">
                <input
                  className="field-input"
                  value={mistake.mistake_text}
                  onChange={(event) => updateMistake(index, { mistake_text: event.target.value })}
                />
              </Field>
              <Field label="Why it is wrong">
                <textarea
                  className="field-textarea"
                  value={mistake.why_it_is_wrong}
                  onChange={(event) => updateMistake(index, { why_it_is_wrong: event.target.value })}
                />
              </Field>
              <Field label="Remediation hint">
                <textarea
                  className="field-textarea"
                  value={mistake.remediation_hint}
                  onChange={(event) => updateMistake(index, { remediation_hint: event.target.value })}
                />
              </Field>
            </div>
          ))}
        </div>
      </SectionCard>

      <div className="page-actions">
        <Button type="button" onClick={onSubmit} disabled={submitting}>
          {submitting ? "Creating..." : "Create question bundle"}
        </Button>
        <Button type="button" variant="secondary" onClick={() => onChange(value)}>
          Sync draft
        </Button>
      </div>
    </div>
  );
}
