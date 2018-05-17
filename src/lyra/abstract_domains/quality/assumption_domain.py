from copy import deepcopy

from lyra.abstract_domains.numerical.interval_domain import IntervalState
from lyra.abstract_domains.numerical.octagon_d import OctagonDomain
from lyra.abstract_domains.quality.type_domain import TypeState
from lyra.abstract_domains.store import Store
from lyra.abstract_domains.stack import Stack
from lyra.abstract_domains.state import State
from lyra.core.expressions import *
from lyra.abstract_domains.quality.assumption_lattice import AssumptionGraph, Assumption
from lyra.core.statements import ProgramPoint
from lyra.core.types import FloatLyraType, BooleanLyraType, IntegerLyraType, StringLyraType, ListLyraType, AnyLyraType


class AssumptionState(State):

    def __init__(self, variables: List[VariableIdentifier]):
        self.states = {}
        self.types = {
            "numerical": [AnyLyraType, IntegerLyraType, FloatLyraType, BooleanLyraType],
            "string": [StringLyraType]
        }
        self.variables = variables
        self.type_state = TypeState(variables)
        self.states["numerical"] = OctagonDomain([v for v in variables if type(v.typ) in self.types["numerical"]])
        self.states["string"] = StringAssumptionState([v for v in variables if type(v.typ) in self.types["string"]])
        self.stack = AssumptionStack(AssumptionGraph)

    def copy(self):
        new_state = AssumptionState(self.variables)
        new_state.states = {}
        new_state.types = deepcopy(self.types)
        new_state.type_state = self.type_state.copy()
        for k,v in self.states.items():
            new_state.states[k] = v.copy()
        new_state.stack = self.stack.copy()
        new_state.pp = deepcopy(self.pp)
        new_state.result = deepcopy(self.result)
        return new_state

    def __repr__(self):
        return f"types: {self.type_state}, states: {self.states}, stack: {self.stack}"

    def bottom(self):
        self.propagate_down("bottom")
        return self

    def top(self):
        self.propagate_down("top")
        return self

    def is_bottom(self) -> bool:
        _, disj = self.propagate_down("is_bottom")
        return disj

    def is_top(self) -> bool:
        conj, _ = self.propagate_down("is_top")
        return conj

    # TODO add less_equal for stack
    def _less_equal(self, other: 'AssumptionState') -> bool:
        conj, _ = self.propagate_down("_less_equal", other=other)
        return conj

    def _join(self, other: 'AssumptionState') -> 'AssumptionState':
        self.propagate_down("_join", other=other)
        return self

    def _meet(self, other: 'AssumptionState'):
        self.propagate_down("_meet", other=other)
        return self

    def _widening(self, other: 'AssumptionState'):
        self.propagate_down("_widening", other=other)
        return self

    def _assign(self, left: Expression, right: Expression) -> 'State':
        raise Exception("Assign should not be called in backward analysis")

    def _assume(self, condition: Expression) -> 'State':
        self.propagate_down("_assume", condition)
        self.stack.top_layer(condition=condition)
        return self

    def enter_if(self) -> 'State':
        self.stack.push()
        return self

    def exit_if(self) -> 'State':
        self.stack.pop()
        return self

    def enter_loop(self) -> 'State':
        self.stack.push()
        self.stack.top_layer(is_loop=True)
        return self

    def exit_loop(self) -> 'State':
        self.pop()
        return self

    def _output(self, output: Expression) -> 'State':
        pass

    def raise_error(self) -> 'State':
        self.propagate_down("raise_error")
        return self

    def _substitute(self, left: Expression, right: Expression) -> 'State':
        old_type = self.type_state.get_type(left)
        if isinstance(right, Input):
            # calls substitute in different order to preserve type and assumption information
            self.handle_input(left, right)
        else:
            self.propagate_down("_substitute", left, right)

        new_type = self.type_state.get_type(left)
        old_category = self.get_key(old_type)
        new_category = self.get_key(new_type)
        # if substitution changes type, then replace variable in appropriate domain
        if old_category != new_category and old_category != AnyLyraType:
            self.states[old_category].remove_variable(left)
            self.states[new_category].add_variable(left)

        return self

    def forget_variable(self, variable: VariableIdentifier):
        pass

    def add_variable(self, variable: VariableIdentifier):
        pass

    def remove_variable(self, variable: VariableIdentifier):
        pass

    # =================================================
    #                   HEURISTICS
    # =================================================

    def propagate_down(self, func: str, *args, other=None):
        """
        Performs a certain operation on: the type state, the stack, and the operating substates
        :param func: name of the function to be called
        :param args: arguments to be passed to the function
        :param other: optional attribute in case of binary functions
        :return:
        """
        if other is None:
            disj = getattr(self.type_state, func)(*args) or getattr(self.stack, func)(*args)
            conj = getattr(self.type_state, func)(*args) and getattr(self.stack, func)(*args)
            for state in self.states.values():
                result = getattr(state, func)(*args)
                if isinstance(result, bool):
                    conj = conj and result
                    disj = disj or result
        else:
            disj = getattr(self.type_state, func)(other.type_state) or getattr(self.stack, func)(other.stack)
            conj = getattr(self.type_state, func)(other.type_state) and getattr(self.stack, func)(other.stack)
            for state, other_state in zip(self.states.values(), other.states.values()):
                result = getattr(state, func)(other_state)
                if isinstance(result, bool):
                    conj = conj and result
                    disj = disj or result
        return conj, disj

    def get_key(self, typ: LyraType):
        for k, v in self.types.items():
            if type(typ) in v or typ in v:
                return k

    def handle_input(self, variable: VariableIdentifier, right: Expression):
        category = self.get_key(variable.typ)
        # get lattice element, this is lost after substitution
        lattice_element = self.states[category].forget_variable(variable)
        # perform substitution
        self.propagate_down("_substitute", variable, right)
        # get type lattice element, this is updated only after substitution
        type_element = self.type_state.forget_variable(variable)
        # associate assumption with line number
        assumption = Assumption(id=self.pp.line, lattice_elements=[type_element, lattice_element])
        # prepend assumption to top layer of stack
        self.stack.top_layer(prepend=assumption)
        # TODO replace every occurence of variable in stack with its line number


class StringAssumptionState(State):

    def __init__(self, variables: List[VariableIdentifier]):
        pass

    def __repr__(self):
        return "STRING ASSUMPTION"

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

    def forget_variable(self, variable: VariableIdentifier):
        pass

    def add_variable(self, variable: VariableIdentifier):
        pass

    def remove_variable(self, variable: VariableIdentifier):
        pass


class AssumptionStack(Stack):

    def __init__(self, typ: AssumptionGraph):
        super().__init__(typ, {})

    def _assume(self, condition: Expression):
        pass

    def _substitute(self, left: Expression, right: Expression):
        pass

    def raise_error(self):
        pass

    def push(self):
        self.stack.append(AssumptionGraph())
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

    def replace(self, variable: VariableIdentifier, pp: ProgramPoint):
        pass

    def top_layer(self, is_loop: bool=None, condition: Expression=None, prepend:Assumption=None):
        if is_loop is not None:
            self.stack[-1].is_loop = is_loop
        if condition is not None:
            self.stack[-1].condition = condition
        if prepend is not None:
            self.stack[-1].add_assumption(prepend)
