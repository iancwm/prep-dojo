import type { ReactNode } from "react";

interface FieldProps {
  label: string;
  hint?: string;
  error?: string | null;
  children: ReactNode;
  className?: string;
}

export function Field({ label, hint, error, children, className = "" }: FieldProps) {
  const classes = ["field", className].filter(Boolean).join(" ");

  return (
    <div className={classes}>
      <label>
        <span>{label}</span>
        {hint ? <small>{hint}</small> : null}
      </label>
      {children}
      {error ? <small className="field-help" style={{ color: "var(--danger)" }}>{error}</small> : null}
    </div>
  );
}

