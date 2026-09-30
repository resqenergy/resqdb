"""Module to run oemof simulations and store results."""

from __future__ import annotations

from loguru import logger
from oemof.solph import EnergySystem, Model, processing
from oemof.tabular import datapackage  # noqa: F401
from oemof.tabular.constraint_facades import CONSTRAINT_TYPE_MAP
from oemof.tabular.facades import TYPEMAP

import hooks
import settings
from facades.heatpump import AquiferHeatpump, FLHHeatpump, Heatpump

RESQ_TYPEMAP = TYPEMAP.copy()
RESQ_TYPEMAP["heatpump"] = Heatpump
RESQ_TYPEMAP["flh_heatpump"] = FLHHeatpump
RESQ_TYPEMAP["aquifer_heatpump"] = AquiferHeatpump


def simulate_datapackage(
    datapackage_name: str,
    parameters: dict | None = None,
) -> tuple[dict, dict]:
    """
    Simulate a data package and return results.

    This function loads JSON definition, builds an energy system,
    adds constraints, and solves it using the specified solver. Returns the results
    of the simulation as a dictionary.

    Args:
        datapackage_name (str): The name of the data package folder, which contains
            a `datapackage.json` file. This file defines the energy system structure,
            constraints, and other necessary components for the simulation.
        parameters (dict or None): A dictionary containing parameter values to adapt ES components; defaults to None

    Returns:
        dict: The simulation results, containing outputs such as optimized values
            or any other data produced after solving the system.

    """
    datapackage_json = str(
        settings.DATAPACKAGE_DIR / datapackage_name / "datapackage.json",
    )
    es = EnergySystem.from_datapackage(datapackage_json, typemap=RESQ_TYPEMAP)

    # Adapt ES from parameters
    parameters = parameters or {}
    es = hooks.adapt_energysystem(es, parameters)

    logger.info("Building model...")
    m = Model(es)
    m.add_constraints_from_datapackage(
        datapackage_json,
        constraint_type_map=CONSTRAINT_TYPE_MAP,
    )
    logger.info("Solving model...")
    m.solve("cbc")
    logger.info("Model solved.")

    input_data = processing.parameter_as_dict(
        es,
        exclude_attrs=["bus", "from_bus", "to_bus", "from_node", "to_node"],
    )
    output_data = m.results()
    return input_data, output_data


if __name__ == "__main__":
    results_ = simulate_datapackage(settings.OEMOF_SCENARIO)
