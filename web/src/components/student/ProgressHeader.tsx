import { formatStatusLabel } from "../../data/demoSession"
import type { SessionStatus } from "../../types/student"

interface ProgressHeaderProps {
  sessionTitle: string
  source: string
  status: SessionStatus
  currentIndex: number
  totalCount: number
  remainingCount: number
}

export function ProgressHeader({
  sessionTitle,
  source,
  status,
  currentIndex,
  totalCount,
  remainingCount,
}: ProgressHeaderProps) {
  const progress = totalCount === 0 ? 0 : Math.min(100, Math.round(((currentIndex + 1) / totalCount) * 100))

  return (
    <section className="card progress-header">
      <div className="progress-header__top">
        <div>
          <div className="card__eyebrow">Active session</div>
          <h1 className="progress-header__title">{sessionTitle}</h1>
          <p className="progress-header__body">{source} · {formatStatusLabel(status)}</p>
        </div>
        <div className="progress-header__stats">
          <div className="stat-chip">
            <span className="stat-chip__label">Current</span>
            <span className="stat-chip__value">{currentIndex + 1} / {totalCount}</span>
          </div>
          <div className="stat-chip">
            <span className="stat-chip__label">Remaining</span>
            <span className="stat-chip__value">{remainingCount}</span>
          </div>
        </div>
      </div>

      <div className="meter" aria-hidden="true">
        <div className="meter__fill" style={{ width: `${progress}%` }} />
      </div>
    </section>
  )
}

