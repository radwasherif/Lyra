from copy import deepcopy
from enum import IntEnum
from typing import List

from lyra.abstract_domains.lattice import Lattice
from lyra.abstract_domains.state import State
from lyra.abstract_domains.numerical.interval_domain import IntervalState, IntervalLattice
from lyra.core.types import LyraType, IntegerLyraType

from abc import ABCMeta, abstractmethod

from lyra.core.expressions import Expression, Literal, VariableIdentifier


class TypeLattice(State):

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

    def __repr__(self):
        return self.element.name

    @property
    def max_type(self):
        return max([t for t in TypeLattice.Type])

    @property
    def min_type(self):
        return min([t for t in TypeLattice.Type])

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

    def forget_variable(self, variable: VariableIdentifier) -> 'Lattice':
        pass

    def add_variable(self, variable: VariableIdentifier):
        pass

    def remove_variable(self, variable: VariableIdentifier):
        pass


class Assumption(Lattice):

    def __init__(self, id: int, lattice_elements: List[Lattice]):
        super().__init__()
        self._id = id
        self.lattice_elements = lattice_elements

    def __repr__(self):
        return f"(id{self.id}, {self.lattice_elements})"

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        self._id = id

    def bottom(self):
        for element in self.lattice_elements:
            element.bottom()

    def top(self):
        for element in self.lattice_elements:
            element.bottom()

    def is_bottom(self) -> bool:
        return any(element.is_bottom() for element in self.lattice_elements)

    def is_top(self) -> bool:
        return all(element.is_top() for element in self.lattice_elements)

    def _less_equal(self, other: 'Assumption') -> bool:
        return all(element.less_equal(other_element) if type(element) is type(other_element) else False for element, other_element in zip(self.lattice_elements, other.lattice_elements))

    def _join(self, other: 'Assumption') -> 'Assumption':
        for element, other_element in zip(self.lattice_elements, other.lattice_elements):
            if type(element) is type(other_element):
                element.join(other_element)
            else:
                element.top()
        return self

    def _meet(self, other: 'Assumption'):
        for element, other_element in zip(self.lattice_elements, other.lattice_elements):
            if type(element) is type(other_element):
                element.meet(other_element)
            else:
                element.top()
        return self

    def _widening(self, other: 'Assumption'):
        self.join(other)
        return self

    def copy(self):
        array = []
        for element in self.lattice_elements:
            array.append(element.copy())
        return Assumption(self.id, array)


class AssumptionGraph(Lattice):

    def __init__(self):
        """

        """
        self.mult = Literal(IntegerLyraType, "1")  # multiplicity parameter: Expression
        self.assumptions = []  # list of children: Assumption or AssumptionGraph
        self.condition = None  # condition to be used to calculate multiplicity in case of loops: Expression
        self.is_loop = False  # indicates whether condition is a loop condition or if-statement condition: bool

    def __repr__(self):
        return self.to_string(self)

    def copy(self):
        return self.copy_helper(self)

    def bottom(self):
        self.traverse(self, "bottom")
        return self

    def top(self):
        self.traverse(self, "top")
        return self

    def is_bottom(self) -> bool:
        _, disj = self.traverse(self, "is_bottom")
        return disj

    def is_top(self) -> bool:
        conj, _ = self.traverse(self, "is_top")

    def _less_equal(self, other: 'AssumptionGraph') -> bool:
        if self.is_bottom() or other.is_top():
            return True
        if self.is_top() or other.is_bottom():
            return False
        try:
            conj, _ = self.traverse(self, "_less_equal", other=other)
        except Exception:
            return False

    def _join(self, other: 'AssumptionGraph') -> 'AssumptionGraph':
        if self.is_bottom() or other.is_top():
            return other
        if self.is_top() or other.is_bottom():
            return self
        try:
            self.traverse(self, "_join", other=other)
            return self
        except Exception:
            return self.top()

    def _meet(self, other: 'Lattice'):
        if self.is_bottom() or other.is_top():
            return self
        if self.is_top() or other.is_bottom():
            return other
        try:
            self.traverse(self, "_meet", other=other)
            return self
        except Exception:
            return self.top()


    def _widening(self, other: 'Lattice'):
        self.join(other)
        return self

    # =============================================
    #             HEURISTICS
    # =============================================

    def copy_helper(self, this: Lattice):
        if isinstance(this, Assumption):
            return this.copy()
        result = AssumptionGraph()
        result.mult = deepcopy(this.mult)
        result.condition = deepcopy(this.condition)
        result.is_loop = deepcopy(this.is_loop)
        result.assumptions = []
        for element in this.assumptions:
            result.assumptions.append(self.copy_helper(element))
        return result

    def to_string(self, graph):
        if isinstance(graph, Assumption):
            return repr(graph)
        return "(" + str(graph.mult) + ", [" + ",".join([self.to_string(assmp) for assmp in graph.assumptions]) + "])"

    def traverse(self, graph, func, *args, other=None):
        """
        Traverse the graph and apply the function to every leaf node. For binary operations, the two graphs are assumed to be of identical structure.
        :param graph: Graph to be traversed
        :param func: Function to be applied
        :return:
        """
        if other is None:
            if isinstance(graph, Assumption):
                return getattr(graph, func)(*args)
            conj, disj = True, False
            for assmp in graph.assumptions:
                result = self.traverse(assmp, func)
                if isinstance(result, bool):
                    conj = conj and result
                    disj = disj or result
            return conj, disj
        else:
            if isinstance(graph, Assumption) and isinstance(other, Assumption):
                return getattr(graph, func)(other)
            elif isinstance(graph, AssumptionGraph) and isinstance(other, AssumptionGraph):
                conj, disj = True, False
                for assmp, other_assmp in zip(graph.assumptions, other.assumptions):
                    result = self.traverse(assmp, func, other=other_assmp)
                    if isinstance(result, bool):
                        conj = conj and result
                        disj = disj or result
                return conj, disj
            else:
                raise Exception("Graphs must be of the same structure")

    def combine(self, lower):
        """
            Combining two elements from the assumption graph when doing a pop operation
        :param lower:
        :return:
        """

        if self.is_loop:
            self.mult = self.condition
        if lower is not None:
            if len(lower.assumptions) == 0 and len(self.assumptions) == 0:
                return self
            lower.assumptions.append(self)
            return lower
        return self

    def add_assumption(self, assumption: Assumption):
        """
        Prepends new assumption to the front of assumption list
        :param assumption:
        :return:
        """
        self.assumptions = [assumption] + self.assumptions


