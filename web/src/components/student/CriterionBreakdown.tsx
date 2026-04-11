import type { StudentCriterionScore } from "../../types/student"

interface CriterionBreakdownProps {
  scores: StudentCriterionScore[]
}

export function CriterionBreakdown({ scores }: CriterionBreakdownProps) {
  return (
    <section className="card">
      <div className="card__eyebrow">Rubric breakdown</div>
      <div className="card__section-title-row">
        <h2 className="card__section-title">How the answer was read</h2>
        <p className="card__section-copy">The strongest demo result is specific, not vague. These bands make the feedback feel concrete.</p>
      </div>

      <div className="criterion-list">
        {scores.map((criterion) => {
          const percentage = Math.round((criterion.score / criterion.maxScore) * 100)
          return (
            <article key={criterion.criterionName} className="criterion-card">
              <div className="criterion-card__top">
                <div>
                  <h3 className="criterion-card__title">{criterion.criterionName}</h3>
                  <p className="criterion-card__notes">{criterion.notes}</p>
                </div>
                <span className="criterion-card__score">
                  {criterion.score}/{criterion.maxScore}
                </span>
              </div>

              <div className="meter meter--criterion" aria-hidden="true">
                <div className="meter__fill" style={{ width: `${percentage}%` }} />
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}

