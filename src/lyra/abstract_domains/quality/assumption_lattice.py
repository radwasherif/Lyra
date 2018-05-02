from enum import IntEnum

from lyra.abstract_domains.lattice import Lattice
from lyra.abstract_domains.state import State
from lyra.abstract_domains.numerical.interval_domain import IntervalState
from lyra.core.types import LyraType, IntegerLyraType

from abc import  ABCMeta

from lyra.core.expressions import Expression, Literal


class TypeState(State):

    class Type(IntEnum):
        """
            Type enum.
        """
        __order__ = "Any Float Int Bool"
        Any = 4
        String = 3
        Float = 2
        Int = 1
        Bool = 0

    def __init__(self, type: Type):
        super().__init__()
        if type is not None:
            self.element = type
        else:
            self = self.top()

    def __repr__(self):
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

    @property
    def max_type(self):
        return max([t for t in TypeState.Type])

    @property
    def min_type(self):
        return min([t for t in TypeState.Type])

    def bottom(self):
        self.replace(TypeState(self.min_type))
        return self

    def top(self):
        self.replace(TypeState(self.max_type))
        return self

    def is_bottom(self) -> bool:
        return self.element == self.min_type

    def is_top(self) -> bool:
        return self.element == self.max_type

    def _less_equal(self, other: 'TypeState') -> bool:
        return self.element <= other.element

    def _join(self, other: 'TypeState') -> 'TypeState':
        self.replace(TypeState(max(self.element, other.element)))
        return self

    def _meet(self, other: 'TypeState') -> 'TypeState':
        self.replace(TypeState(min(self.element, other.element)))
        return self

    def _widening(self, other: 'TypeState') -> 'TypeState':
        return self._join(other)


class Assumption(State, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        self.id = None


class NumericalAssumption(Assumption):


    def __init__(self):
        self.type = TypeState().top()
        self.interval = IntervalState().top()

    def __repr__(self):
        pass

    def bottom(self):
        self.type.bottom()
        self.interval.bottom()
        return self

    def top(self):
        self.type.top()
        self.interval.top()
        return self

    def is_bottom(self) -> bool:
        return self.type.is_bottom() or self.interval.is_bottom()

    def is_top(self) -> bool:
        return self.type.is_top() and self.interval.is_top()

    def _less_equal(self, other: 'NumericalAssumption') -> bool:
        return self.type._less_equal(other.type) and self.interval.less_equal(other.interval)

    def _join(self, other: 'NumericalAssumption') -> 'NumericalAssumption':
        self.type.join(other.type)
        self.interval.join(other.interval)
        return self

    def _meet(self, other: 'NumericalAssumption'):
        self.type.meet(other.type)
        self.interval.meet(other.interval)
        return self

    def _widening(self, other: 'NumericalAssumption'):
        self.type.widening(other.type)
        self.interval.widening(other.interval)
        return self
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

class AssumptionGraph(State):

    def __init__(self, mult: Expression, current: Assumption):
        """

        :param mult: multiplicity parameter
        :param current: assumption of the current node
        """
        self.mult = mult
        self.current = current
        self.children = []

    def __repr__(self):
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




