from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
import os
import tomllib


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = ROOT_DIR / "config" / "app.toml"


@dataclass(frozen=True)
class AppSettings:
    name: str
    version: str
    description: str
    environment: str


@dataclass(frozen=True)
class ServerSettings:
    host: str
    port: int
    reload: bool
    log_level: str


@dataclass(frozen=True)
class DatabaseSettings:
    url: str
    init_mode: str


@dataclass(frozen=True)
class PracticeSettings:
    reference_student_email: str


@dataclass(frozen=True)
class RuntimeSettings:
    pid_file: str
    log_file: str


@dataclass(frozen=True)
class DeploymentSettings:
    host: str
    port_env_var: str
    healthcheck_path: str
    proxy_headers: bool


@dataclass(frozen=True)
class Settings:
    config_path: str
    app: AppSettings
    server: ServerSettings
    database: DatabaseSettings
    practice: PracticeSettings
    runtime: RuntimeSettings
    deployment: DeploymentSettings

    def as_dict(self) -> dict:
        return asdict(self)


def _read_config_file(config_path: Path) -> dict:
    with config_path.open("rb") as handle:
        return tomllib.load(handle)


def _env_or_default(name: str, default):
    return os.getenv(name, default)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    config_path = Path(os.getenv("APP_CONFIG_PATH", str(DEFAULT_CONFIG_PATH))).expanduser()
    if not config_path.is_absolute():
        config_path = ROOT_DIR / config_path
    config = _read_config_file(config_path)

    app_config = config["app"]
    server_config = config["server"]
    database_config = config["database"]
    practice_config = config["practice"]
    runtime_config = config["runtime"]
    deployment_config = config["deployment"]

    return Settings(
        config_path=str(config_path),
        app=AppSettings(
            name=_env_or_default("APP_NAME", app_config["name"]),
            version=_env_or_default("APP_VERSION", app_config["version"]),
            description=_env_or_default("APP_DESCRIPTION", app_config["description"]),
            environment=_env_or_default("APP_ENV", app_config["environment"]),
        ),
        server=ServerSettings(
            host=_env_or_default("APP_HOST", _env_or_default("DEPLOY_HOST", server_config["host"])),
            port=_env_int("APP_PORT", int(_env_or_default(deployment_config["port_env_var"], server_config["port"]))),
            reload=_env_bool("APP_RELOAD", server_config["reload"]),
            log_level=_env_or_default("APP_LOG_LEVEL", server_config["log_level"]),
        ),
        database=DatabaseSettings(
            url=_env_or_default("DATABASE_URL", database_config["url"]),
            init_mode=_env_or_default("DATABASE_INIT_MODE", database_config.get("init_mode", "metadata")),
        ),
        practice=PracticeSettings(
            reference_student_email=_env_or_default(
                "REFERENCE_STUDENT_EMAIL",
                practice_config["reference_student_email"],
            ),
        ),
        runtime=RuntimeSettings(
            pid_file=_env_or_default("APP_PID_FILE", runtime_config["pid_file"]),
            log_file=_env_or_default("APP_LOG_FILE", runtime_config["log_file"]),
        ),
        deployment=DeploymentSettings(
            host=_env_or_default("DEPLOY_HOST", deployment_config["host"]),
            port_env_var=_env_or_default("DEPLOY_PORT_ENV_VAR", deployment_config["port_env_var"]),
            healthcheck_path=_env_or_default("DEPLOY_HEALTHCHECK_PATH", deployment_config["healthcheck_path"]),
            proxy_headers=_env_bool("DEPLOY_PROXY_HEADERS", deployment_config["proxy_headers"]),
        ),
    )
