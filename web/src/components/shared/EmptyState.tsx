import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="quote-box stack-8">
      <strong>{title}</strong>
      <p className="muted">{description}</p>
      {action ? <div>{action}</div> : null}
    </div>
  );
}

