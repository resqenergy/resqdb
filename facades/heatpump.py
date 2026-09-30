"""Thius module adds custom heatpumps to oemof."""

from dataclasses import field
from typing import Union
from collections.abc import Iterable, Sequence
import pandas as pd

from oemof.solph._plumbing import sequence
from oemof.solph.buses import Bus
from oemof.solph.components import Converter
from oemof.solph.flows import Flow

from oemof.tabular._facade import Facade, dataclass_facade


@dataclass_facade
class Heatpump(Converter, Facade):
    r"""
    Conversion unit with one input and one output.

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
        If capacity is not set, this value will be used for optimizing the
        conversion output capacity.
    expandable: boolean or numeric (binary)
        True, if capacity can be expanded within optimization. Default: False.
    capacity_potential: numeric
        Maximum invest capacity in unit of output capacity.
    capacity_minimum: numeric
        Minimum invest capacity in unit of output capacity.
    input_parameters: dict (optional)
        Set parameters on the input edge of the conversion unit
        (see oemof.solph for more information on possible parameters)
    ouput_parameters: dict (optional)
        Set parameters on the output edge of the conversion unit
         (see oemof.solph for more information on possible parameters)


    .. math::
        x^{flow, from}(t) \cdot c^{efficiency}(t) = x^{flow, to}(t)
        \qquad \forall t \in T

    **Objective expression** for operation includes marginal cost and/or
    carrier costs:

        .. math::

            x^{opex} =  \sum_t (x^{flow, out}(t) \cdot c^{marginal\_cost}(t)
            + x^{flow, carrier}(t) \cdot c^{carrier\_cost}(t))


    Examples
    --------
    >>> from oemof import solph
    >>> from oemof.tabular import facades
    >>> my_biomass_bus = solph.Bus('my_biomass_bus')
    >>> my_heat_bus = solph.Bus('my_heat_bus')
    >>> my_conversion = Heatpump(
    ...     label='biomass_plant',
    ...     carrier='biomass',
    ...     tech='st',
    ...     from_bus=my_biomass_bus,
    ...     to_bus=my_heat_bus,
    ...     capacity=100,
    ...     efficiency=0.4)

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

    low_temperature_potential: Union[float, Sequence[float]] = None

    input_parameters: dict = field(default_factory=dict)

    output_parameters: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Turn efficiency into a series if it is a scalar or a list."""
        self.efficiency = pd.Series(self.efficiency)
        minimum_cop = self.efficiency.min()
        if minimum_cop < 1:
            raise ValueError(
                f"COP of '{self.label}' must be greater than 1, but the minimum is {minimum_cop}.",
            )

    def build_solph_components(self) -> None:
        """Build solph components."""
        self.conversion_factors.update(
            {
                self.from_bus: sequence(1 / self.efficiency),
                self.to_bus: sequence(1),
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
                    max=self.low_temperature_potential
                    / ((self.efficiency - 1) / self.efficiency),
                    **self.output_parameters,
                ),
            },
        )


@dataclass_facade
class FLHHeatpump(Converter, Facade):
    r"""
    Conversion unit with one input and one output.

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
        If capacity is not set, this value will be used for optimizing the
        conversion output capacity.
    expandable: boolean or numeric (binary)
        True, if capacity can be expanded within optimization. Default: False.
    capacity_potential: numeric
        Maximum invest capacity in unit of output capacity.
    capacity_minimum: numeric
        Minimum invest capacity in unit of output capacity.
    input_parameters: dict (optional)
        Set parameters on the input edge of the conversion unit
        (see oemof.solph for more information on possible parameters)
    ouput_parameters: dict (optional)
        Set parameters on the output edge of the conversion unit
         (see oemof.solph for more information on possible parameters)


    .. math::
        x^{flow, from}(t) \cdot c^{efficiency}(t) = x^{flow, to}(t)
        \qquad \forall t \in T

    **Objective expression** for operation includes marginal cost and/or
    carrier costs:

        .. math::

            x^{opex} =  \sum_t (x^{flow, out}(t) \cdot c^{marginal\_cost}(t)
            + x^{flow, carrier}(t) \cdot c^{carrier\_cost}(t))


    Examples
    --------
    >>> from oemof import solph
    >>> from oemof.tabular import facades
    >>> my_biomass_bus = solph.Bus('my_biomass_bus')
    >>> my_heat_bus = solph.Bus('my_heat_bus')
    >>> my_conversion = Heatpump(
    ...     label='biomass_plant',
    ...     carrier='biomass',
    ...     tech='st',
    ...     from_bus=my_biomass_bus,
    ...     to_bus=my_heat_bus,
    ...     capacity=100,
    ...     efficiency=0.4)

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

    full_load_time_max: float = None

    input_parameters: dict = field(default_factory=dict)

    output_parameters: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Turn efficiency into a series if it is a scalar or a list."""
        self.efficiency = pd.Series(self.efficiency)
        minimum_cop = self.efficiency.min()
        if minimum_cop < 1:
            raise ValueError(
                f"COP of '{self.label}' must be greater than 1, but the minimum is {minimum_cop}.",
            )

    def build_solph_components(self) -> None:
        """Build solph components."""
        self.conversion_factors.update(
            {
                self.from_bus: sequence(1 / self.efficiency),
                self.to_bus: sequence(1),
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
                    full_load_time_max=self.full_load_time_max,
                    **self.output_parameters,
                ),
            },
        )


@dataclass_facade
class AquiferHeatpump(Converter, Facade):
    r"""
    Aquifer heatpump with two inputs (electricity and aquifer heat) and one heat output.

    The heatpump lifts low temperature heat from an aquifer to the temperature
    level of a heat bus, driven by electricity. All three flows are coupled by
    the coefficient of performance (COP), so the aquifer heat is not a free
    parameter but follows from the electricity input.

    Parameters
    ----------
    electricity_bus: oemof.solph.Bus
        An oemof bus instance where the heatpump is connected to with its
        electricity input.
    aquifer_bus: oemof.solph.Bus
        An oemof bus instance where the heatpump is connected to with its
        low temperature heat input. The available aquifer potential is limited
        by the component feeding this bus, not by the heatpump itself.
    heat_bus: oemof.solph.Bus
        An oemof bus instance where the heatpump is connected to with its
        heat output.
    cop: numeric or sequence of numeric
        Coefficient of performance of the heatpump, either a scalar or a time
        series. Must be greater than 1, otherwise no heat is drawn from the
        aquifer.
    capacity: numeric
        The electrical capacity of the heatpump (e.g. in MW_el).
    marginal_cost: numeric
        Marginal cost for one unit of produced heat (e.g. in Euro / MWh_th).
        Default: 0
    carrier_cost: numeric
        Carrier cost for one unit of used electricity
        (e.g. in Euro / MWh_el). Default: 0
    capacity_cost: numeric
        Investment costs per unit of electrical capacity
        (e.g. in Euro / MW_el). If capacity is not set, this value will be used
        for optimizing the electrical capacity.
    expandable: boolean or numeric (binary)
        True, if capacity can be expanded within optimization. Default: False.
    capacity_potential: numeric
        Maximum invest capacity in unit of electrical capacity.
    capacity_minimum: numeric
        Minimum invest capacity in unit of electrical capacity.
    electricity_input_parameters: dict (optional)
        Set parameters on the electricity input edge of the heatpump
        (see oemof.solph for more information on possible parameters)
    aquifer_input_parameters: dict (optional)
        Set parameters on the aquifer input edge of the heatpump
        (see oemof.solph for more information on possible parameters)
    output_parameters: dict (optional)
        Set parameters on the heat output edge of the heatpump
        (see oemof.solph for more information on possible parameters)


    .. math::
        x^{flow, heat}(t) = c^{COP}(t) \cdot x^{flow, electricity}(t)
        \qquad \forall t \in T

    .. math::
        x^{flow, aquifer}(t) = (c^{COP}(t) - 1) \cdot
        x^{flow, electricity}(t) \qquad \forall t \in T

    **Objective expression** for operation includes marginal cost and/or
    carrier costs:

        .. math::

            x^{opex} =  \sum_t (x^{flow, heat}(t) \cdot c^{marginal\_cost}(t)
            + x^{flow, electricity}(t) \cdot c^{carrier\_cost}(t))


    Examples
    --------
    >>> from oemof import solph
    >>> from facades.heatpump import AquiferHeatpump
    >>> my_electricity_bus = solph.Bus('my_electricity_bus')
    >>> my_aquifer_bus = solph.Bus('my_aquifer_bus')
    >>> my_heat_bus = solph.Bus('my_heat_bus')
    >>> my_heatpump = AquiferHeatpump(
    ...     label='aquifer_heatpump',
    ...     carrier='electricity',
    ...     tech='hp',
    ...     electricity_bus=my_electricity_bus,
    ...     aquifer_bus=my_aquifer_bus,
    ...     heat_bus=my_heat_bus,
    ...     capacity=100,
    ...     cop=4.0)

    """

    electricity_bus: Bus

    aquifer_bus: Bus

    heat_bus: Bus

    carrier: str

    tech: str

    cop: Union[float, Sequence[float]]

    capacity: float = None

    marginal_cost: float = 0

    carrier_cost: float = 0

    capacity_cost: float = None

    expandable: bool = False

    capacity_potential: float = float("+inf")

    capacity_minimum: float = None

    electricity_input_parameters: dict = field(default_factory=dict)

    aquifer_input_parameters: dict = field(default_factory=dict)

    output_parameters: dict = field(default_factory=dict)

    def build_solph_components(self) -> None:
        """Build solph components."""
        cop_is_series = isinstance(self.cop, Iterable)
        cop_values = list(self.cop) if cop_is_series else [self.cop]
        minimum_cop = min(cop_values)
        if minimum_cop <= 1:
            raise ValueError(
                f"COP of '{self.label}' must be greater than 1, but the minimum is {minimum_cop}.",
            )

        # Scalars must stay scalars: solph turns them into an endless sequence,
        # while a list of length one would only cover the first time step.
        heat_efficiency = cop_values if cop_is_series else self.cop
        aquifer_efficiency = (
            [cop - 1 for cop in cop_values] if cop_is_series else self.cop - 1
        )

        self.conversion_factors.update(
            {
                self.electricity_bus: sequence(1),
                self.aquifer_bus: sequence(aquifer_efficiency),
                self.heat_bus: sequence(heat_efficiency),
            },
        )

        self.inputs.update(
            {
                self.electricity_bus: Flow(
                    nominal_value=self._nominal_value(),
                    investment=self._investment(),
                    variable_costs=self.carrier_cost,
                    **self.electricity_input_parameters,
                ),
                self.aquifer_bus: Flow(
                    **self.aquifer_input_parameters,
                ),
            },
        )

        self.outputs.update(
            {
                self.heat_bus: Flow(
                    variable_costs=self.marginal_cost,
                    **self.output_parameters,
                ),
            },
        )
