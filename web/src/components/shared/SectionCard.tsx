import type { ReactNode } from "react";

interface SectionCardProps {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function SectionCard({
  eyebrow,
  title,
  description,
  action,
  children,
  className = "",
}: SectionCardProps) {
  const classes = ["section-card", className].filter(Boolean).join(" ");

  return (
    <section className={classes}>
      <header>
        <div className="stack-8">
          {eyebrow ? <div className="eyebrow">{eyebrow}</div> : null}
          <div className="stack-8">
            <h2>{title}</h2>
            {description ? <p>{description}</p> : null}
          </div>
        </div>
        {action ? <div>{action}</div> : null}
      </header>
      {children}
    </section>
  );
}

