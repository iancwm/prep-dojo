import type { StudentResult, StudentSession } from "../../types/student"
import { formatBandLabel } from "../../data/demoSession"

interface SessionCompleteCardProps {
  session: StudentSession
  result: StudentResult
  onViewResult: () => void
}

export function SessionCompleteCard({ session, result, onViewResult }: SessionCompleteCardProps) {
  return (
    <section className="card card--hero">
      <div className="card__eyebrow">Session complete</div>
      <div className="card__title-row">
        <div>
          <h1 className="card__title">Your answer is scored.</h1>
          <p className="card__lede">The session closed cleanly, and the result page is ready with a rubric-backed breakdown.</p>
        </div>
        <span className="status-pill status-pill--complete">{formatBandLabel(result.score.masteryBand)}</span>
      </div>

      <div className="session-complete__grid">
        <div className="session-complete__metric">
          <span className="session-complete__metric-label">Overall score</span>
          <span className="session-complete__metric-value">{result.score.overallScore.toFixed(0)}%</span>
        </div>
        <div className="session-complete__metric">
          <span className="session-complete__metric-label">Attempts</span>
          <span className="session-complete__metric-value">{Math.max(1, session.attempts.length)}</span>
        </div>
        <div className="session-complete__metric">
          <span className="session-complete__metric-label">Next step</span>
          <span className="session-complete__metric-value">Review the breakdown</span>
        </div>
      </div>

      <div className="session-complete__actions">
        <button className="button button--primary" type="button" onClick={onViewResult}>
          View result
        </button>
      </div>
    </section>
  )
}
