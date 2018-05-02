from typing import List

from lyra.abstract_domains.numerical.interval_domain import IntervalLattice
from lyra.abstract_domains.quality.assumption_lattice_m import AssumptionLattice, TypeLattice
from lyra.abstract_domains.store import Store
from lyra.abstract_domains.quality.assumption import AssumptionState
from lyra.core.expressions import Expression, VariableIdentifier, LengthIdentifier
from lyra.abstract_domains.quality.assumption_domain_m import InputAssumptionStack
from lyra.abstract_domains.numerical.octagon_d import OctagonDomain
from lyra.core.types import FloatLyraType, StringLyraType, ListLyraType, BooleanLyraType, IntegerLyraType


class NumericalAssumptionState(Store, AssumptionState):

    def __init__(self, variables: List[VariableIdentifier]):
        types = [BooleanLyraType, IntegerLyraType, FloatLyraType, StringLyraType, ListLyraType]
        lattices = {typ: AssumptionLattice for typ in types}
        super().__init__(variables, lattices)
        self.variables = variables
        input_assumption_collector = InputAssumptionStack()
        relations_collector = OctagonDomain(variables)
        self.collector_pairs.append((input_assumption_collector, relations_collector))
        # boolean is initialized as interval [0,1]
        for var in [v for v in variables if v.typ == BooleanLyraType()]:
            self.store[var].range_assumption.meet(IntervalLattice(0, 1))
        # length variables initialized to [0, inf]
        for var in [v for v in variables if isinstance(v, LengthIdentifier)]:
            self.store[var].type_assumption.meet(TypeLattice().integer())
            self.store[var].range_assumption.meet(IntervalLattice(0))

    def transfer_relations(self, variable):
        pass

    def _assign(self, left: Expression, right: Expression) -> 'State':
        pass

    def _assume(self, condition: Expression) -> 'State':
        for input_collector, relations_collector in self.collector_pairs:
            input_collector.assume(condition)
            relations_collector.assume(condition)


    def enter_if(self) -> 'State':
        pass

    def exit_if(self) -> 'State':
        pass

    def enter_loop(self) -> 'State':
        pass

    def exit_loop(self) -> 'State':
        pass

    def _output(self, output: Expression) -> 'State':
        pass

    def raise_error(self) -> 'State':
        pass

    def _substitute(self, left: Expression, right: Expression) -> 'State':
        pass

    def bottom(self):
        pass

    def top(self):
        pass

    def is_bottom(self) -> bool:
        pass

    def is_top(self) -> bool:
        pass

    def _less_equal(self, other: 'Lattice') -> bool:
        pass

    def _join(self, other: 'Lattice') -> 'Lattice':
        pass

    def _meet(self, other: 'Lattice'):
        pass

    def _widening(self, other: 'Lattice'):
        pass

