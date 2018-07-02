from enum import IntEnum
from typing import List

from lyra.abstract_domains.lattice import Lattice
from lyra.abstract_domains.state import State
from lyra.abstract_domains.store import Store
from lyra.core.expressions import Expression, VariableIdentifier, Identifier
from lyra.core.statements import ProgramPoint
from lyra.core.types import *

#
# class TopLyraType(LyraType):
#
#     def __repr__(self):
#         return "T"
from lyra.quality_analysis.input_checker import InputError


class BottomLyraType(LyraType):
    def __repr__(self):
        return "⊥"


class TypeState(Store, State):

    def __init__(self, variables: List[VariableIdentifier]):
        types = [BooleanLyraType, IntegerLyraType, FloatLyraType, StringLyraType]
        lattices = {typ: TypeLattice for typ in types}
        arguments = {}
        for typ in types:
            t = typ()
            arguments[typ] = {"type_element": t}
        super().__init__(variables, lattices, arguments)

    def _assign(self, left: Expression, right: Expression) -> 'TypeState':
        pass

    # TODO implement assume for type_element
    def _assume(self, condition: Expression) -> 'TypeState':
        # ids = condition.ids()
        # for variable in ids:
        #     self.store[variable] = self.store[variable].meet(TypeLattice(type_element=condition.typ))
        return self

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
        self.store[left].join(TypeLattice(type_element=right.typ))
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

    def replace_variable(self, variable: Identifier, pp: ProgramPoint):
        pass

    @staticmethod
    def from_json(obj):
        map = {
            "string": StringLyraType,
            "float": FloatLyraType,
            "int": IntegerLyraType,
            "bool": BooleanLyraType,
            "⊥": BottomLyraType
        }
        return TypeLattice(type_element=map[obj]())


class TypeLattice(Lattice):

    def __init__(self, type_element=None):
        super().__init__()
        self.types = [BottomLyraType(), BooleanLyraType(), IntegerLyraType(), FloatLyraType(), StringLyraType()]
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
        return self.types.index(self.type_element) <= other.types.index(other.type_element)

    def _join(self, other: 'TypeLattice') -> 'TypeLattice':
        idx1 = self.types.index(self.type_element)
        idx2 = self.types.index(other.type_element)
        self.replace(TypeLattice(self.types[max(idx1, idx2)]))
        return self

    def _meet(self, other: 'TypeLattice') -> 'TypeLattice':
        idx1 = self.types.index(type(self.type_element))
        idx2 = self.types.index(type(other.type_element))
        self.replace(TypeLattice(self.types[min(idx1, idx2)]))
        return self

    def _widening(self, other: 'TypeLattice') -> 'TypeLattice':
        return self._join(other)

    def replace_variable(self, variable: Identifier, pp: ProgramPoint):
        pass

    def get_type(self, variable: VariableIdentifier):
        return self.type_element

    def check_input(self, id, line_number, start_offset, end_offset, input_value, id_val_map):
        if isinstance(self.type_element, IntegerLyraType) and not self.is_int(input_value):
            return InputError(code_line=id, input_line=line_number, start_offset=start_offset, end_offset=end_offset, message=self.format_error_message(self.type_element))
        if isinstance(self.type_element, FloatLyraType) and not self.is_bool(input_value):
            return InputError(code_line=id, input_line=line_number, start_offset=start_offset, end_offset=end_offset, message=self.format_error_message(self.type_element))
        if isinstance(self.type_element, BottomLyraType) and not self.is_bool(input_value):
            return InputError(code_line=id, input_line=line_number, start_offset=start_offset, end_offset=end_offset, message=self.format_error_message(self.type_element))

    def format_error_message(self, expected_type):
        return f"should be of type {expected_type}"

    def is_int(self, val):
        try:
            int(val)
            return True
        except:
            return False

    def is_float(self, val):
        try:
            float(val)
            return True
        except:
            return False

    def is_bool(self, val):
        if val in [True, False, "True", "False", 1, 0, "1", "0"]:
            return True
        return False