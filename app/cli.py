from __future__ import annotations

import argparse
import json

import uvicorn

from app.core.settings import get_settings


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Prep Dojo runtime helpers.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("runserver")
    subparsers.add_parser("show-config")

    args = parser.parse_args()
    if args.command == "runserver":
        runserver()
        return
    if args.command == "show-config":
        show_config()
        return

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
