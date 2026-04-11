import type { ReactNode } from "react";
import { TopNav } from "@/components/layout/TopNav";
import { FlowStepper } from "@/components/layout/FlowStepper";
import { appConfig } from "@/app/appConfig";

type AppShellProps = {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
  aside?: ReactNode;
  steps?: readonly { title: string; detail: string }[];
  activeStep?: number;
  children: ReactNode;
};

export function AppShell({
  eyebrow,
  title,
  description,
  actions,
  aside,
  steps,
  activeStep,
  children,
}: AppShellProps) {
  return (
    <div className="app-shell">
      <div className="app-shell__backdrop app-shell__backdrop--amber" />
      <div className="app-shell__backdrop app-shell__backdrop--green" />
      <TopNav />

      <main className="app-shell__stage">
        <section className="hero-card">
          <div className="hero-card__eyebrow">{eyebrow}</div>
          <h1 className="hero-card__title">{title}</h1>
          <p className="hero-card__description">{description}</p>
          {actions ? <div className="hero-card__actions">{actions}</div> : null}
          {steps ? (
            <div className="hero-card__steps">
              <FlowStepper steps={steps} activeStep={activeStep} />
            </div>
          ) : null}
        </section>

        <section className="app-shell__body">
          <div className="app-shell__primary">{children}</div>
          {aside ? <aside className="app-shell__aside">{aside}</aside> : null}
        </section>

        <footer className="app-shell__footer">
          <span>{appConfig.brandName}</span>
          <span>Frontend shell connected to the existing FastAPI backend</span>
        </footer>
      </main>
    </div>
  );
}
