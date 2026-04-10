import { NavLink } from "react-router-dom";
import { appConfig } from "@/app/appConfig";

const navItems = [
  { to: "/", label: "Landing" },
  { to: "/operator", label: "Operator" },
  { to: "/student", label: "Student" },
  { to: "/session", label: "Demo session" },
];

export function TopNav() {
  return (
    <header className="top-nav">
      <div className="top-nav__brand">
        <span className="top-nav__mark" aria-hidden="true">
          PD
        </span>
        <div>
          <div className="top-nav__name">{appConfig.brandName}</div>
          <div className="top-nav__subline">{appConfig.productLine}</div>
        </div>
      </div>

      <nav className="top-nav__links" aria-label="Primary">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `top-nav__link${isActive ? " top-nav__link--active" : ""}`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="top-nav__meta">
        <span className="status-badge status-badge--success">Shell ready</span>
      </div>
    </header>
  );
}
