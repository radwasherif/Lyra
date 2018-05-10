from lyra.abstract_domains.numerical.interval_domain import IntervalState
from lyra.abstract_domains.quality.type_domain import TypeState
from lyra.abstract_domains.store import Store
from lyra.abstract_domains.stack import Stack
from lyra.abstract_domains.state import State
from lyra.core.expressions import *
from lyra.abstract_domains.quality.assumption_lattice import AssumptionGraph, Assumption, NumericalAssumption, StringAssumption
from lyra.core.statements import ProgramPoint
from lyra.core.types import FloatLyraType, BooleanLyraType, IntegerLyraType, StringLyraType, ListLyraType, AnyLyraType


class AssumptionState(State):

    def __init__(self, variables: List[VariableIdentifier]):
        self.states = {}
        self.types = {
            "numerical": [AnyLyraType, IntegerLyraType, FloatLyraType, BooleanLyraType],
            "string": [StringLyraType]
        }
        self.type_state = TypeState(variables)
        self.states["numerical"] = IntervalState([v for v in variables if type(v.typ) in self.types["numerical"]])
        self.states["string"] = StringAssumptionState([v for v in variables if type(v.typ) in self.types["string"]])
        self.stack = AssumptionStack(AssumptionGraph)

    def __repr__(self):
        return f"types: {self.type_state}, states: {self.states}"

    def bottom(self):
        self.propagate_down("bottom")
        self.stack.bottom()
        return self

    def top(self):
        self.propagate_down("top")
        self.stack.top()
        return self

    def is_bottom(self) -> bool:
        _, disj = self.propagate_down("is_bottom")
        return disj or self.stack.is_bottom()

    def is_top(self) -> bool:
        conj, _ = self.propagate_down("is_bottom")
        return  conj and self.stack.is_top()

    # TODO add less_equal for stack
    def _less_equal(self, other: 'AssumptionState') -> bool:
        conj, _ = self.propagate_down("_less_equal", other=other)
        return conj and self.stack.less_equal(other.stack)

    def _join(self, other: 'AssumptionState') -> 'AssumptionState':
        self.propagate_down("_join", other=other)
        self.stack.join(other.stack)
        return self

    def _meet(self, other: 'AssumptionState'):
        self.propagate_down("_meet", other=other)
        self.stack.meet(other.stack)
        return self

    def _widening(self, other: 'AssumptionState'):
        self.propagate_down("_widening", other=other)
        self.stack.widening(other.stack)
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
        self.propagate_down("_substitute", left, right)
        new_type = self.type_state.get_type(left)
        old_category = self.get_key(old_type)
        new_category = self.get_key(new_type)
        print("old", old_category)
        print("new", new_category)
        if old_category != new_category and old_category != AnyLyraType:
            self.states[old_category].remove_variable(left)
            self.states[new_category].add_variable(left)

        if isinstance(right, Input):
            self.handle_input(left)

        return self

    def propagate_down(self, func: str, *args, other=None):
        if other is None:
            disj = conj = getattr(self.type_state, func)(*args)
            for state in self.states.values():
                result = getattr(state, func)(*args)
                if isinstance(result, bool):
                    conj = conj and result
                    disj = disj or result
        else:
            disj = conj = getattr(self.type_state, func)(other.type_state)
            for state, other_state in zip(self.states.values(), other.states.values()):
                result = getattr(state, func)(other_state)
                if isinstance(result, bool):
                    conj = conj and result
                    disj = disj or result
        return conj, disj

    def get_key(self, typ: LyraType):
        print("type",typ)
        for k, v in self.types.items():
            if type(typ) in v or typ in v:
                print("get key",k)
                return k


    def handle_input(self, variable: VariableIdentifier):
        category = self.get_key(variable.typ)
        #store the assumption about this variable and then forget it
        assumption = self.states[category].forget_variable(variable)
        #associate assumption with line number
        
        #prepend assumption to top layer of stack

        #replace every occurence of variable in stack with its line number

        pass


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

    def __repr__(self):
        return "STRING ASSUMPTION"

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


class AssumptionStack(Stack):

    def __init__(self, typ: AssumptionGraph):
        super().__init__(typ)

    def join(self, other: 'Stack'):
        pass

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

    def replace(self, variable: VariableIdentifier, pp: ProgramPoint):
        pass

    def top_layer(self, is_loop: bool=None, condition: Expression=None, pp: ProgramPoint=None):
        if is_loop is not None:
            self.stack[-1].is_loop = is_loop
        if condition is not None:
            self.stack[-1].condition = condition
        if pp is not None:
            self.stack[-1].pp = pp
