set dotenv-load := true
set export := true
set shell := ["/bin/zsh", "-cu"]

config_path := env_var_or_default("APP_CONFIG_PATH", "config/app.toml")
pid_file := env_var_or_default("APP_PID_FILE", ".run/prep-dojo.pid")
log_file := env_var_or_default("APP_LOG_FILE", ".run/prep-dojo.log")
local_sqlite_path := env_var_or_default("LOCAL_SQLITE_PATH", "prep_dojo.db")

default:
  @just --list

bootstrap:
  #!/usr/bin/env bash
  set -euo pipefail
  uv sync --extra dev
  mkdir -p .run
  if [ ! -f .env ]; then cp .env.example .env; fi

config:
  APP_CONFIG_PATH={{config_path}} ./.venv/bin/python -m app.cli show-config

test:
  APP_CONFIG_PATH={{config_path}} ./.venv/bin/pytest tests

up:
  #!/usr/bin/env bash
  set -euo pipefail
  mkdir -p .run
  if [ -f {{pid_file}} ] && kill -0 "$(cat {{pid_file}})" 2>/dev/null; then
    echo "prep-dojo already running on pid $(cat {{pid_file}})"
    exit 1
  fi
  APP_CONFIG_PATH={{config_path}} ./.venv/bin/python -m app.cli runserver > {{log_file}} 2>&1 &
  echo $! > {{pid_file}}
  echo "prep-dojo started on pid $(cat {{pid_file}})"
  echo "logs: {{log_file}}"

down:
  #!/usr/bin/env bash
  set -euo pipefail
  if [ -f {{pid_file}} ] && kill -0 "$(cat {{pid_file}})" 2>/dev/null; then
    kill "$(cat {{pid_file}})"
  fi
  rm -f {{pid_file}}

restart:
  just down
  just up

status:
  #!/usr/bin/env bash
  set -euo pipefail
  if [ -f {{pid_file}} ] && kill -0 "$(cat {{pid_file}})" 2>/dev/null; then
    echo "prep-dojo running on pid $(cat {{pid_file}})"
  else
    echo "prep-dojo is not running"
  fi

logs:
  #!/usr/bin/env bash
  set -euo pipefail
  if [ -f {{log_file}} ]; then
    tail -n 50 {{log_file}}
  else
    echo "no log file at {{log_file}}"
  fi

teardown-local:
  #!/usr/bin/env bash
  set -euo pipefail
  just down
  rm -f {{local_sqlite_path}}
  rm -rf .run

cloud-readiness:
  #!/usr/bin/env bash
  set -euo pipefail
  echo "Runtime config: {{config_path}}"
  echo "Deployment profile: config/deploy.toml"
  echo "Health endpoint: /healthz"
  echo "Port source: ${PORT:-8000}"
  echo "Next step: replace startup create_all with migrations before production rollout."
