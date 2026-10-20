"""Tests for running scenarios via main module."""

from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

import main
import models
import scenarios
import settings
import simulation
import views


@pytest.fixture(autouse=True)
def no_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unbind every module from the configured DB, so no test can touch a real database."""
    for module in (settings, models, scenarios, views):
        monkeypatch.setattr(module, "ENGINE", None)
    monkeypatch.setattr(settings, "DATABASE_URL", None)
    monkeypatch.setattr(settings, "DB_CONFIG_ERROR", None)


@pytest.fixture
def file_store_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect results to tmp folder and return path to a scenario file."""
    monkeypatch.setattr(settings, "RESULTS_DIR", tmp_path / "results")
    (tmp_path / "results").mkdir()
    scenario_file = tmp_path / "my_scenario.yaml"
    scenario_file.write_text(
        "scenario: {period: p, climate: c, weather: w}\ndatapackage: dp\n",
        encoding="utf-8",
    )
    return scenario_file


def fake_simulation(flow: float) -> Callable[[str, dict], tuple[dict, dict]]:
    """Return fake simulation, yielding a single flow with given value."""

    def simulate(_datapackage: str, _capacities: dict) -> tuple[dict, dict]:
        output = {
            ("pv", "bus"): {
                "scalars": pd.Series(dtype=float),
                "sequences": pd.DataFrame({"flow": [flow]}),
            },
        }
        return {}, output

    return simulate


def read_flow(results_dir: Path) -> float:
    """Read flow value from written results."""
    sequences = pd.read_csv(
        results_dir / "my_scenario" / "pv-bus-sequences.csv",
        sep=";",
    )
    return float(sequences["flow"].iloc[0])


def fail_simulation(_datapackage: str, _capacities: dict) -> tuple[dict, dict]:
    """Fail test if simulation is called."""
    pytest.fail("Simulation must not run.")


def test_file_store_writes_results_into_scenario_folder(
    file_store_only: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Results are stored in a folder named after the scenario, without touching the DB."""
    monkeypatch.setattr(simulation, "simulate_datapackage", fake_simulation(1.0))

    main.run_scenario(file_store_only, use_db=False)

    assert read_flow(settings.RESULTS_DIR) == 1.0


def test_force_overwrites_file_store(
    file_store_only: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Existing results are kept without re-simulating, unless run is forced."""
    monkeypatch.setattr(simulation, "simulate_datapackage", fake_simulation(1.0))
    main.run_scenario(file_store_only, use_db=False)

    monkeypatch.setattr(simulation, "simulate_datapackage", fail_simulation)
    main.run_scenario(file_store_only, use_db=False)
    assert read_flow(settings.RESULTS_DIR) == 1.0

    forced_flow = 3.0
    monkeypatch.setattr(
        simulation,
        "simulate_datapackage",
        fake_simulation(forced_flow),
    )
    main.run_scenario(file_store_only, use_db=False, force_creation=True)
    assert read_flow(settings.RESULTS_DIR) == forced_flow


def run_cli(monkeypatch: pytest.MonkeyPatch, *args: str) -> None:
    """Run CLI with given arguments."""
    monkeypatch.setattr("sys.argv", ["resq", *args])
    main.main()


def test_cli_run_without_db_uses_file_store(
    file_store_only: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without DB credentials, database store is disabled automatically."""
    monkeypatch.setattr(simulation, "simulate_datapackage", fake_simulation(1.0))

    run_cli(monkeypatch, "run", str(file_store_only))

    assert read_flow(settings.RESULTS_DIR) == 1.0


@pytest.mark.parametrize(
    ("engine", "args"),
    [
        (None, ["run", "--no-files"]),
        (object(), ["run", "--no-db", "--no-files"]),
    ],
)
def test_cli_run_without_result_store_fails_before_simulation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    engine: object,
    args: list[str],
) -> None:
    """A run without any result store is rejected before simulating."""
    monkeypatch.setattr(settings, "ENGINE", engine)
    monkeypatch.setattr(simulation, "simulate_datapackage", fail_simulation)

    with pytest.raises(SystemExit):
        run_cli(monkeypatch, *args)

    assert "no result store" in capsys.readouterr().err


@pytest.mark.parametrize("command", ["setup", "nuke", "delete", "views"])
def test_cli_db_commands_fail_without_db(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    command: str,
) -> None:
    """DB-only commands fail with a clear message if no database is configured."""
    with pytest.raises(SystemExit):
        run_cli(monkeypatch, command)

    assert "database not configured" in capsys.readouterr().err


@pytest.fixture
def incomplete_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate partially set DB credentials."""
    monkeypatch.setattr(
        settings,
        "DB_CONFIG_ERROR",
        "Incomplete DB credentials, missing: DB_USER",
    )


@pytest.mark.usefixtures("incomplete_credentials")
def test_cli_no_db_ignores_incomplete_credentials(
    file_store_only: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Incomplete DB credentials do not matter if the database store is disabled."""
    monkeypatch.setattr(simulation, "simulate_datapackage", fake_simulation(1.0))

    run_cli(monkeypatch, "run", str(file_store_only), "--no-db")

    assert read_flow(settings.RESULTS_DIR) == 1.0


@pytest.mark.usefixtures("incomplete_credentials")
@pytest.mark.parametrize("args", [["run"], ["views"]])
def test_cli_incomplete_credentials_fail_if_db_is_used(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    args: list[str],
) -> None:
    """Incomplete DB credentials are reported instead of silently falling back to files."""
    monkeypatch.setattr(simulation, "simulate_datapackage", fail_simulation)

    with pytest.raises(SystemExit):
        run_cli(monkeypatch, *args)

    assert "missing: DB_USER" in capsys.readouterr().err
