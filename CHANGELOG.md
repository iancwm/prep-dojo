# Changelog

All notable changes to this project will be documented in this file.

The format is simple and release-oriented.

## [0.2.0.0] - 2026-04-11

### Added
- Added a Vite + React demo frontend for the guided operator and student story, covering question composition, review, session practice, and result views.
- Added root `npm` and `just` shortcuts so frontend install, dev, build, preview, and typecheck flows can run from the repo root.
- Added request observability helpers, structured request and exception logging, and `X-Request-Id` propagation in API responses.
- Added `/readyz` plus a CLI readiness check for quick database reachability verification.
- Added authored-question transition audit metadata, including the last actor role, reason, and transition timestamp.
- Added a Sprint 3 hardening spec focused on observability, runtime safety, and practical developer baseline improvements.

### Changed
- Changed runtime configuration so non-development environments default to migration-first database initialization and `reload = false` unless explicitly overridden.
- Changed the local test harness to use an isolated shared in-process SQLite database, which keeps tests independent from stale local schema files.
- Changed frontend API error handling so backend failures are named by action and the question composer can fall back to built-in assessment-mode defaults.
- Changed the README and deployment-readiness docs to reflect the current backend, frontend, readiness, and local workflow reality.

### Fixed
- Fixed the misleading composer failure state where optional mode-loading errors could surface as a full-page blocking error.
- Fixed readiness and observability gaps that previously made it hard to trace request failures or distinguish liveness from database readiness.
