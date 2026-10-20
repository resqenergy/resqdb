"""Tests for settings."""

import pytest

import settings

DB_ENV = {
    "DB_USER": "user",
    "DB_PASSWORD": "secret",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_NAME": "resq",
}


def test_database_url_is_none_without_credentials() -> None:
    """Without any DB credentials the database store is disabled."""
    assert settings.get_database_url({}) is None


def test_database_url_from_credentials() -> None:
    """Complete DB credentials result in a database URL."""
    assert (
        settings.get_database_url(DB_ENV)
        == "timescaledb://user:secret@localhost:5432/resq"
    )


def test_partial_credentials_raise() -> None:
    """Partially set DB credentials are a configuration error, not a fallback to files."""
    env = {key: value for key, value in DB_ENV.items() if key != "DB_HOST"}
    with pytest.raises(ValueError, match="DB_HOST"):
        settings.get_database_url(env)
