set dotenv-load := true
set export := true
set shell := ["/bin/bash", "-lc"]

local_dev_config_path := env_var_or_default("LOCAL_DEV_CONFIG_PATH", "config/local-dev.yaml")
web_dir := "web"

default:
  @just --list

bootstrap:
  #!/usr/bin/env bash
  set -euo pipefail
  uv sync --extra dev
  npm --prefix {{web_dir}} install
  ./.venv/bin/python -m app.cli ensure-local-dev-config --path {{local_dev_config_path}} >/dev/null
  app_config_path=$(./.venv/bin/python -m app.cli get-local-dev-config app_config_path --path {{local_dev_config_path}})
  pid_file=$(./.venv/bin/python -m app.cli get-local-dev-config backend.pid_file --path {{local_dev_config_path}})
  log_file=$(./.venv/bin/python -m app.cli get-local-dev-config backend.log_file --path {{local_dev_config_path}})
  mkdir -p "$(dirname "$pid_file")"
  mkdir -p "$(dirname "$log_file")"
  if [ ! -f .env ]; then cp .env.example .env; fi
  echo "local dev config: {{local_dev_config_path}}"
  echo "app config: $app_config_path"

config:
  #!/usr/bin/env bash
  set -euo pipefail
  app_config_path=$(./.venv/bin/python -m app.cli get-local-dev-config app_config_path --path {{local_dev_config_path}})
  app_host=$(./.venv/bin/python -m app.cli get-local-dev-config backend.host --path {{local_dev_config_path}})
  app_port=$(./.venv/bin/python -m app.cli get-local-dev-config backend.port --path {{local_dev_config_path}})
  app_reload=$(./.venv/bin/python -m app.cli get-local-dev-config backend.reload --path {{local_dev_config_path}})
  database_url=$(./.venv/bin/python -m app.cli get-local-dev-config database.url --path {{local_dev_config_path}})
  database_init_mode=$(./.venv/bin/python -m app.cli get-local-dev-config database.init_mode --path {{local_dev_config_path}})
  APP_CONFIG_PATH="$app_config_path" APP_HOST="$app_host" APP_PORT="$app_port" APP_RELOAD="$app_reload" DATABASE_URL="$database_url" DATABASE_INIT_MODE="$database_init_mode" ./.venv/bin/python -m app.cli show-config

local-config:
  ./.venv/bin/python -m app.cli show-local-dev-config --path {{local_dev_config_path}}

test:
  #!/usr/bin/env bash
  set -euo pipefail
  app_config_path=$(./.venv/bin/python -m app.cli get-local-dev-config app_config_path --path {{local_dev_config_path}})
  database_url=$(./.venv/bin/python -m app.cli get-local-dev-config database.url --path {{local_dev_config_path}})
  APP_CONFIG_PATH="$app_config_path" DATABASE_URL="$database_url" ./.venv/bin/pytest tests

web-install:
  npm --prefix {{web_dir}} install

web-dev:
  #!/usr/bin/env bash
  set -euo pipefail
  backend_target=$(./.venv/bin/python -m app.cli get-local-dev-config frontend.backend_target --path {{local_dev_config_path}})
  frontend_port=$(./.venv/bin/python -m app.cli get-local-dev-config frontend.dev_port --path {{local_dev_config_path}})
  VITE_BACKEND_TARGET="$backend_target" npm --prefix {{web_dir}} run dev -- --port "$frontend_port"

web-build:
  #!/usr/bin/env bash
  set -euo pipefail
  backend_target=$(./.venv/bin/python -m app.cli get-local-dev-config frontend.backend_target --path {{local_dev_config_path}})
  VITE_BACKEND_TARGET="$backend_target" npm --prefix {{web_dir}} run build

web-test:
  npm --prefix {{web_dir}} test

web-typecheck:
  npm --prefix {{web_dir}} run typecheck

web-preview:
  #!/usr/bin/env bash
  set -euo pipefail
  backend_target=$(./.venv/bin/python -m app.cli get-local-dev-config frontend.backend_target --path {{local_dev_config_path}})
  preview_port=$(./.venv/bin/python -m app.cli get-local-dev-config frontend.preview_port --path {{local_dev_config_path}})
  VITE_BACKEND_TARGET="$backend_target" npm --prefix {{web_dir}} run preview -- --port "$preview_port"

migrate:
  #!/usr/bin/env bash
  set -euo pipefail
  app_config_path=$(./.venv/bin/python -m app.cli get-local-dev-config app_config_path --path {{local_dev_config_path}})
  database_url=$(./.venv/bin/python -m app.cli get-local-dev-config database.url --path {{local_dev_config_path}})
  APP_CONFIG_PATH="$app_config_path" DATABASE_URL="$database_url" ./.venv/bin/python -m app.cli migrate-head

up:
  #!/usr/bin/env bash
  set -euo pipefail
  app_config_path=$(./.venv/bin/python -m app.cli get-local-dev-config app_config_path --path {{local_dev_config_path}})
  app_host=$(./.venv/bin/python -m app.cli get-local-dev-config backend.host --path {{local_dev_config_path}})
  app_port=$(./.venv/bin/python -m app.cli get-local-dev-config backend.port --path {{local_dev_config_path}})
  app_reload=$(./.venv/bin/python -m app.cli get-local-dev-config backend.reload --path {{local_dev_config_path}})
  pid_file=$(./.venv/bin/python -m app.cli get-local-dev-config backend.pid_file --path {{local_dev_config_path}})
  log_file=$(./.venv/bin/python -m app.cli get-local-dev-config backend.log_file --path {{local_dev_config_path}})
  database_url=$(./.venv/bin/python -m app.cli get-local-dev-config database.url --path {{local_dev_config_path}})
  database_init_mode=$(./.venv/bin/python -m app.cli get-local-dev-config database.init_mode --path {{local_dev_config_path}})
  mkdir -p "$(dirname "$pid_file")"
  mkdir -p "$(dirname "$log_file")"
  if [ -f "$pid_file" ]; then
    if kill -0 "$(cat "$pid_file")" 2>/dev/null; then
      echo "prep-dojo already running on pid $(cat "$pid_file")"
      exit 0
    fi
    rm -f "$pid_file"
  fi
  APP_CONFIG_PATH="$app_config_path" DATABASE_URL="$database_url" DATABASE_INIT_MODE="$database_init_mode" APP_HOST="$app_host" APP_PORT="$app_port" APP_RELOAD="$app_reload" ./.venv/bin/python -m app.cli runserver > "$log_file" 2>&1 &
  echo $! > "$pid_file"
  sleep 1
  if ! kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    rm -f "$pid_file"
    echo "prep-dojo failed to start"
    if [ -f "$log_file" ]; then tail -n 50 "$log_file"; fi
    exit 1
  fi
  echo "prep-dojo started on pid $(cat "$pid_file")"
  echo "backend: http://$app_host:$app_port"
  echo "logs: $log_file"

down:
  #!/usr/bin/env bash
  set -euo pipefail
  pid_file=$(./.venv/bin/python -m app.cli get-local-dev-config backend.pid_file --path {{local_dev_config_path}})
  if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    kill "$(cat "$pid_file")" || true
    sleep 1
  fi
  rm -f "$pid_file"
  echo "prep-dojo is stopped"

restart:
  just down
  just up

status:
  #!/usr/bin/env bash
  set -euo pipefail
  pid_file=$(./.venv/bin/python -m app.cli get-local-dev-config backend.pid_file --path {{local_dev_config_path}})
  app_host=$(./.venv/bin/python -m app.cli get-local-dev-config backend.host --path {{local_dev_config_path}})
  app_port=$(./.venv/bin/python -m app.cli get-local-dev-config backend.port --path {{local_dev_config_path}})
  if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "prep-dojo running on pid $(cat "$pid_file")"
    echo "backend: http://$app_host:$app_port"
  else
    echo "prep-dojo is not running"
  fi

logs:
  #!/usr/bin/env bash
  set -euo pipefail
  log_file=$(./.venv/bin/python -m app.cli get-local-dev-config backend.log_file --path {{local_dev_config_path}})
  if [ -f "$log_file" ]; then
    tail -n 50 "$log_file"
  else
    echo "no log file at $log_file"
  fi

teardown-local:
  #!/usr/bin/env bash
  set -euo pipefail
  just down
  sqlite_path=$(./.venv/bin/python -m app.cli get-local-dev-config database.sqlite_path --path {{local_dev_config_path}})
  pid_file=$(./.venv/bin/python -m app.cli get-local-dev-config backend.pid_file --path {{local_dev_config_path}})
  log_file=$(./.venv/bin/python -m app.cli get-local-dev-config backend.log_file --path {{local_dev_config_path}})
  rm -f "$sqlite_path"
  rm -f "$pid_file"
  rm -f "$log_file"
  run_dir="$(dirname "$pid_file")"
  if [ -d "$run_dir" ] && [ "$run_dir" = "$(dirname "$log_file")" ]; then
    rmdir "$run_dir" 2>/dev/null || true
  fi
  echo "local runtime artifacts removed"

cloud-readiness:
  #!/usr/bin/env bash
  set -euo pipefail
  app_config_path=$(./.venv/bin/python -m app.cli get-local-dev-config app_config_path --path {{local_dev_config_path}})
  app_port=$(./.venv/bin/python -m app.cli get-local-dev-config backend.port --path {{local_dev_config_path}})
  echo "Runtime config: $app_config_path"
  echo "Local dev config: {{local_dev_config_path}}"
  echo "Deployment profile: config/deploy.toml"
  echo "Health endpoint: /healthz"
  echo "Port source: ${PORT:-$app_port}"
  echo "Migration command: just migrate"
  echo "Production hint: set DATABASE_INIT_MODE=migrations before rollout."
