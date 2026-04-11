import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  icon?: ReactNode;
}

export function Button({ variant = "primary", icon, className = "", children, ...props }: ButtonProps) {
  const classes = ["button", `button-${variant}`, className].filter(Boolean).join(" ");

  return (
    <button className={classes} {...props}>
      {icon}
      <span>{children}</span>
    </button>
  );
}

