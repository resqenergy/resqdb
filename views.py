"""Create materialized views from SQL files."""

from collections.abc import Iterable
from pathlib import Path

from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from settings import ENGINE, VIEWS_DIR

FUNCTIONS_DIR = VIEWS_DIR / "functions"
FUNCTION_SIGNATURES = ("flow_label(text, text)", "node_label(text)")


def get_views() -> Iterable[Path]:
    """
    Retrieve SQL views from a directory.

    Iterates through all files in the VIEWS directory, filters files with the .sql
    extension, reads their content, removes trailing semicolons, and retrieves their
    stem and query content as a tuple.

    Yields:
        Iterable[Path]: An iterable of paths to SQL files.

    """
    for view in VIEWS_DIR.iterdir():
        if view.suffix != ".sql":
            continue
        yield view


def read_query(view: Path) -> str:
    """Read a SQL query from a file."""
    with view.open("r", encoding="utf-8") as view_file:
        query = view_file.read()
        query = query.replace(";", "")
        return query


def create_view(view_name: str, query: str, *, recreate: bool = False) -> None:
    """
    Create or recreate a materialized view in the database with the specified query.

    This function handles the creation of a materialized view in the database. If the
    `recreate` flag is set to True, it will first drop the materialized view if it
    exists before creating it again. Otherwise, it will ensure that the view exists
    but will not overwrite it if it already exists.

    Args:
        view_name (str): The name of the materialized view to be created or recreated.
        query (str): The SQL query used to define the view.
        recreate (bool, optional): When set to True, drops and recreates the view even
            if it already exists. Defaults to False.

    """
    with Session(ENGINE) as session:
        if recreate:
            session.execute(text(f"DROP MATERIALIZED VIEW IF EXISTS {view_name};"))
        session.execute(
            text(f"CREATE MATERIALIZED VIEW IF NOT EXISTS {view_name} AS ({query});"),
        )
        session.commit()
        logger.info(f"Created materialized view '{view_name}'.")


def create_functions() -> None:
    """Create or replace SQL functions from files in the functions directory."""
    with Session(ENGINE) as session:
        for function_path in sorted(FUNCTIONS_DIR.glob("*.sql")):
            session.execute(text(function_path.read_text(encoding="utf-8")))
            logger.info(f"Created functions from '{function_path.name}'.")
        session.commit()


def delete_functions() -> None:
    """Delete SQL functions used by views."""
    with Session(ENGINE) as session:
        session.execute(
            text(f"DROP FUNCTION IF EXISTS {', '.join(FUNCTION_SIGNATURES)};"),
        )
        session.commit()
    logger.info("Deleted SQL functions.")


def create_all_views(*, recreate: bool = False) -> None:
    """
    Create all materialized views from SQL files in the views directory.

    SQL functions are created first, as views depend on them.

    Args:
        recreate (bool, optional): When set to True, drops and recreates all views even
            if it already exists. Defaults to False.

    """
    create_functions()
    for view_path in get_views():
        query = read_query(view_path)
        try:
            create_view(view_path.stem, query, recreate=recreate)
        except ProgrammingError:
            logger.error(f"Failed to create materialized view '{view_path.stem}'.")


def delete_view(view_name: str) -> None:
    """Delete a materialized view."""
    with Session(ENGINE) as session:
        session.execute(text(f"DROP MATERIALIZED VIEW IF EXISTS {view_name};"))
        session.commit()
    logger.info(f"Deleted materialized view '{view_name}'.")


def delete_all_views() -> None:
    """Delete all materialized views defined in views folder."""
    for view_path in get_views():
        view_name = view_path.stem
        delete_view(view_name)
    delete_functions()


if __name__ == "__main__":
    create_all_views(recreate=True)
