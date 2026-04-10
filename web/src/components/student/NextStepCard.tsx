interface NextStepCardProps {
  onReturnToSession: () => void
}

export function NextStepCard({ onReturnToSession }: NextStepCardProps) {
  return (
    <section className="card next-step-card">
      <div className="card__eyebrow">Continue</div>
      <h2 className="card__section-title">Use the result to keep the loop moving.</h2>
      <p className="card__section-copy">
        The guided demo works best when the student result is not the end of the story. Keep the next practice path one click away.
      </p>

      <div className="next-step-card__actions">
        <button className="button button--primary" type="button" onClick={onReturnToSession}>
          Back to session
        </button>
      </div>
    </section>
  )
}

