import type { StudentFeedbackResult } from "../../types/student"

interface FeedbackPanelProps {
  feedback: StudentFeedbackResult
}

export function FeedbackPanel({ feedback }: FeedbackPanelProps) {
  return (
    <section className="card">
      <div className="card__eyebrow">Feedback</div>
      <div className="card__section-title-row">
        <h2 className="card__section-title">What stands out</h2>
        <p className="card__section-copy">This is the part that makes the demo feel like a real practice product instead of a score badge.</p>
      </div>

      <div className="feedback-panel">
        <div className="feedback-panel__column">
          <h3>Strengths</h3>
          <ul className="bullet-list">
            {feedback.strengths.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="feedback-panel__column">
          <h3>Gaps</h3>
          <ul className="bullet-list bullet-list--muted">
            {feedback.gaps.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="feedback-panel__column">
          <h3>Next step</h3>
          <p className="feedback-panel__next-step">{feedback.nextStep}</p>
          <ul className="hint-list">
            {feedback.remediationHints.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}

