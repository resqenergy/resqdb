# ResQDB

## Overview

`resqdb` is a Python package designed to run energy system simulations using `oemof-tabular` and upload the results to a PostgreSQL database.
It automates the process of simulating energy scenarios defined in data packages and storing both scalar results and time-series flows in a structured database format,
allowing for further analysis and visualization.

Key features include:
- Simulation of energy systems defined in `oemof-tabular` data packages.
- Automated database schema setup and management using SQLAlchemy.
- Support for storing scenario-specific results (scalars and flows).
- Geographical mapping of results to clusters.
- Automated creation of materialized views in DB for further usage in visualization tool (i.e. Apache Superset)

## Setup

### Prerequisites

- Python 3.13 or higher.
- A PostgreSQL database with the PostGIS extension enabled.
- [uv](https://github.com/astral-sh/uv) for dependency management (recommended).

### Installation

Clone the repository and install the dependencies using `uv`:

```bash
uv sync
```

### Configuration

The application is configured via environment variables. Create a `.env` file in the root directory with the following variables:

```env
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=your_db_name
DB_SCHEMA=resqenergy
OEMOF_SCENARIO=investment
```

## Usage

The application provides a command-line interface `resq` to manage the simulation process and the database. You can run it using `python main.py` or through the installed package entry point.

### Available Commands

- **`run [scenario]`**: Run energy system simulations.
    - `scenario`: Name of the scenario to run or `all` (default) to run all scenarios found in the scenarios folder.
- **`setup`**: Initialize the database schema and tables.
- **`nuke`**: Drop the database schema and all its contents (use with caution).
- **`delete [id]`**: Delete scenario results from the database.
    - `id`: The ID of the scenario to delete or `all` (default) to delete all scenarios.
- **`views [command]`**: Manage database materialized views for visualization.
    - `command`: `recreate` (default) to update metadata and refresh views, or `drop` to remove all views.

### Examples

Run all scenarios:
```bash
python main.py run all
```

Initialize the database:
```bash
python main.py setup
```

Recreate materialized views:
```bash
python main.py views recreate
```

## Docker Compose

### Superset

Set up superset container:
1. Run `docker compose up -d --build`

Set up login role:
1. Enter container (via `docker exec -it <superset_container> bash`)
2. Create admin via `superset fab create-admin`
3. Run `superset db upgrade`
4. Run `superset init`

Set up postgresql DB support:
1. Enter container as root (via `docker exec -it -u root <superset_container> bash`)
2. Install pip via `python -m ensurepip --upgrade`
3. Run `python -m pip install psycopg2-binary`
4. Restart container

Import database, datasets, charts and dashboards
(This works only for an empty Superset environment)
1. Set correct sqlalchemy_uri in file `superset/databases/ResQEnergy.yaml`
1. Create `.zip` file from folder superset
2. Login to Superset
3. Open tab "Dashboards"
4. Click on "Import dashboards"
5. Select zipped superset file
6. Enter database password
