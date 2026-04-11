from __future__ import annotations

import argparse
import json

import uvicorn
from alembic import command
from alembic.config import Config

from app.core.local_dev import ensure_local_dev_config, get_local_dev_value, load_local_dev_settings
from app.core.settings import get_settings
from app.db.session import check_database_readiness, get_alembic_config_path


def runserver() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        log_level=settings.server.log_level,
        proxy_headers=settings.deployment.proxy_headers,
    )


def show_config() -> None:
    settings = get_settings()
    print(json.dumps(settings.as_dict(), indent=2, sort_keys=True))


def migrate_head() -> None:
    command.upgrade(Config(str(get_alembic_config_path())), "head")


def check_readiness() -> None:
    settings = get_settings()
    report = check_database_readiness()
    print(
        json.dumps(
            {
                "app_environment": settings.app.environment,
                "database_init_mode": settings.database.init_mode,
                "database_ready": report.ready,
                "message": report.message,
            },
            indent=2,
            sort_keys=True,
        )
    )
    if not report.ready:
        raise SystemExit(1)


def ensure_local_dev(path: str | None) -> None:
    config_path = ensure_local_dev_config(path)
    print(config_path)


def show_local_dev(path: str | None) -> None:
    settings = load_local_dev_settings(path)
    print(json.dumps(settings.as_dict(), indent=2, sort_keys=True))


def get_local_dev(path: str | None, key: str) -> None:
    print(get_local_dev_value(key, config_path=path))


def main() -> None:
    parser = argparse.ArgumentParser(description="Prep Dojo runtime helpers.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("runserver")
    subparsers.add_parser("show-config")
    subparsers.add_parser("migrate-head")
    subparsers.add_parser("check-readiness")
    ensure_local_dev_parser = subparsers.add_parser("ensure-local-dev-config")
    ensure_local_dev_parser.add_argument("--path", default=None)
    show_local_dev_parser = subparsers.add_parser("show-local-dev-config")
    show_local_dev_parser.add_argument("--path", default=None)
    get_local_dev_parser = subparsers.add_parser("get-local-dev-config")
    get_local_dev_parser.add_argument("key")
    get_local_dev_parser.add_argument("--path", default=None)

    args = parser.parse_args()
    if args.command == "runserver":
        runserver()
        return
    if args.command == "show-config":
        show_config()
        return
    if args.command == "migrate-head":
        migrate_head()
        return
    if args.command == "check-readiness":
        check_readiness()
        return
    if args.command == "ensure-local-dev-config":
        ensure_local_dev(args.path)
        return
    if args.command == "show-local-dev-config":
        show_local_dev(args.path)
        return
    if args.command == "get-local-dev-config":
        get_local_dev(args.path, args.key)
        return

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
