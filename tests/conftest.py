"""Shared pytest fixtures."""

from collections.abc import Iterator

import pytest
from sqlalchemy import Connection, text
from sqlalchemy.exc import OperationalError

import views
from settings import ENGINE


@pytest.fixture
def db_connection() -> Iterator[Connection]:
    """
    Yield a connection to the configured DB inside a transaction which is rolled back afterwards.

    SQL functions from the views folder are (re)created inside the transaction, so tests always run against the
    current function definitions. Tests are skipped if the DB is not reachable.

    Yields:
        Connection: Connection with an open transaction.

    """
    if ENGINE is None:
        pytest.skip("Database not configured.")
    try:
        connection = ENGINE.connect()
    except OperationalError as error:
        pytest.skip(f"Database not reachable: {error}")
    with connection, connection.begin() as transaction:
        for function_path in sorted(views.FUNCTIONS_DIR.glob("*.sql")):
            connection.execute(text(function_path.read_text(encoding="utf-8")))
        yield connection
        transaction.rollback()
