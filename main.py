"""Main project script."""

from __future__ import annotations

import argparse
import contextlib
from typing import TYPE_CHECKING

from loguru import logger

from scenarios import ScenarioError

if TYPE_CHECKING:
    from pathlib import Path

import export
import models
import scenarios
import settings
import simulation
import views

NO_ARGS_FCT = ("setup", "nuke")
DB_COMMANDS = ("setup", "nuke", "delete", "views")


def run_all(
    *,
    force_creation: bool = False,
    use_db: bool = True,
    use_files: bool = True,
) -> None:
    """
    Run all scenarios from scenario folder and store results in enabled result stores.

    Args:
        force_creation (bool): Replace existing results in enabled result stores.
        use_db (bool): Store results in database store.
        use_files (bool): Store results in file store.

    """
    for file in scenarios.get_scenarios_in_folder():
        run_scenario(
            file,
            force_creation=force_creation,
            use_db=use_db,
            use_files=use_files,
        )
    if use_db:
        views.create_all_views(recreate=True)


def run_scenario(
    file: str | Path,
    *,
    force_creation: bool = False,
    use_db: bool = True,
    use_files: bool = True,
) -> None:
    """
    Run scenario from scenario folder and store results in enabled result stores.

    Scenarios with existing results are skipped without simulating, unless forced.

    Args:
        file (str | Path): Scenario name or path to scenario file.
        force_creation (bool): Replace existing results in enabled result stores.
        use_db (bool): Store results in database store.
        use_files (bool): Store results in file store.

    """
    scenario_config = scenarios.load_scenario_settings_from_file(file)
    if (
        not use_db
        and not force_creation
        and export.has_results_in_folder(scenario_config.name)
    ):
        logger.warning(
            f"Results for scenario '{scenario_config.name}' already exist. Skipping.",
        )
        return
    if use_db:
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
    if use_files:
        export.store_results_in_folder(
            scenario_config.name,
            output_data,
            overwrite=force_creation,
        )
    if use_db:
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
        run_all(force_creation=args.force, use_db=args.use_db, use_files=args.use_files)
    else:
        run_scenario(
            args.scenario,
            force_creation=args.force,
            use_db=args.use_db,
            use_files=args.use_files,
        )


def handle_views(args: argparse.Namespace) -> None:
    """Handle scenario views."""
    if args.command == "recreate":
        models.update_default_components()
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
    run_parser.add_argument("--no-db", dest="use_db", action="store_false")
    run_parser.add_argument("--no-files", dest="use_files", action="store_false")
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
    if settings.ENGINE is None:
        if args.parser in DB_COMMANDS:
            parser.error("database not configured (set DB_* credentials)")
        if args.parser == "run":
            args.use_db = False
    if args.parser == "run" and not (args.use_db or args.use_files):
        parser.error(
            "no result store enabled: --no-files given, but database store is off",
        )
    if args.parser in NO_ARGS_FCT:
        args.func()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
