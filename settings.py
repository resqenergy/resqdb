"""Holds settings for the project."""

from __future__ import annotations

import json
import os
import pathlib
import warnings
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import Engine, create_engine

if TYPE_CHECKING:
    from collections.abc import Mapping

warnings.filterwarnings("ignore", category=FutureWarning, module="oemof.solph")

env_file = os.environ.get("ENV_FILE", ".env")
load_dotenv(env_file)

DEBUG = os.getenv("DEBUG", "False") == "True"

ROOT_DIR = pathlib.Path(__file__).parent
CONFIG_DIR = ROOT_DIR / "config"
DATAPACKAGE_DIR = ROOT_DIR / "datapackages"
RESULTS_DIR = ROOT_DIR / "results"
GEOPACKAGES_DIR = ROOT_DIR / "geopackages"
VIEWS_DIR = ROOT_DIR / "views"
SCENARIOS_DIR = ROOT_DIR / "scenarios"

# --- Database Configuration ---
DB_CREDENTIALS = ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME")
DB_SCHEMA = os.environ.get("DB_SCHEMA", "public")


def get_database_url(environ: Mapping[str, str]) -> str | None:
    """
    Build the database URL from DB credentials in the given environment.

    Args:
        environ (Mapping[str, str]): Environment holding the DB credentials.

    Returns:
        str | None: Database URL, or None if no credentials are set (database store disabled).

    Raises:
        ValueError: If only some of the credentials are set.

    """
    missing = [key for key in DB_CREDENTIALS if not environ.get(key)]
    if len(missing) == len(DB_CREDENTIALS):
        return None
    if missing:
        raise ValueError(f"Incomplete DB credentials, missing: {', '.join(missing)}")
    user, password, host, port, name = (environ[key] for key in DB_CREDENTIALS)
    return f"timescaledb://{user}:{password}@{host}:{port}/{name}"


# Incomplete credentials only fail if the database store is used (see main)
DB_CONFIG_ERROR: str | None = None
try:
    DATABASE_URL = get_database_url(os.environ)
except ValueError as error:
    DATABASE_URL = None
    DB_CONFIG_ERROR = str(error)


def connect_to_db(url: str) -> Engine:
    """
    Connect to the PostgreSQL database.

    Args:
        url (str): Database URL.

    Returns:
        Engine: Engine connected to the database.

    """
    logger.info("Connecting to database.")
    return create_engine(url)


ENGINE = connect_to_db(DATABASE_URL) if DATABASE_URL else None

# --- OEMOF Settings ---
OEMOF_SCENARIO = os.getenv("OEMOF_SCENARIO", "dispatch")

# --- Cluster Mapping ---
CLUSTER_COMPONENT_FILE = CONFIG_DIR / "clusters.json"
CLUSTER_GEOPACKAGE = GEOPACKAGES_DIR / "clusters.gpkg"

with CLUSTER_COMPONENT_FILE.open("r", encoding="utf-8") as json_file:
    CLUSTERS = json.load(json_file)

# --- Components and categories Mapping ---
with (CONFIG_DIR / "component.json").open("r", encoding="utf-8") as json_file:
    COMPONENTS: dict[str, dict[str, str]] = json.load(json_file)

with (CONFIG_DIR / "categories.json").open("r", encoding="utf-8") as json_file:
    categories_raw = json.load(json_file)
CATEGORIES = {tuple(key.split("|")): value for key, value in categories_raw.items()}

# --- S3 Support ---
S3_ENDPOINT = os.environ.get("S3_ENDPOINT")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY")
