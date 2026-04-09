# Cloud Deployment Readiness

This repo is still development-first, but it now has the minimum shape needed to stop baking local assumptions into the codebase.

## What Is Ready

- Runtime values are centralized in [config/app.toml](/Users/iancwm/git/prep-dojo/config/app.toml)
- Environment overrides are documented in [.env.example](/Users/iancwm/git/prep-dojo/.env.example)
- Local automation is codified in [justfile](/Users/iancwm/git/prep-dojo/justfile)
- The app already exposes a health endpoint at `/healthz`
- The server can bind to a cloud-provided port via `PORT`
- The server host can be overridden to `0.0.0.0` via `DEPLOY_HOST` or `APP_HOST`

## Config Surface

Primary runtime config:
- [config/app.toml](/Users/iancwm/git/prep-dojo/config/app.toml)

Deployment profile notes:
- [config/deploy.toml](/Users/iancwm/git/prep-dojo/config/deploy.toml)

The intended precedence is:
1. environment variables
2. `APP_CONFIG_PATH` target file
3. defaults in `config/app.toml`

## What Still Blocks Production

- No migration layer yet. Startup still relies on `Base.metadata.create_all()`.
- No production auth or secret management.
- No container image, deployment manifest, or CI deploy pipeline.
- No separation between dev and prod database lifecycle behavior.
- No observability beyond process logs and `/healthz`.

## Recommended Next Steps

1. Add Alembic and remove `create_all()` from production startup.
2. Add a production entrypoint with `reload = false` and explicit worker strategy.
3. Add structured logging and request-level error monitoring.
4. Add secret-backed configuration for database credentials and future auth keys.
5. Add a container or platform manifest after migrations exist.
