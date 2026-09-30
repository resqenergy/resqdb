"""Module to handle scenarios."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError

if TYPE_CHECKING:
    from pathlib import Path
    from collections.abc import Iterable

import yaml
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from settings import ENGINE, SCENARIOS_DIR


class ScenarioError(Exception):
    """Raised when scenario or related data does not exist in the database."""


@dataclasses.dataclass(frozen=True)
class ScenarioConfig:
    """Configuration object for a scenario."""

    name: str
    scenario: dict
    datapackage: str
    capacities: dict | None = dataclasses.field(default_factory=dict)


def get_scenarios_in_folder(folder: Path = SCENARIOS_DIR) -> Iterable[Path]:
    """Get a list of scenarios in the given folder (defaults to scenario directory)."""
    for file in folder.iterdir():
        if file.suffix == ".yaml":
            yield file


def load_scenario_settings_from_file(filepath: str | Path) -> ScenarioConfig:
    """
    Read the scenario settings from a file.

    If only filename is given as a string, the file is read from scenario directory.
    """
    if isinstance(filepath, str):
        filepath = f"{filepath}.yaml" if not filepath.endswith(".yaml") else filepath
        filepath = SCENARIOS_DIR / filepath
    if not filepath.exists():
        error_msg = f"Scenario file '{filepath}' not found."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    with filepath.open("r", encoding="utf-8") as f:
        scenario_config = yaml.safe_load(f)
    if "name" not in scenario_config:
        scenario_config["name"] = filepath.stem
    return ScenarioConfig(**scenario_config)


def get_instance_by_name(session: Session, model, name: str) -> int:  # noqa: ANN001
    """Retrieve database ID for a reference entity by name."""
    entity_id = session.execute(
        select(model.id).where(model.name == name),
    ).scalar_one_or_none()
    if entity_id is None:
        raise ScenarioError(f"'{name}' not found in {model.__name__}.")
    return int(entity_id)


def create_scenario(
    name: str,
    period: str,
    climate: str,
    weather: str,
    sensitivity_id: int | None = None,
) -> int:
    """
    Create a new scenario in the database with given setup.

    Scenario is set up with the provided year and connected to climate, weather, and optional sensitivity identifiers.
    This function associates the given parameters with their corresponding database identifiers,
    creates a new scenario record, and commits it to the database.

    Args:
        name (str): Name to show for scenario
        period (str): The period associated with the scenario.
        climate (str): The name of the climate type for the scenario.
        weather (str): The name of the weather type for the scenario.
        sensitivity_id (int | None): The optional sensitivity identifier for the scenario.

    Returns:
        int: The unique identifier of the created scenario.
        bool: Whether scenario has been created or already existed.

    Raises:
        KeyError: If the specified climate, weather, or period is not found in the database.

    """
    with Session(ENGINE) as session:
        period_id = get_instance_by_name(session, models.Period, period)
        climate_id = get_instance_by_name(session, models.Climate, climate)
        weather_id = get_instance_by_name(session, models.Weather, weather)

        scenario = models.Scenario(
            name=name,
            period_id=period_id,
            weather_id=weather_id,
            climate_id=climate_id,
            sensitivity_id=sensitivity_id,
        )
        session.add(scenario)
        try:
            session.commit()
        except IntegrityError as ie:
            error_msg = f"Scenario {scenario} already exists in database."
            logger.error(error_msg)
            raise ScenarioError(error_msg) from ie

        logger.info(f"Created scenario #{scenario.id} ({scenario}).")
        return scenario.id


def delete_scenario(scenario_id: int | str) -> None:
    """
    Delete a scenario from the database.

    Args:
        scenario_id (int|str): ID or name of the scenario to delete.

    """
    with Session(ENGINE) as session:
        if isinstance(scenario_id, int):
            instance = session.get(models.Scenario, scenario_id)
        else:
            instance = session.execute(
                select(models.Scenario).where(models.Scenario.name == scenario_id),
            ).scalar_one_or_none()
        if instance is None:
            raise ScenarioError(f"Scenario {scenario_id} not found.")
        session.delete(instance)
        session.commit()
    logger.info(f"Scenario #{scenario_id} deleted from database.")


def delete_all_scenarios() -> None:
    """Delete all scenarios from the database."""
    with Session(ENGINE) as session:
        session.query(models.Scenario).delete()
        session.commit()
    logger.info("All scenarios deleted from database.")
