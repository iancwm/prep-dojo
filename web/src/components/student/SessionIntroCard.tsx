import type { StudentQuestion, StudentSession } from "../../types/student"
import { formatStatusLabel } from "../../data/demoSession"

interface SessionIntroCardProps {
  session: StudentSession
  question: StudentQuestion
  onStart: () => void
  isStarting?: boolean
}

export function SessionIntroCard({ session, question, onStart, isStarting = false }: SessionIntroCardProps) {
  return (
    <section className="card card--hero">
      <div className="card__eyebrow">Practice session</div>
      <div className="card__title-row">
        <div>
          <h1 className="card__title">{session.title}</h1>
          <p className="card__lede">{session.subtitle}</p>
        </div>
        <span className="status-pill status-pill--ready">{formatStatusLabel(session.status)}</span>
      </div>

      <div className="session-intro__grid">
        <div className="session-intro__summary">
          <p className="session-intro__summary-label">Focus question</p>
          <p className="session-intro__summary-title">{question.title}</p>
          <p className="session-intro__summary-body">{question.context}</p>
        </div>

        <div className="session-intro__meta">
          <div className="session-intro__meta-item">
            <span className="session-intro__meta-label">Queue</span>
            <span className="session-intro__meta-value">{session.questionQueue.length} prompt</span>
          </div>
          <div className="session-intro__meta-item">
            <span className="session-intro__meta-label">Session</span>
            <span className="session-intro__meta-value">{session.source}</span>
          </div>
          <div className="session-intro__meta-item">
            <span className="session-intro__meta-label">Recommended pace</span>
            <span className="session-intro__meta-value">60 seconds</span>
          </div>
        </div>
      </div>

      <div className="session-intro__actions">
        <button className="button button--primary" type="button" onClick={onStart} disabled={isStarting}>
          {isStarting ? "Starting session..." : "Start practice"}
        </button>
        <p className="session-intro__note">The first answer is scored against a rubric and returned with a clean result summary.</p>
      </div>
    </section>
  )
}

