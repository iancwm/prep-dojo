import type { StudentQuestion } from "../../types/student"

interface QuestionPromptProps {
  question: StudentQuestion
}

export function QuestionPrompt({ question }: QuestionPromptProps) {
  return (
    <section className="card question-prompt">
      <div className="card__eyebrow">Question</div>
      <h2 className="question-prompt__title">{question.prompt}</h2>
      {question.context ? <p className="question-prompt__context">{question.context}</p> : null}

      <div className="question-prompt__foot">
        <div className="question-prompt__note">
          <span className="question-prompt__note-label">Cue</span>
          <span className="question-prompt__note-value">{question.cue ?? "Give a concise, confident answer."}</span>
        </div>

        {question.responseGuidance?.length ? (
          <ul className="question-prompt__guidance">
            {question.responseGuidance.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : null}
      </div>
    </section>
  )
}

