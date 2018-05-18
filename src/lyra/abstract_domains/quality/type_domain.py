from enum import IntEnum
from typing import List

from lyra.abstract_domains.lattice import Lattice
from lyra.abstract_domains.state import State
from lyra.abstract_domains.store import Store
from lyra.core.expressions import Expression, VariableIdentifier
from lyra.core.types import *


class TypeState(Store, State):

    def __init__(self, variables: List[VariableIdentifier]):
        types = [BooleanLyraType, IntegerLyraType, FloatLyraType, StringLyraType, ListLyraType]
        lattices = {typ: TypeLattice for typ in types}
        super().__init__(variables, lattices)

    def _assign(self, left: Expression, right: Expression) -> 'TypeState':
        pass

    #TODO implement assume for type_element
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
        self.store[left].substitute(right.typ)
        return self

    def get_type(self, variable: VariableIdentifier) -> 'Type':
        return self.store[variable].get_type(variable)

    def add_variable(self, variable: VariableIdentifier):
        pass

    def remove_variable(self, variable: VariableIdentifier):
        pass

    def forget_variable(self, variable: VariableIdentifier):
        val = self.store[variable].copy()
        self.store[variable].top()
        return val


class TypeLattice(Lattice):

    def __init__(self, type_element=None):
        super().__init__()
        self.types = [BooleanLyraType, IntegerLyraType, FloatLyraType, StringLyraType, AnyLyraType]
        if type_element is not None:
            self.type_element = type_element
        else:
            self.top()

    def __repr__(self):
        return repr(self.type_element)

    def bottom(self):
        self.replace(TypeLattice(self.types[0]))
        return self

    def top(self):
        self.replace(TypeLattice(self.types[-1]))
        return self

    def is_bottom(self) -> bool:
        return self.type_element == self.types[0]

    def is_top(self) -> bool:
        return self.type_element == self.types[-1]

    def _less_equal(self, other: 'TypeLattice') -> bool:
        return self.types.index(self.type_element) <= other.types.index(self.type_element)

    def _join(self, other: 'TypeLattice') -> 'TypeLattice':
        idx1 = self.types.index(self.type_element)
        idx2 = self.types.index(self.type_element)
        self.replace(TypeLattice(self.types[max(idx1, idx2)]))
        return self

    def _meet(self, other: 'TypeLattice') -> 'TypeLattice':
        idx1 = self.types.index(self.type_element)
        idx2 = self.types.index(self.type_element)
        self.replace(TypeLattice(self.types[min(idx1, idx2)]))
        return self

    def _widening(self, other: 'TypeLattice') -> 'TypeLattice':
        return self._join(other)

    def substitute(self, type_element):
        self.type_element = type_element
        return self

    def get_type(self, variable: VariableIdentifier):
        return self.type_element

