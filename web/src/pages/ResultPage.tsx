import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { CriterionBreakdown } from "../components/student/CriterionBreakdown"
import { FeedbackPanel } from "../components/student/FeedbackPanel"
import { NextStepCard } from "../components/student/NextStepCard"
import { ScoreHero } from "../components/student/ScoreHero"
import { loadStudentResult } from "../data/demoSession"
import type { StudentResult } from "../types/student"
import "../styles/student.css"

interface ResultPageViewProps {
  result: StudentResult | null
  onReturnToSession: () => void
}

export function ResultPageView({ result, onReturnToSession }: ResultPageViewProps) {
  if (!result) {
    return (
      <div className="page page--student">
        <section className="card card--hero">
          <div className="card__eyebrow">Result missing</div>
          <h1 className="card__title">No scored result is available yet.</h1>
          <p className="card__lede">Open the practice session first, submit the answer, then come back to this page.</p>
          <div className="session-complete__actions">
            <button className="button button--primary" type="button" onClick={onReturnToSession}>
              Back to session
            </button>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="page page--student page--result">
      <ScoreHero result={result} />
      <div className="page-stack">
        <CriterionBreakdown scores={result.score.criterionScores} />
        <FeedbackPanel feedback={result.feedback} />
        <NextStepCard onReturnToSession={onReturnToSession} />
      </div>
    </div>
  )
}

export default function ResultPage() {
  const params = useParams()
  const navigate = useNavigate()
  const sessionId = params.sessionId ?? ""
  const [result, setResult] = useState<StudentResult | null>(() => loadStudentResult(sessionId))

  useEffect(() => {
    setResult(loadStudentResult(sessionId))
  }, [sessionId])

  function handleReturnToSession() {
    navigate(`/practice/${sessionId}`)
  }

  return <ResultPageView result={result} onReturnToSession={handleReturnToSession} />
}
