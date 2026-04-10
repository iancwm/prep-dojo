from app.db.session import uses_metadata_schema_management


def test_metadata_schema_management_is_enabled_for_metadata_mode() -> None:
    assert uses_metadata_schema_management("metadata") is True


def test_metadata_schema_management_is_disabled_for_migrations_mode() -> None:
    assert uses_metadata_schema_management("migrations") is False
