from lyra.abstract_domains.numerical.interval_domain import IntervalState
from lyra.abstract_domains.store import Store
from lyra.abstract_domains.stack import Stack
from lyra.abstract_domains.state import State
from lyra.core.expressions import *
from lyra.abstract_domains.quality.assumption_lattice import AssumptionGraph, Assumption, NumericalAssumption, StringAssumption
from lyra.core.types import FloatLyraType, BooleanLyraType, IntegerLyraType, StringLyraType, ListLyraType


class AssumptionState(Stack, State):

    def __init__(self, variables: List[VariableIdentifier]):
        # initialize a stack of assumption graphs
        super().__init__(AssumptionGraph, {})
        self.types = [BooleanLyraType, IntegerLyraType, FloatLyraType, StringLyraType, ListLyraType]
        lattices = {typ: NumericalAssumption if typ != StringLyraType else StringAssumption for typ in self.types}
        substates = {typ: NumericalAssumption if typ != StringLyraType else StringAssumption for typ in self.types}
        self.variables = variables
        self.map = Store(variables, lattices)
        print(self.map.store.values())
        self.substates = {
            BooleanLyraType: NumericalAssumptionState(variables),
            IntegerLyraType: NumericalAssumptionState(variables),
            FloatLyraType: NumericalAssumptionState(variables),
            ListLyraType: NumericalAssumptionState(variables),
            StringLyraType: StringAssumptionState(variables)
        }

    def bottom(self):
        for element in self.stack:
            element.bottom()
        for state in self.substates.values():
            print("YOO")
            state.bottom()

        print(self.map.store.values())
        self.propagate_up()
        print("Bottom")
        print(self.map.store.values())
        return self

    def top(self):
        for element in self.stack:
            element.top()

        for state in self.substates:
            state.top()

        self.propagate_up()
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

    # TODO add less_equal for stack
    def _less_equal(self, other: 'AssumptionState') -> bool:
        return self.map.less_equal(other.map)

    def _join(self, other: 'AssumptionState') -> 'AssumptionState':
        for typ in self.types:
            self.substates[typ].join(other.substates[type])
        self.join(other)
        self.propagate_up()
        return self

    def _meet(self, other: 'AssumptionState'):
        for typ in self.types:
            self.substates[typ].meet(other.substates[type])
        self.meet(other)
        self.propagate_up()
        return self

    def _widening(self, other: 'AssumptionState'):
        for typ in self.types:
            self.substates[typ].widening(other.substates[type])
        self.widening(other)
        self.propagate_up()
        return self

    def _assign(self, left: Expression, right: Expression) -> 'State':
        raise Exception("Assign should not be called in backward analysis")

    def _assume(self, condition: Expression) -> 'State':
        # get all variables included in this condition
        variable_ids = condition.ids()
        # assume the condition on the mapping of every one of these variables
        # the validity of the condition is checked inside the assumption function
        for state in self.substates.values():
            state._assume(condition)
        # saving loop/if condition on the top layer of the stack
        # used for calculating multiplicity for loops
        self.stack[-1].condition = condition
        self.propagate_up()

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
        for state in self.substates.values():
            state.raise_error()
        self.propagate_up()
        return self

    def _substitute(self, left: Expression, right: Expression) -> 'State':
        if isinstance(right, Input):
            self.handle_input(left)
        else:
            for state in self.substates.values():
                state.substitute(left, right)
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
        # TODO propagate to substates
        # for state in self.substates:
        #     state.store[variable].top()

    def propagate_up(self):
        """
        Propagate values from substates up to the store of the main state.
        :return:
        """
        lyra_type = {
            "int": IntegerLyraType,
            "float": FloatLyraType,
            "bool": BooleanLyraType,
            "list": ListLyraType,
            "str": StringLyraType
        }
        for var in self.variables:
            state = self.substates[lyra_type[str(var.typ)]]
            self.map.store[var] = state.get_element(var)


class NumericalAssumptionState(State):

    def __init__(self, variables: VariableIdentifier):
        self.interval_state = IntervalState(variables)
        # self.type_state = TypeState(variables)

    def bottom(self):
        self.interval_state.bottom()
        return self

    def top(self):
        self.interval_state.top()
        return self

    def is_bottom(self) -> bool:
        return self.interval_state.is_bottom()

    def is_top(self) -> bool:
        return self.interval_state.is_top()

    def _less_equal(self, other: 'Lattice') -> bool:
        return self.interval_state.less_equal(other.interval_state)

    def _join(self, other: 'Lattice') -> 'Lattice':
        self.interval_state.join(other.interval_state)
        return self

    def _meet(self, other: 'Lattice'):
        self.interval_state.meet(other.interval_state)
        return self

    def _widening(self, other: 'Lattice'):
        self.interval_state.widening(other.interval_state)
        return self

    def _assign(self, left: Expression, right: Expression) -> 'State':
        pass

    def _assume(self, condition: Expression) -> 'State':
        self.interval_state.assume(condition)
        return self

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
        self.interval_state.raise_error()
        return self

    def _substitute(self, left: Expression, right: Expression) -> 'State':
        self.interval_state.substitute(left, right)
        return self

    def get_element(self, variable: VariableIdentifier):
        interval = self.interval_state.store[variable]
        # type = self.type_state.store[variable]

        lattice_element = NumericalAssumption()
        lattice_element.interval = interval
        return lattice_element

class StringAssumptionState(State):

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

    def __init__(self, variables: List[VariableIdentifier]):
        pass

    def _assign(self, left: Expression, right: Expression) -> 'State':
        pass

    def _assume(self, condition: Expression) -> 'State':
        pass

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


