"""Tests for custom facades."""

import pandas as pd
import pytest
from oemof.solph import Bus

from facades.conversion import ConversionMax


def make_converter(max_profile: object) -> ConversionMax:
    return ConversionMax(
        label="heat_lt_central-heat_exchanger",
        from_bus=Bus(label="heat_lt_central"),
        to_bus=Bus(label="heat_central"),
        carrier="heat",
        tech="heat_exchanger",
        capacity=35.0,
        efficiency=0.98,
        max=max_profile,
    )


def test_max_profile_is_set_on_output_flow():
    profile = pd.Series([0.2, 1.0, 0.5])
    converter = make_converter(profile)

    output_flow = converter.outputs[converter.to_bus]
    assert list(output_flow.max) == pytest.approx([0.2, 1.0, 0.5])


def test_missing_max_profile_means_no_limit():
    converter = make_converter(None)

    assert converter.max == 1
    assert list(converter.outputs[converter.to_bus].max) == [1]
