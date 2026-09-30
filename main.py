"""Main project script."""

from __future__ import annotations

import argparse
import contextlib
from typing import TYPE_CHECKING

from scenarios import ScenarioError

if TYPE_CHECKING:
    from pathlib import Path

import export
import models
import scenarios
import simulation
import views

NO_ARGS_FCT = ("setup", "nuke")


def run_all(*, force_creation: bool = False) -> None:
    """Run all scenarios store results in the database."""
    for file in scenarios.get_scenarios_in_folder():
        run_scenario(file, force_creation=force_creation)
    views.create_all_views(recreate=True)


def run_scenario(file: str | Path, *, force_creation: bool = False) -> None:
    """Run scenario from scenario folder."""
    scenario_config = scenarios.load_scenario_settings_from_file(file)
    if force_creation:
        with contextlib.suppress(ScenarioError):
            scenarios.delete_scenario(scenario_config.name)
    try:
        scenario_id = scenarios.create_scenario(
            scenario_config.name,
            **scenario_config.scenario,
        )
    except ScenarioError:
        return
    input_data, output_data = simulation.simulate_datapackage(
        scenario_config.datapackage,
        scenario_config.capacities,
    )
    export.store_results_in_folder(str(file), output_data)
    export.store_scenario_results(scenario_id, input_data, output_data)


def handle_delete(args: argparse.Namespace) -> None:
    """Handle scenario deletion."""
    if args.id == "all":
        scenarios.delete_all_scenarios()
    else:
        scenarios.delete_scenario(int(args.id))


def handle_run(args: argparse.Namespace) -> None:
    """Handle scenario runs."""
    if args.scenario == "all":
        run_all(force_creation=args.force)
    else:
        run_scenario(args.scenario, force_creation=args.force)


def handle_views(args: argparse.Namespace) -> None:
    """Handle scenario views."""
    if args.command == "recreate":
        models.update_default_labels()
        models.update_default_categories()
        models.update_cluster_components()
        views.create_all_views(recreate=True)
    elif args.command == "drop":
        views.delete_all_views()


def main() -> None:
    """
    Parse command-line arguments to execute database setup or teardown operations.

    This function defines a command-line interface (CLI) for managing a database
    through three primary commands: `setup`, `nuke`, and `delete`. The `setup`
    command prepares the database configuration and initialization, the `nuke`
    command handles the teardown and removal of all database resources, and the
    `delete` command allows deleting specific scenarios or all of them.

    Raises:
        SystemExit: Raised implicitly by `argparse` when invalid arguments are
            provided or if the help message is displayed.

    """
    parser = argparse.ArgumentParser(
        prog="resq",
        description="Commands for resqdb",
    )

    subparsers = parser.add_subparsers(dest="parser", required=True)

    # DB setup command
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("scenario", nargs="?", default="all")
    run_parser.add_argument("-f", "--force", action="store_true")
    run_parser.set_defaults(func=handle_run)

    # DB setup command
    setup_parser = subparsers.add_parser("setup")
    setup_parser.set_defaults(func=models.setup_db)

    # DB nuke command
    nuke_parser = subparsers.add_parser("nuke")
    nuke_parser.set_defaults(func=models.teardown_db)

    # DB delete command
    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("id", nargs="?", default="all")
    delete_parser.set_defaults(func=handle_delete)

    # DB views command
    view_parser = subparsers.add_parser("views")
    view_parser.add_argument("command", nargs="?", default="recreate")
    view_parser.set_defaults(func=handle_views)

    args = parser.parse_args()
    if args.parser in NO_ARGS_FCT:
        args.func()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
