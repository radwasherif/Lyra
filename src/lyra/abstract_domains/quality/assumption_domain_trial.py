from lyra.abstract_domains.store import Store
from lyra.abstract_domains.stack import Stack
from lyra.abstract_domains.state import State
from lyra.core.expressions import *
from lyra.abstract_domains.quality.assumption_lattice import AssumptionGraph, AssumptionNode, NumericalAssumption
from lyra.core.types import FloatLyraType, BooleanLyraType, IntegerLyraType, StringLyraType, ListLyraType


class AssumptionState(Stack, State):

    def __init__(self, variables: List[VariableIdentifier]):
        # initialize a stack of assumption graphs
        super().__init__(AssumptionGraph, {})
        self.substates = [NumericalAssumption(variables)]

    def bottom(self):
        for state in self.substates:
            state.bottom()
        return self

    def top(self):
        for state in self.substates:
            state.top()
        return self

    def is_bottom(self) -> bool:
        # for element in self.stack:
        #     if element.is_bottom():
        #         return True
        # return self.map.is_bottom()
        print("IS BOTTOM")

    def is_top(self) -> bool:
        # for element in self.stack:
        #     if not element.is_top():
        #         return False
        # if not self.map.is_top():
        #     return False
        # return True
        print("IS TOP")

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
        # saving loop/if condition on the top layer of the stack
        # used for calculating multiplicity for loops
        self.stack[-1].condition = condition

    def enter_if(self) -> 'State':
        self.push()
        return self

    def exit_if(self) -> 'State':
        self.pop()
        return self

    def enter_loop(self) -> 'State':
        self.push()
        self.stack[-1].is_loop = True
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
        return self

    def push(self):
        self.stack.append(AssumptionGraph().bottom())
        return self

    def pop(self):
        upper = self.stack.pop(-1)
        lower = None
        if len(self.stack) > 0:
            lower = self.stack.pop(-1)
        # combine the two top elements to make one element
        new_top = upper.combine(lower)
        # push new element to top of stack
        self.stack.append(new_top)
        return self

    def handle_input(self, variable: VariableIdentifier):
        assumption = self.map.store[variable]
        assumption.id = self.pp.line
        # add assumption to the top of the stack
        self.stack[-1].add_assumption(assumption)
        # replace the assumption of the variable with top element
        self.map.store[variable].top()
