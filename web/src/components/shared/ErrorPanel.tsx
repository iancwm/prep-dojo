import type { ReactNode } from "react";
import { Button } from "./Button";

interface ErrorPanelProps {
  title?: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  footer?: ReactNode;
}

export function ErrorPanel({ title = "Something needs attention", message, actionLabel, onAction, footer }: ErrorPanelProps) {
  return (
    <div className="error-panel stack-12">
      <strong>{title}</strong>
      <div>{message}</div>
      {actionLabel && onAction ? (
        <div>
          <Button variant="secondary" type="button" onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      ) : null}
      {footer ? <div>{footer}</div> : null}
    </div>
  );
}

