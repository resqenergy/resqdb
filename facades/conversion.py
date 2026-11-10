"""Module to add a conversion facade with an hourly upper limit on its output."""

from collections.abc import Sequence
from dataclasses import field
from typing import Union

from oemof.solph._plumbing import sequence
from oemof.solph.buses import Bus
from oemof.solph.components import Converter
from oemof.solph.flows import Flow

from oemof.tabular._facade import Facade, dataclass_facade


@dataclass_facade
class ConversionMax(Converter, Facade):
    r"""
    Conversion unit with one input and one output and an hourly output limit.

    Parameters
    ----------
    from_bus: oemof.solph.Bus
        An oemof bus instance where the conversion unit is connected to with
        its input.
    to_bus: oemof.solph.Bus
        An oemof bus instance where the conversion unit is connected to with
        its output.
    capacity: numeric
        The conversion capacity (output side) of the unit.
    efficiency: numeric
        Efficiency of the conversion unit (0 <= efficiency <= 1). Default: 1
    marginal_cost: numeric
        Marginal cost for one unit of produced output. Default: 0
    carrier_cost: numeric
        Carrier cost for one unit of used input. Default: 0
    capacity_cost: numeric
        Investment costs per unit of output capacity.
    expandable: boolean or numeric (binary)
        True, if capacity can be expanded within optimization. Default: False.
    capacity_potential: numeric
        Maximum invest capacity in unit of output capacity.
    capacity_minimum: numeric
        Minimum invest capacity in unit of output capacity.
    max: numeric or sequence (optional)
        Hourly upper limit of the output flow as share of the capacity.
        Missing values mean no limit (max = 1).
    input_parameters: dict (optional)
        Set parameters on the input edge of the conversion unit.
    output_parameters: dict (optional)
        Set parameters on the output edge of the conversion unit.

    Examples
    --------
    >>> from oemof import solph
    >>> from facades.conversion import ConversionMax
    >>> lt_bus = solph.Bus(label="heat_lt_central")
    >>> ht_bus = solph.Bus(label="heat_central")
    >>> converter = ConversionMax(
    ...     label="heat_lt_central-heat_exchanger",
    ...     from_bus=heat_lt_central_bus,
    ...     to_bus=heat_central_bus,
    ...     carrier="heat",
    ...     tech="heat_exchanger",
    ...     capacity=35.0,
    ...     efficiency=0.98,
    ...     max=[0.2, 1.0, 0.5],
    ... )

    """

    from_bus: Bus

    to_bus: Bus

    carrier: str

    tech: str

    capacity: float = None

    efficiency: float = 1

    marginal_cost: float = 0

    carrier_cost: float = 0

    capacity_cost: float = None

    expandable: bool = False

    capacity_potential: float = float("+inf")

    capacity_minimum: float = None

    max: Union[float, Sequence[float]] = None

    input_parameters: dict = field(default_factory=dict)

    output_parameters: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Treat a missing max profile as unrestricted output."""
        if self.max is None:
            self.max = 1

    def build_solph_components(self) -> None:
        """Build solph components."""
        self.conversion_factors.update(
            {
                self.from_bus: sequence(1),
                self.to_bus: sequence(self.efficiency),
            },
        )

        self.inputs.update(
            {
                self.from_bus: Flow(
                    variable_costs=self.carrier_cost,
                    **self.input_parameters,
                ),
            },
        )

        self.outputs.update(
            {
                self.to_bus: Flow(
                    nominal_value=self._nominal_value(),
                    variable_costs=self.marginal_cost,
                    investment=self._investment(),
                    max=self.max,
                    **self.output_parameters,
                ),
            },
        )
