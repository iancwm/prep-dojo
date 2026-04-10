import type { StudentResult } from "../../types/student"
import { formatBandLabel } from "../../data/demoSession"

interface ScoreHeroProps {
  result: StudentResult
}

export function ScoreHero({ result }: ScoreHeroProps) {
  const ringStyle = {
    background: `conic-gradient(var(--accent) ${result.score.overallScore}%, rgba(32, 58, 82, 0.12) 0)`,
  }

  return (
    <section className="card score-hero">
      <div className="score-hero__ring" style={ringStyle} aria-hidden="true">
        <div className="score-hero__ring-inner">
          <span className="score-hero__score">{result.score.overallScore.toFixed(0)}</span>
          <span className="score-hero__percent">/ 100</span>
        </div>
      </div>

      <div className="score-hero__content">
        <div className="card__eyebrow">Result</div>
        <h1 className="score-hero__title">{formatBandLabel(result.score.masteryBand)}</h1>
        <p className="score-hero__body">
          {result.question.title} scored by {result.score.scoringMethod} rubric logic.
        </p>

        <dl className="score-hero__meta">
          <div>
            <dt>Question</dt>
            <dd>{result.question.id}</dd>
          </div>
          <div>
            <dt>Attempt</dt>
            <dd>{result.attemptId}</dd>
          </div>
          <div>
            <dt>Answered</dt>
            <dd>{new Date(result.completedAt).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}</dd>
          </div>
        </dl>
      </div>
    </section>
  )
}

