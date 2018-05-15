from enum import IntEnum
from typing import List

from lyra.abstract_domains.lattice import Lattice
from lyra.abstract_domains.state import State
from lyra.abstract_domains.numerical.interval_domain import IntervalState, IntervalLattice
from lyra.core.types import LyraType, IntegerLyraType

from abc import ABCMeta, abstractmethod

from lyra.core.expressions import Expression, Literal


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


class Assumption:
    def __init__(self, id, lattice_elements: List[Lattice]):
        super().__init__()
        self._id = id
        self.lattice_elements = lattice_elements

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        self._id = id

    def __repr__(self):
        return f"(id{self.id}, {self.lattice_elements})"


class AssumptionGraph(Lattice):

    def __init__(self):
        """

        """
        self.mult = Literal(IntegerLyraType, "1")  # multiplicity parameter: Expression
        self.assumptions = []  # list of children: Assumption or AssumptionGraph
        self.condition = None  # condition to be used to calculate multiplicity in case of loops: Expression
        self.is_loop = False  # indicates whether condition is a loop condition or if-statement condition: bool

    def __repr__(self):
        return self.repr(self)

    def bottom(self):
        self.traverse(self, "bottom")
        return self

    def top(self):
        self.traverse(self, "top")
        return self

    def is_bottom(self) -> bool:
        pass

    def is_top(self) -> bool:
        pass

    def _less_equal(self, other: 'Lattice') -> bool:
        return True

    def _join(self, other: 'Lattice') -> 'Lattice':
        pass

    def _meet(self, other: 'Lattice'):
        pass

    def _widening(self, other: 'Lattice'):
        self.join(other)
        return self

    # =============================================
    #             HEURISTICS
    # =============================================

    # TODO: Not sure  how to implement this
    def less_equal_helper(self, this:'Lattice', other: 'Lattice'):
        if isinstance(this, Assumption) and isinstance(other, Assumption):
            return this.less_equal(other)

        elif isinstance(this, AssumptionGraph) and isinstance(other, AssumptionGraph) and len(this.assumptions) == len(other.assumptions):
            leq = True
            for assmp1, assmp2 in zip(this, other):
                return leq and self.join(assmp1, assmp2)
        else:
            return False

    def join(self, this:'Lattice', other: 'Lattice'):
        if isinstance(this, Assumption) and isinstance(other, Assumption):
            this.join(other)
            return this

        elif isinstance(this, AssumptionGraph) and isinstance(other, AssumptionGraph) and len(this.assumptions) == len(other.assumptions):
            for assmp1, assmp2 in zip(this, other):
                return self.join(assmp1, assmp2)
        else:
            return this.bottom()

    def repr(self, graph):
        if isinstance(graph, Assumption):
            return repr(graph)
        return "(" + str(graph.mult) + ", [" + ",".join([self.repr(assmp) for assmp in graph.assumptions]) + "])"

    def traverse(self, graph, func, *args):
        """
        Traverse the graph and apply the function to every leaf node
        :param graph: Graph to be traversed
        :param func: Function to be applied
        :return:
        """
        if isinstance(graph, Assumption):
            graph.getattr(self, func)(*args)
            return
        for child in graph.assumptions:
            self.traverse(child)

    def combine(self, lower):
        """
            Combining two elements from the assumption graph when doing a pop operation
        :param lower:
        :return:
        """
        if self.is_loop:
            self.mult = self.condition
        if lower is not None:
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


