import { Link } from "react-router-dom";
import { Button } from "../components/shared/Button";
import { SectionCard } from "../components/shared/SectionCard";
import { StatusBadge } from "../components/shared/StatusBadge";

export function LandingPage() {
  return (
    <div className="app-shell">
      <main className="workspace">
        <section className="page-hero">
          <div className="kicker-row">
            <StatusBadge tone="soft" label="Guided demo" />
            <span className="inline-metric">Create to Practice to Review</span>
            <span className="inline-metric">Investor-facing prototype</span>
          </div>
          <h1>Interview prep that feels like a living system, not a pile of forms.</h1>
          <p>
            Prep Dojo turns authored interview content into a full loop. An operator creates and publishes a
            question, a learner practices it, and the scored outcome shows back up in the system with enough
            structure to feel real.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" to="/operator">
              Enter operator studio
            </Link>
            <Button type="button" variant="secondary" onClick={() => window.location.assign("/operator/questions/new")}>
              Start the demo path
            </Button>
          </div>
        </section>

        <div className="grid-3">
          <SectionCard
            eyebrow="Beat 1"
            title="Create credible content"
            description="The operator studio uses the real authored endpoints for topic, concept, question, rubric, and review state."
          >
            <div className="stack-12">
              <StatusBadge tone="draft" />
              <p className="muted">
                Draft one question that is structured enough to publish and serious enough to practice.
              </p>
            </div>
          </SectionCard>

          <SectionCard
            eyebrow="Beat 2"
            title="Run the learner experience"
            description="The student route loads the real session and question, then submits an answer for scoring."
          >
            <div className="stack-12">
              <StatusBadge tone="in_progress" label="Practice live" />
              <p className="muted">
                The practice workspace keeps the question central and the answer area calm, focused, and high-trust.
              </p>
            </div>
          </SectionCard>

          <SectionCard
            eyebrow="Beat 3"
            title="Review the system state"
            description="The operator session detail proves that the attempt, score, and lifecycle changes are not just frontend theater."
          >
            <div className="stack-12">
              <StatusBadge tone="completed" />
              <p className="muted">
                One clean loop. No dashboard sprawl. Just enough product surface to make the system feel inevitable.
              </p>
            </div>
          </SectionCard>
        </div>
      </main>
    </div>
  );
}
