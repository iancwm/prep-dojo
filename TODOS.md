# TODOS

## Frontend Demo

- Title: Add frontend test baseline for `web/`
  - **Priority:** P1
  - **Why:** The demo frontend builds cleanly, but it does not yet have automated UI or route-level tests.
  - **Next step:** Add Vitest plus a small set of smoke tests for routing, composer fallback behavior, and student result flows.

- Title: Reconstruct student results from backend state
  - **Priority:** P2
  - **Why:** The current result flow still depends on client-side demo session storage for part of the experience.
  - **Next step:** Load result state entirely from persisted backend session and attempt data.

## Sprint 3 Hardening

- Title: Document JSON field intent in architecture docs
  - **Priority:** P1
  - **Why:** The repo now has lightweight data guardrails, but the intentional JSON-backed fields versus future normalization targets are not yet called out in `ARCHITECTURE.md`.
  - **Next step:** Add a short section explaining which JSON fields are deliberate and which are next normalization candidates.

- Title: Tighten session and attempt invariants
  - **Priority:** P2
  - **Why:** Sprint 3 added observability and audit metadata, but the next highest-value backend hardening step is still protecting the remaining workflow seams around session and attempt transitions.
  - **Next step:** Add a focused invariants pass and regression tests for the sharpest session and attempt edge cases.

- Title: Clarify seeded reference-user assumptions
  - **Priority:** P2
  - **Why:** The current seeded reference-user behavior is still practical for demos, but it should be documented clearly before more developer work stacks on top of it.
  - **Next step:** Add explicit docs and code comments that separate demo identity assumptions from future real-user auth behavior.

## Completed
