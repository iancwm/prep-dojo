import type { StudentAnswerDraft, StudentQuestion } from "../../types/student"

interface AnswerComposerProps {
  question: StudentQuestion
  value: StudentAnswerDraft
  onChange: (value: StudentAnswerDraft) => void
  onSubmit: () => void
  isSubmitting?: boolean
  disabled?: boolean
}

export function AnswerComposer({
  question,
  value,
  onChange,
  onSubmit,
  isSubmitting = false,
  disabled = false,
}: AnswerComposerProps) {
  const canSubmit = question.responseType === "multiple_choice"
    ? Boolean(value.selectedOptionId)
    : Boolean(value.content?.trim() || value.transcript?.trim())

  return (
    <section className="card answer-composer">
      <div className="card__eyebrow">Your answer</div>

      {question.responseType === "multiple_choice" ? (
        <fieldset className="answer-composer__field">
          <legend className="sr-only">Choose one answer</legend>
          <div className="choice-list">
            {question.options?.map((option) => (
              <label key={option.id} className={`choice ${value.selectedOptionId === option.id ? "choice--selected" : ""}`}>
                <input
                  type="radio"
                  name={question.id}
                  value={option.id}
                  checked={value.selectedOptionId === option.id}
                  disabled={disabled}
                  onChange={() => onChange({ ...value, responseType: "multiple_choice", selectedOptionId: option.id })}
                />
                <span className="choice__body">
                  <span className="choice__label">{option.label}</span>
                  {option.rationale ? <span className="choice__rationale">{option.rationale}</span> : null}
                </span>
              </label>
            ))}
          </div>
        </fieldset>
      ) : (
        <div className="answer-composer__field">
          <label className="field-label" htmlFor="student-answer">
            {question.responseType === "oral_transcript" ? "Transcript" : "Response"}
          </label>
          <textarea
            id="student-answer"
            className="textarea textarea--answer"
            rows={10}
            value={value.content ?? value.transcript ?? ""}
            placeholder={
              question.responseType === "oral_transcript"
                ? "Type the spoken answer transcript here."
                : "Write a concise interview answer with enough structure to be scored clearly."
            }
            disabled={disabled}
            onChange={(event) =>
              onChange(
                question.responseType === "oral_transcript"
                  ? { ...value, responseType: "oral_transcript", transcript: event.target.value }
                  : { ...value, responseType: "free_text", content: event.target.value },
              )
            }
          />

          {question.targetDurationSeconds ? (
            <div className="duration-chip">Target time: about {question.targetDurationSeconds} seconds</div>
          ) : null}
        </div>
      )}

      <div className="answer-composer__actions">
        <button className="button button--primary" type="button" onClick={onSubmit} disabled={!canSubmit || isSubmitting || disabled}>
          {isSubmitting ? "Scoring answer..." : "Submit answer"}
        </button>
        <p className="answer-composer__hint">The answer is scored immediately and the result screen shows the rubric breakdown.</p>
      </div>
    </section>
  )
}

