import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

interface OperatorFrameProps {
  children: ReactNode;
}

const navLinks = [
  { to: "/operator", label: "Operator Home" },
  { to: "/operator/questions/new", label: "Question Composer" },
  { to: "/operator/sessions/preview", label: "Session Triage" },
];

export function OperatorFrame({ children }: OperatorFrameProps) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">P</span>
          <div>
            Prep Dojo
            <small>Operator studio for the guided demo loop</small>
          </div>
        </div>
        <nav className="topnav" aria-label="Operator navigation">
          {navLinks.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === "/operator"}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="workspace">{children}</main>
    </div>
  );
}

