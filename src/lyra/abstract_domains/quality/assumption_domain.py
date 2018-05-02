from lyra.abstract_domains.store import Store
from lyra.abstract_domains.stack import Stack
from lyra.abstract_domains.state import State
from lyra.core.expressions import *
from lyra.abstract_domains.quality.assumption_lattice import AssumptionGraph, Assumption
from lyra.core.types import FloatLyraType, BooleanLyraType, IntegerLyraType, StringLyraType, ListLyraType

class AssumptionState(State, Stack):

    def __init__(self, variables: List[VariableIdentifier]):
        # initialize a stack of assumption graphs
        super().__init__(AssumptionGraph, {})
        types = [BooleanLyraType, IntegerLyraType, FloatLyraType, StringLyraType, ListLyraType]
        lattices = {typ: Assumption for typ in types}
        self.variables = variables
        self.map = Store(variables, lattices)

    def bottom(self):
        for element in self.stack:
            element.bottom()
        self.map.bottom()
        return self


    def top(self):
        for element in self.stack:
            element.top()
        self.map.top()

        return self

    def is_bottom(self) -> bool:
        for element in self.stack:
            if element.is_bottom():
                return True
        return self.map.is_bottom()


    def is_top(self) -> bool:
        for element in self.stack:
            if not element.is_top():
                return False
        if not self.map.is_top():
            return False
        return True

    def _less_equal(self, other: 'AssumptionState') -> bool:
        return self.less_equal(other) and self.map.less_equal(other.map)


    def _join(self, other: 'AssumptionState') -> 'AssumptionState':
        self.map.join(other.map)
        self.join(other)
        return self

    def _meet(self, other: 'AssumptionState'):
        self.map.meet(other.map)
        self.meet(other)
        return self

    def _widening(self, other: 'AssumptionState'):
        self.map.widening(other.map)
        self.widening(other)
        return self

    def _assign(self, left: Expression, right: Expression) -> 'State':
        raise Exception("Assign should not be called in backward analysis")

    def _assume(self, condition: Expression) -> 'State':
        # get all variables included in this condition
        variable_ids = condition.ids()
        # assume the condition on the mapping of every one of these variables
        # the validity of the condition is checked inside the assumption function
        for var in variable_ids:
            self.map.store[var].assume(condition)

    def enter_if(self) -> 'State':
        self.push()
        return self

    def exit_if(self) -> 'State':
        self.pop()
        return self

    def enter_loop(self) -> 'State':
        self.push()
        return self

    def exit_loop(self) -> 'State':
        self.pop()
        return self

    def _output(self, output: Expression) -> 'State':
        pass

    def raise_error(self) -> 'State':
        self.bottom()
        return self

    def _substitute(self, left: Expression, right: Expression) -> 'State':
        if isinstance(right, Input):
            self.handle_input(left)
        else:
            self.map.store[left].substitue(left, right)

    def push(self):
        self.stack.append(AssumptionGraph().bottom())

    def pop(self):
        top = self.stack.pop(-1)
        second_top = self.stack.pop(-1)
        new_top = top.collapse(second_top)
        self.stack.append(new_top)

    def handle_input(self, variable: VariableIdentifier):
        assumption = self.map.store[variable]
        assumption.id = self.pp.line
        self.stack.append(assumption)