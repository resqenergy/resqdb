"""Holds settings for the project."""

from __future__ import annotations

import json
import os
import pathlib
import warnings

from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import Engine, create_engine

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
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]
DB_SCHEMA = os.environ.get("DB_SCHEMA", "public")

DATABASE_URL = f"timescaledb://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def connect_to_db(url: str) -> Engine:
    """Connect to the PostgreSQL database."""
    logger.info(f"Connecting to database: {url}")
    return create_engine(DATABASE_URL)


ENGINE = connect_to_db(DATABASE_URL)

# --- OEMOF Settings ---
OEMOF_WRITE_RESULTS = os.getenv("OEMOF_WRITE_RESULTS", "False") == "True"
OEMOF_SCENARIO = os.getenv("OEMOF_SCENARIO", "dispatch")
OEMOF_OVERWRITE_RESULTS = os.getenv("OEMOF_OVERWRITE_RESULTS", "False") == "True"

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
