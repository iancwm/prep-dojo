# Cloud Deployment Readiness

This repo is still pilot-first, but it now has a practical baseline that avoids the most common local-only assumptions without drifting into hyperscale platform work.

## What Is Ready

- Runtime values are centralized in [config/app.toml](/home/iancwm/git/prep-dojo/config/app.toml)
- Environment overrides are documented in [.env.example](/home/iancwm/git/prep-dojo/.env.example)
- Local automation is codified in [justfile](/home/iancwm/git/prep-dojo/justfile)
- The app already exposes a health endpoint at `/healthz`
- The app now exposes a readiness endpoint at `/readyz`
- The CLI can check DB reachability with `python -m app.cli check-readiness`
- Non-development environments prefer migration-first DB initialization unless explicitly overridden
- The server can bind to a cloud-provided port via `PORT`
- The server host can be overridden to `0.0.0.0` via `DEPLOY_HOST` or `APP_HOST`
- API responses propagate `X-Request-Id` and backend request/exception logs can be correlated by that id

## Config Surface

Primary runtime config:
- [config/app.toml](/home/iancwm/git/prep-dojo/config/app.toml)

Deployment profile notes:
- [config/deploy.toml](/home/iancwm/git/prep-dojo/config/deploy.toml)

The intended precedence is:
1. environment variables
2. `APP_CONFIG_PATH` target file
3. defaults in `config/app.toml`

## What Still Blocks Production

- No production entrypoint or platform manifest.
- No production auth or secret management.
- No metrics endpoint or external error reporting integration.
- No container image or CI deploy pipeline.
- No formal secret management or auth deployment story.

## Recommended Next Steps

1. Add secret-backed configuration for production credentials and auth keys.
2. Add one deployment artifact only after the target platform is known.
3. Add lightweight metrics or external error reporting once a real deployment target exists.
4. Keep the frontend same-origin or explicitly reverse-proxied so `/api` routing stays simple.
