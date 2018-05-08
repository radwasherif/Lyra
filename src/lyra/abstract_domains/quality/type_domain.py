from enum import IntEnum
from typing import List

from lyra.abstract_domains.lattice import Lattice
from lyra.abstract_domains.state import State
from lyra.abstract_domains.store import Store
from lyra.core.expressions import Expression, VariableIdentifier
from lyra.core.types import ListLyraType, BooleanLyraType, IntegerLyraType, FloatLyraType, StringLyraType


class TypeState(Store, State):

    def __init__(self, variables: List[VariableIdentifier]):
        types = [BooleanLyraType, IntegerLyraType, FloatLyraType, StringLyraType, ListLyraType]
        lattices = {v: TypeLattice for v in variables}
        super(TypeState, self).__init__(variables, lattices)

    def add_variable(self, variable: VariableIdentifier):
        pass

    def remove_variable(self, variable: VariableIdentifier):
        pass

    def _assign(self, left: Expression, right: Expression) -> 'TypeState':
        pass

    #TODO implement assume for type
    def _assume(self, condition: Expression) -> 'TypeState':
        pass

    def enter_if(self) -> 'TypeState':
        pass

    def exit_if(self) -> 'TypeState':
        pass

    def enter_loop(self) -> 'TypeState':
        pass

    def exit_loop(self) -> 'State':
        pass

    def _output(self, output: Expression) -> 'State':
        pass

    def raise_error(self) -> 'State':
        self.bottom()
        return self

    def _substitute(self, left: Expression, right: Expression) -> 'TypeState':
        self.store[left].element.substitute(right.typ)
        return self


class TypeLattice(Lattice):

    class Type(IntEnum):
        """
            Type enum.
        """
        __order__ = "Any String Float Int Bool"
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
        self.type_map = {
            any: TypeLattice.Type.Any,
            str: TypeLattice.Type.String,
            float: TypeLattice.Type.Float,
            int: TypeLattice.Type.Int,
            bool: TypeLattice.Type.Bool
        }

    def __repr__(self):
        return self.element.name

    def max_type(self):
        return max([t for t in TypeLattice.Type])

    @property
    def min_type(self):
        return min([t for t in TypeLattice.Type])

    def bottom(self):
        self.replace(TypeLattice(self.min_type))
        return self

    def top(self):
        self.replace(TypeLattice(self.max_type))
        return self

    def is_bottom(self) -> bool:
        return self.element == self.min_type

    def is_top(self) -> bool:
        return self.element == self.max_type

    def _less_equal(self, other: 'TypeLattice') -> bool:
        return self.element <= other.element

    def _join(self, other: 'TypeLattice') -> 'TypeLattice':
        self.replace(TypeLattice(max(self.element, other.element)))
        return self

    def _meet(self, other: 'TypeLattice') -> 'TypeLattice':
        self.replace(TypeLattice(min(self.element, other.element)))
        return self

    def _widening(self, other: 'TypeLattice') -> 'TypeLattice':
        return self._join(other)

    def substitute(self, type):
        self.element = self.type_map[type]



