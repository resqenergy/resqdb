"""Tests for config files."""

import csv

import pytest

from settings import COMPONENTS, DATAPACKAGE_DIR

BUS_FILES = sorted(DATAPACKAGE_DIR.glob("*/data/elements/bus.csv"))


@pytest.mark.skipif(not BUS_FILES, reason="No datapackages available")
def test_datapackage_buses_have_bus_role() -> None:
    """Buses defined in datapackages must have role 'bus', otherwise flow labels fall back to the bus label."""
    buses = set()
    for bus_file in BUS_FILES:
        with bus_file.open(encoding="utf-8") as csv_file:
            dialect = csv.Sniffer().sniff(csv_file.readline(), delimiters=",;")
            csv_file.seek(0)
            buses |= {row["name"] for row in csv.DictReader(csv_file, dialect=dialect)}

    wrong_role = sorted(
        bus
        for bus in buses
        if bus in COMPONENTS and COMPONENTS[bus].get("role") != "bus"
    )

    assert wrong_role == []
