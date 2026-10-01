"""Tests for SQL views and the SQL functions they depend on."""

from pathlib import Path

import pytest
from sqlalchemy import Connection, text

import views

SCENARIO_DIMENSIONS = {
    "scenario_id",
    "scenario_name",
    "climate_name",
    "period_name",
    "weather_name",
    "sensitivity",
}
EXCLUDED_CAPACITY_ROLES = ("excess", "shortage", "import", "export")


def create_temp_view(connection: Connection, view_name: str) -> str:
    """
    Create a temporary view from a view file, so the query can be tested without touching materialized views.

    Args:
        connection: Connection with an open transaction.
        view_name: Stem of the SQL file in the views folder.

    Returns:
        Name of the temporary view.

    """
    temp_view_name = f"test_{view_name}"
    query = views.read_query(views.VIEWS_DIR / f"{view_name}.sql")
    connection.execute(text(f"CREATE TEMP VIEW {temp_view_name} AS ({query})"))
    return temp_view_name


def test_read_query_strips_only_trailing_semicolon(tmp_path: Path) -> None:
    """Semicolons inside the query are kept, only the trailing one is removed."""
    view_file = tmp_path / "view.sql"
    view_file.write_text("SELECT ';' AS separator;\n", encoding="utf-8")

    assert views.read_query(view_file) == "SELECT ';' AS separator"


@pytest.mark.parametrize(
    ("from_node", "to_node", "expected"),
    [
        ("test_bus", "test_component", "Test Component"),
        ("test_component", "test_bus", "Test Component"),
        ("test_bus", "test_unlabeled", "test_unlabeled"),
        ("test_unlabeled", "test_bus", "test_unlabeled"),
    ],
)
def test_flow_label(
    db_connection: Connection,
    from_node: str,
    to_node: str,
    expected: str,
) -> None:
    """Flow label prefers the non-bus component, also when falling back to the raw node name."""
    db_connection.execute(
        text(
            "INSERT INTO component (component, label, role) VALUES "
            "('test_bus', 'Test Bus', 'bus'), ('test_component', 'Test Component', NULL)",
        ),
    )

    label = db_connection.execute(
        text("SELECT flow_label(:from_node, :to_node)"),
        {"from_node": from_node, "to_node": to_node},
    ).scalar_one()

    assert label == expected


@pytest.mark.parametrize(
    "view_path",
    sorted(views.get_views()),
    ids=lambda path: path.stem,
)
def test_view_exposes_scenario_dimensions(
    db_connection: Connection,
    view_path: Path,
) -> None:
    """Every view can be created and exposes all scenario dimensions for filtering in Superset."""
    temp_view_name = create_temp_view(db_connection, view_path.stem)

    columns = set(
        db_connection.execute(text(f"SELECT * FROM {temp_view_name} LIMIT 0")).keys(),
    )

    assert columns >= SCENARIO_DIMENSIONS


def test_cluster_map_geojson_properties_is_object(db_connection: Connection) -> None:
    """GeoJSON properties must be a JSON object, not the string '{}'."""
    temp_view_name = create_temp_view(db_connection, "cluster_energies_map")

    property_types = db_connection.execute(
        text(
            f"SELECT DISTINCT jsonb_typeof(geojson::jsonb -> 'properties') FROM {temp_view_name}",
        ),
    ).scalars()

    assert set(property_types) <= {"object"}


@pytest.mark.parametrize(
    "view_name",
    ["cluster_energies", "cluster_energies_map", "capacities"],
)
def test_view_exposes_carrier(db_connection: Connection, view_name: str) -> None:
    """Views must not mix carriers, so carrier has to be exposed."""
    temp_view_name = create_temp_view(db_connection, view_name)

    columns = set(
        db_connection.execute(text(f"SELECT * FROM {temp_view_name} LIMIT 0")).keys(),
    )

    assert "carrier" in columns


def test_capacities_exclude_roles(db_connection: Connection) -> None:
    """Capacities of excess, shortage, import and export components are not shown."""
    temp_view_name = create_temp_view(db_connection, "capacities")

    excluded = db_connection.execute(
        text(
            f"SELECT DISTINCT capacities.label FROM {temp_view_name} AS capacities "
            "JOIN component ON component.label = capacities.label WHERE component.role IN :roles",
        ).bindparams(roles=EXCLUDED_CAPACITY_ROLES),
    ).scalars()

    assert list(excluded) == []


def test_capacities_prefer_results_over_inputs(db_connection: Connection) -> None:
    """Input capacities (without carrier) are not shown next to result capacities of the same component."""
    db_connection.execute(
        text(
            "INSERT INTO component (component, label, role) VALUES "
            "('test_bus', 'Test Bus', 'bus'), ('test_component', 'Test Component', NULL);"
            "INSERT INTO category (from_node, to_node, category, carrier, is_renewable) VALUES "
            "('test_component', 'test_bus', 'Erzeugung', 'test_carrier', false);"
            "INSERT INTO scalar (scenario_id, is_exogenous, from_node, to_node, attribute, value) "
            "SELECT id, true, 'test_component', NULL, 'capacity', 1 FROM scenario LIMIT 1;"
            "INSERT INTO scalar (scenario_id, is_exogenous, from_node, to_node, attribute, value) "
            "SELECT id, false, 'test_component', 'test_bus', 'total', 2 FROM scenario LIMIT 1;",
        ),
    )
    temp_view_name = create_temp_view(db_connection, "capacities")

    rows = db_connection.execute(
        text(
            f"SELECT carrier, capacity FROM {temp_view_name} WHERE label = 'Test Component'",
        ),
    ).all()

    assert rows == [("test_carrier", 2)]


def test_energy_flows_use_directional_labels(db_connection: Connection) -> None:
    """Components with directional labels use label_out as source and label_in as target in energy flows."""
    temp_view_name = create_temp_view(db_connection, "energy_flows")

    mismatches = db_connection.execute(
        text(
            f"SELECT energy_flows.from_node, energy_flows.to_node FROM {temp_view_name} AS energy_flows "
            "LEFT JOIN component AS source ON source.component = energy_flows.from_node "
            "LEFT JOIN component AS target ON target.component = energy_flows.to_node "
            "WHERE energy_flows.from_label IS DISTINCT FROM "
            "COALESCE(source.label_out, source.label, energy_flows.from_node) "
            "OR energy_flows.to_label IS DISTINCT FROM COALESCE(target.label_in, target.label, energy_flows.to_node)",
        ),
    ).all()

    assert mismatches == []


def test_all_nodes_have_component_label(db_connection: Connection) -> None:
    """Every node in results and inputs has an entry in component.json."""
    missing = db_connection.execute(
        text(
            "SELECT DISTINCT node FROM ("
            "  SELECT from_node AS node FROM scalar UNION SELECT to_node FROM scalar"
            "  UNION SELECT from_node FROM sequence UNION SELECT to_node FROM sequence"
            ") AS nodes "
            "WHERE node IS NOT NULL AND NOT EXISTS (SELECT 1 FROM component WHERE component.component = nodes.node) "
            "ORDER BY node",
        ),
    ).scalars()

    assert list(missing) == []


def test_all_flows_have_category(db_connection: Connection) -> None:
    """Every flow (and every capacity) between two nodes has an entry in categories.json."""
    missing = db_connection.execute(
        text(
            "SELECT DISTINCT from_node, to_node FROM ("
            "  SELECT from_node, to_node FROM sequence WHERE attribute = 'flow'"
            "  UNION SELECT from_node, to_node FROM scalar WHERE attribute IN ('capacity', 'total')"
            ") AS flows "
            "WHERE to_node IS NOT NULL AND NOT EXISTS ("
            "  SELECT 1 FROM category WHERE category.from_node = flows.from_node AND category.to_node = flows.to_node"
            ") ORDER BY from_node, to_node",
        ),
    ).all()

    assert missing == []
