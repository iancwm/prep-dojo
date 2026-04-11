from pathlib import Path

from app.core.local_dev import ensure_local_dev_config, get_local_dev_value, load_local_dev_settings


def test_ensure_local_dev_config_creates_file_from_template(tmp_path: Path) -> None:
    config_path = tmp_path / "local-dev.yaml"

    created_path = ensure_local_dev_config(config_path)

    assert created_path == config_path
    assert config_path.exists() is True
    assert "backend:" in config_path.read_text()


def test_ensure_local_dev_config_is_idempotent(tmp_path: Path) -> None:
    config_path = tmp_path / "local-dev.yaml"
    config_path.write_text("app_config_path: config/app.toml\n")

    ensure_local_dev_config(config_path)

    config_text = config_path.read_text()
    assert "app_config_path: config/app.toml\n" in config_text
    assert "backend:" in config_text
    assert "database:" in config_text


def test_load_local_dev_settings_reads_nested_values(tmp_path: Path) -> None:
    config_path = tmp_path / "local-dev.yaml"
    config_path.write_text(
        "\n".join(
            [
                "app_config_path: config/app.toml",
                "backend:",
                "  host: 127.0.0.1",
                "  port: 8012",
                "  reload: false",
                "  pid_file: .run/app.pid",
                "  log_file: .run/app.log",
                "frontend:",
                "  dev_port: 5174",
                "  preview_port: 4174",
                "database:",
                "  sqlite_path: local.db",
                "  url: sqlite:///./local.db",
                "  init_mode: migrations",
            ]
        )
        + "\n"
    )

    settings = load_local_dev_settings(config_path)

    assert settings.backend.port == 8012
    assert settings.backend.reload is False
    assert settings.frontend_backend_target == "http://127.0.0.1:8012"
    assert settings.database.url == "sqlite:///./local.db"


def test_get_local_dev_value_supports_derived_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "local-dev.yaml"
    config_path.write_text(
        "\n".join(
            [
                "app_config_path: config/app.toml",
                "backend:",
                "  host: 127.0.0.1",
                "  port: 8015",
                "  reload: false",
                "  pid_file: .run/app.pid",
                "  log_file: .run/app.log",
                "frontend:",
                "  dev_port: 5173",
                "  preview_port: 4173",
                "database:",
                "  sqlite_path: prep_dojo.db",
                "  url: sqlite:///./prep_dojo.db",
                "  init_mode: migrations",
            ]
        )
        + "\n"
    )

    assert get_local_dev_value("frontend.backend_target", config_path=config_path) == "http://127.0.0.1:8015"
    assert get_local_dev_value("database.url", config_path=config_path) == "sqlite:///./prep_dojo.db"


def test_load_local_dev_settings_preserves_explicit_database_url(tmp_path: Path) -> None:
    config_path = tmp_path / "local-dev.yaml"
    config_path.write_text(
        "\n".join(
            [
                "app_config_path: config/app.toml",
                "backend:",
                "  host: 127.0.0.1",
                "  port: 8010",
                "  reload: false",
                "  pid_file: .run/app.pid",
                "  log_file: .run/app.log",
                "frontend:",
                "  dev_port: 5173",
                "  preview_port: 4173",
                "database:",
                "  sqlite_path: prep_dojo.db",
                "  url: sqlite:////tmp/prep-dojo.db",
                "  init_mode: migrations",
            ]
        )
        + "\n"
    )

    settings = load_local_dev_settings(config_path)

    assert settings.database.url == "sqlite:////tmp/prep-dojo.db"
