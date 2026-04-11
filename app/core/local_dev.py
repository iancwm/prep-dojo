from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_LOCAL_DEV_CONFIG_PATH = ROOT_DIR / "config" / "local-dev.yaml"
DEFAULT_LOCAL_DEV_TEMPLATE_PATH = ROOT_DIR / "config" / "local-dev.yaml.example"


@dataclass(frozen=True)
class LocalBackendSettings:
    host: str
    port: int
    reload: bool
    pid_file: str
    log_file: str


@dataclass(frozen=True)
class LocalFrontendSettings:
    dev_port: int
    preview_port: int


@dataclass(frozen=True)
class LocalDatabaseSettings:
    sqlite_path: str
    init_mode: str
    url: str


@dataclass(frozen=True)
class LocalDevSettings:
    config_path: str
    app_config_path: str
    backend: LocalBackendSettings
    frontend: LocalFrontendSettings
    database: LocalDatabaseSettings

    @property
    def frontend_backend_target(self) -> str:
        return f"http://{self.backend.host}:{self.backend.port}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "config_path": self.config_path,
            "app_config_path": self.app_config_path,
            "backend": {
                "host": self.backend.host,
                "port": self.backend.port,
                "reload": self.backend.reload,
                "pid_file": self.backend.pid_file,
                "log_file": self.backend.log_file,
            },
            "frontend": {
                "dev_port": self.frontend.dev_port,
                "preview_port": self.frontend.preview_port,
                "backend_target": self.frontend_backend_target,
            },
            "database": {
                "sqlite_path": self.database.sqlite_path,
                "init_mode": self.database.init_mode,
                "url": self.database.url,
            },
        }


def ensure_local_dev_config(path: str | Path | None = None) -> Path:
    config_path = _resolve_path(path or DEFAULT_LOCAL_DEV_CONFIG_PATH)
    template_data = _parse_yaml_mapping(DEFAULT_LOCAL_DEV_TEMPLATE_PATH.read_text())
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if not config_path.exists():
        config_path.write_text(_dump_yaml_mapping(template_data))
        return config_path

    current_data = _parse_yaml_mapping(config_path.read_text())
    merged_data = _merge_missing_values(current_data, template_data)
    if merged_data != current_data:
        config_path.write_text(_dump_yaml_mapping(merged_data))
    return config_path


def load_local_dev_settings(path: str | Path | None = None) -> LocalDevSettings:
    config_path = ensure_local_dev_config(path)
    raw = _parse_yaml_mapping(config_path.read_text())

    backend = raw.get("backend", {})
    frontend = raw.get("frontend", {})
    database = raw.get("database", {})

    return LocalDevSettings(
        config_path=str(config_path),
        app_config_path=str(raw.get("app_config_path", "config/app.toml")),
        backend=LocalBackendSettings(
            host=str(backend.get("host", "127.0.0.1")),
            port=int(backend.get("port", 8010)),
            reload=bool(backend.get("reload", False)),
            pid_file=str(backend.get("pid_file", ".run/prep-dojo.pid")),
            log_file=str(backend.get("log_file", ".run/prep-dojo.log")),
        ),
        frontend=LocalFrontendSettings(
            dev_port=int(frontend.get("dev_port", 5173)),
            preview_port=int(frontend.get("preview_port", 4173)),
        ),
        database=LocalDatabaseSettings(
            sqlite_path=str(database.get("sqlite_path", "prep_dojo.db")),
            init_mode=str(database.get("init_mode", "migrations")),
            url=str(database.get("url", f"sqlite:///./{database.get('sqlite_path', 'prep_dojo.db')}")),
        ),
    )


def get_local_dev_value(path: str, *, config_path: str | Path | None = None) -> Any:
    data = load_local_dev_settings(config_path).as_dict()
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(f"Unknown local dev config path `{path}`.")
        current = current[part]
    return current


def _resolve_path(path: str | Path) -> Path:
    path_obj = Path(path).expanduser()
    if path_obj.is_absolute():
        return path_obj
    return ROOT_DIR / path_obj


def _parse_yaml_mapping(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()

        container = stack[-1][1]
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()

        if not value:
            nested: dict[str, Any] = {}
            container[key] = nested
            stack.append((indent, nested))
            continue

        container[key] = _parse_scalar(value)

    return root


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if value.isdigit():
        return int(value)
    if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
        return value[1:-1]
    return value


def _merge_missing_values(current: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for key, template_value in template.items():
        current_value = current.get(key)
        if isinstance(template_value, dict):
            if isinstance(current_value, dict):
                merged[key] = _merge_missing_values(current_value, template_value)
            else:
                merged[key] = template_value
            continue

        merged[key] = template_value if key not in current else current_value

    for key, current_value in current.items():
        if key not in merged:
            merged[key] = current_value

    return merged


def _dump_yaml_mapping(data: dict[str, Any], *, indent: int = 0) -> str:
    lines: list[str] = []
    padding = " " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{padding}{key}:")
            lines.append(_dump_yaml_mapping(value, indent=indent + 2).rstrip("\n"))
            continue
        lines.append(f"{padding}{key}: {_dump_scalar(value)}")
    return "\n".join(lines) + "\n"


def _dump_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
