import type { TextareaHTMLAttributes, ReactNode } from "react";

type TextAreaProps = {
  label: string;
  helperText?: string;
  children?: ReactNode;
} & TextareaHTMLAttributes<HTMLTextAreaElement>;

export function TextArea({
  label,
  helperText,
  children,
  className = "",
  ...props
}: TextAreaProps) {
  return (
    <label className={`field ${className}`.trim()}>
      <span className="field__label">{label}</span>
      {children ?? <textarea className="field__control field__control--textarea" {...props} />}
      {helperText ? <span className="field__helper">{helperText}</span> : null}
    </label>
  );
}
