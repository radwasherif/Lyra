from copy import deepcopy
from typing import Tuple

from lyra.abstract_domains.lattice import Lattice
from lyra.core.expressions import Literal, Identifier, UnaryBooleanOperation, \
    BinaryComparisonOperation, Range
from lyra.core.statements import ProgramPoint
from lyra.core.types import IntegerLyraType


class AssumptionGraph(Lattice):
    def __init__(self, mult=None, assumptions=None):
        """

        """
        self.mult = Mult(IntegerLyraType, str(mult)) if mult is not None else Mult(IntegerLyraType,
                                                                                   "1")  # multiplicity parameter: Expression
        self.assumptions = assumptions if assumptions is not None else []  # list of children: Assumption or AssumptionGraph
        self.condition = None  # condition to be used to calculate multiplicity in case of loops: Expression
        self.is_loop = False  # indicates whether condition is a loop condition or if-statement condition: bool
        self.loss = False  # indicates whether information has been lost during a previous join
        self.ids = []  # a map from program line to assumption

    def __repr__(self):
        return self.to_string(self)

    def copy(self):
        return self.copy_helper(self)

    def bottom(self):
        self.assumptions = []
        return self

    def top(self):
        self.traverse(self, "top")
        return self

    def is_bottom(self) -> bool:
        return len(self.assumptions) == 0

    def is_top(self) -> bool:
        conj, _ = self.traverse(self, "is_top")
        return conj

    def _less_equal(self, other: 'AssumptionGraph') -> bool:
        res, rem = AssumptionGraph.less_equal_helper(self, other)
        return res, (AssumptionGraph(1, rem[0]), AssumptionGraph(1, rem[1]))

    def _join(self, other: 'AssumptionGraph') -> 'AssumptionGraph':
        res, rem = AssumptionGraph.join_helper(self, other)
        # wrap result and remainder from join algorithm in AssumptionGraph objects
        res = AssumptionGraph(1, res)
        rem = (AssumptionGraph(1, rem[0]), AssumptionGraph(1, rem[1]))
        return res, rem

    def _meet(self, other: 'Lattice'):
        raise Exception("This should not happen.")

    def _widening(self, other: 'Lattice'):
        self.join(other)
        return self

    def replace_variable(self, variable: Identifier, pp: ProgramPoint):
        self.traverse(self, "replace_variable", variable, pp)

    # =============================================
    #             HEURISTICS
    # =============================================
    def all_nodes(self):
        return all(isinstance(el, AssumptionNode) for el in self.assumptions)

    def loop_join(self, other: 'AssumptionGraph'):
        # both are loops
        if self.is_loop and other.is_loop:
            if not self.loss:  # no information was lost in both loops
                # remove loop marker and return longer assumption list
                # if the not-taken list has lost information, mark result with information loss
                if len(self.assumptions) > len(other.assumptions):
                    # self.is_loop = False
                    self.loss = other.loss
                    return self, (AssumptionGraph(1, []), AssumptionGraph(1, []))
                else:
                    # other.is_loop = False
                    other.loss = self.loss
                    return other, (AssumptionGraph(1, []), AssumptionGraph(1, []))
            else:  # the first loop has information loss, take the first loop
                return self, (AssumptionGraph(1, []), AssumptionGraph(1, []))
        # same stack level, but one is not a loop, normal join
        a = self.copy()
        b = other.copy()
        a.is_loop = False
        b.is_loop = False
        return a._join(b)

    def join_helper(a_in: 'AssumptionGraph', b_in: 'AssumptionGraph'):
        a = a_in.copy()
        b = b_in.copy()
        if isinstance(a, AssumptionNode) and isinstance(b, AssumptionNode):
            return [a.join(b)], ([], [])
        if not isinstance(a, AssumptionGraph) or not isinstance(b, AssumptionGraph):
            anew, bnew = a, b
            if isinstance(a, AssumptionNode):
                anew = AssumptionGraph(1, [a])
            if isinstance(a, list):
                anew = AssumptionGraph(1, a)
            if isinstance(b, AssumptionNode):
                bnew = AssumptionGraph(1, [b])
            if isinstance(b, list):
                bnew = AssumptionGraph(1, b)
            return AssumptionGraph.join_helper(anew, bnew)

        result = []
        remainder = ([], [])
        if a.is_bottom():
            if not b.is_bottom():
                return result, ([], [b])
            return result, remainder
        if b.is_bottom():
            if not a.is_bottom():
                return result, ([a], [])
            return result, remainder

        if a.all_nodes() and b.all_nodes() and len(a.assumptions) == len(b.assumptions):
            return AssumptionGraph.easy_join(a, b)

        # 1 * [A1, A2,.. ] (join) 1 * [B1, B2, B3,..] = 1 * [A1 (join) B1, A2 (join) B2],
        # with remainder = ([], [B3])
        if a.mult == 1 and b.mult == 1:
            if b.assumptions is None:
                raise ValueError
            while len(a.assumptions) > 0 and len(b.assumptions) > 0:
                a1 = a.assumptions.pop(0)
                b1 = b.assumptions.pop(0)
                res, rem = AssumptionGraph.join_helper(a1, b1)
                # print(f"ONE {a1} + {b1} -> RES: {res}, REM: {rem}")
                result = result + res
                if len(rem[0]) > 0:
                    a.assumptions = rem[0] + a.assumptions
                if len(rem[1]) > 0:
                    b.assumptions = rem[1] + b.assumptions
            remainder0 = []
            remainder1 = []
            if len(a.assumptions) > 0:
                remainder0 = a.assumptions
            if len(b.assumptions) > 0:
                remainder1 = b.assumptions
            # print((remainder0, remainder1))
            return result, (remainder0, remainder1)
        else:
            # N * [A1, A2,...An] (join) M * [B1, B2,...,Bm] where at least N or M is not 1
            # unroll one iteration of the loop
            if a.mult == 1:
                left = AssumptionGraph(1, [])
            else:
                left = AssumptionGraph(a.mult - 1, [assmp.copy() for assmp in a.assumptions])
            if b.mult == 1:
                right = AssumptionGraph(1, [])
            else:
                right = AssumptionGraph(b.mult - 1, [assmp.copy() for assmp in b.assumptions])

            # join unrolled iteration, possibly with remainder
            # 1 * [A1, A2,.., An] (join) 1 * [B1, B2,.., Bm] =
            # result, (left_remainder, right_remainder)
            one_a = AssumptionGraph(1, [assmp.copy() for assmp in a.assumptions])
            one_b = AssumptionGraph(1, [assmp.copy() for assmp in b.assumptions])
            res, rem = AssumptionGraph.join_helper(one_a, one_b)

            result = result + res

            if len(rem[0]) > 0:
                left = AssumptionGraph(1, rem[0] + [left])
            if len(rem[1]) > 0:
                right = AssumptionGraph(1, rem[1] + [right])

            # unroll remainder of previous join and the remainder of the iterations
            # 1 * [left_remainder, (N-1) * [A1, A2,.., An]] (join) 1 * [right_remainder,
            # (M-1) * [B1, B2,.., Bm]]
            res, rem = AssumptionGraph.join_helper(left.copy(), right.copy())
            result = result + res
            rem0 = rem[0] + remainder[0]
            rem1 = rem[1] + remainder[1]
            return result, (rem0, rem1)

    def easy_join(a, b):
        

        res_mult = a.mult.min(b.mult)
        res_list = []
        for a1, b1 in zip(a.assumptions, b.assumptions):
            res_list = res_list + AssumptionGraph.join_helper(a1, b1)[0]
        remainder = ([], [])
        if res_mult < a.mult:
            remainder = (
            [AssumptionGraph(a.mult - res_mult, [AssumptionGraph(1, [assmp.copy() for assmp in a.assumptions])])], [])
        elif res_mult < b.mult:
            remainder = (
            [], [AssumptionGraph(b.mult - res_mult, [AssumptionGraph(1, [assmp.copy() for assmp in b.assumptions])])])
        result = AssumptionGraph(res_mult, res_list)
        return [result], remainder

    def loop_less_equal(self, other: 'AssumptionGraph'):
        if not self.loss:  # no information was lost in both loops
            # remove loop marker and return longer assumption list
            # if the not-taken list has lost information, mark result with information loss
            if len(self.assumptions) > len(other.assumptions):
                # self.is_loop = False
                return False, (AssumptionGraph(1, []), AssumptionGraph(1, []))
            else:
                # other.is_loop = False
                return True, (AssumptionGraph(1, []), AssumptionGraph(1, []))
        else:  # the first loop has information loss, take the first loop
            return False, (AssumptionGraph(1, []), AssumptionGraph(1, []))

    def less_equal_helper(a_in: 'AssumptionGraph', b_in: 'AssumptionGraph'):
        a = a_in.copy()
        b = b_in.copy()
        if isinstance(a, AssumptionNode) and isinstance(b, AssumptionNode):
            return a.less_equal(b), ([], [])
        if not isinstance(a, AssumptionGraph) or not isinstance(b, AssumptionGraph):
            anew, bnew = a, b
            if isinstance(a, AssumptionNode):
                anew = AssumptionGraph(1, [a])
            if isinstance(a, list):
                anew = AssumptionGraph(1, a)
            if isinstance(b, AssumptionNode):
                bnew = AssumptionGraph(1, [b])
            if isinstance(b, list):
                bnew = AssumptionGraph(1, b)
            return AssumptionGraph.less_equal_helper(anew, bnew)

        result = True
        remainder = ([], [])
        if a.is_bottom():
            if not b.is_bottom():
                return result, ([], [])
            return result, remainder
        if b.is_bottom():
            if not a.is_bottom():
                return not result, ([], [])
            return result, remainder

        if a.all_nodes() and b.all_nodes() and len(a.assumptions) == len(b.assumptions):
            return AssumptionGraph.easy_less_equal(a, b)

        if a.mult == 1 and b.mult == 1:
            while len(a.assumptions) > 0 and len(b.assumptions) > 0:
                a1 = a.assumptions.pop(0)
                b1 = b.assumptions.pop(0)
                res, rem = AssumptionGraph.less_equal_helper(a1, b1)
                # print(f"ONE {a1} + {b1} -> RES: {res}, REM: {rem}")
                result = result and res
                # if not result:
                #     return result
                if len(rem[0]) > 0:
                    a.assumptions = rem[0] + a.assumptions
                if len(rem[1]) > 0:
                    b.assumptions = rem[1] + b.assumptions
            remainder0 = []
            remainder1 = []
            # if len(a.assumptions) > 0:
            #     remainder0 = a.assumptions
            # if len(b.assumptions) > 0:
            #     remainder1 = b.assumptions
            # print((remainder0, remainder1))
            return result, (remainder0, remainder1)
        else:
            # print("JOIN n m 1 1")
            if a.mult == 1:
                left = AssumptionGraph(1, [])
            else:
                left = AssumptionGraph(a.mult - 1, [assmp.copy() for assmp in a.assumptions])
            if b.mult == 1:
                right = AssumptionGraph(1, [])
            else:
                right = AssumptionGraph(b.mult - 1, [assmp.copy() for assmp in b.assumptions])

            one_a = AssumptionGraph(1, [assmp.copy() for assmp in a.assumptions])
            one_b = AssumptionGraph(1, [assmp.copy() for assmp in b.assumptions])
            res, rem = AssumptionGraph.less_equal_helper(one_a, one_b)
            # print(f"MULT {one_a}, {one_b} -> RES: {res}, REM: {rem}")
            # print(f"RES -> {res}, REM -> {rem}")
            result = result and res
            # print(f"left {left}, right {right}")
            # if len(rem[0]) > 0:
            #     left = AssumptionGraph(1, rem[0] + [left])
            # if len(rem[1]) > 0:
            #     # print(f"REM[1]: {rem[1]}, RIGHT: {right}")
            #     right = AssumptionGraph(1, rem[1] + [right])
            # print(f"right: {right}, after adding rem {rem[1]}")
            # print("JOIN left right", left, right)
            res, rem = AssumptionGraph.less_equal_helper(left.copy(), right.copy())
            # print(f"MULT2 {left}, {right} -> RES: {res}, REM: {rem}")
            result = result and res
            rem0 = rem[0] + remainder[0]
            rem1 = rem[1] + remainder[1]
            return result, (rem0, rem1)

    def easy_less_equal(a, b):
        res_mult = a.mult.min(b.mult)
        result = True
        for a1, b1 in zip(a.assumptions, b.assumptions):
            result = result and (a1.less_equal(b1))
        remainder = ([], [])
        # if res_mult < a.mult:
        #     remainder = ([AssumptionGraph(a.mult - res_mult, [AssumptionGraph(1, [assmp.copy() for assmp in a.assumptions])])], [])
        # elif res_mult < b.mult:
        #     remainder = ([], [AssumptionGraph(b.mult - res_mult, [AssumptionGraph(1, [assmp.copy() for assmp in b.assumptions])])])
        return result, remainder

    def copy_helper(self, this: Lattice):
        if isinstance(this, AssumptionNode):
            return this.copy()
        result = AssumptionGraph()
        result.mult = deepcopy(this.mult)
        result.condition = deepcopy(this.condition)
        result.is_loop = deepcopy(this.is_loop)
        result.loss = deepcopy(this.loss)
        if self.assumptions is None:
            result.assumptions = None
        else:
            result.assumptions = []
            for element in this.assumptions:
                result.assumptions.append(self.copy_helper(element))
            result.ids = deepcopy(this.ids)
        return result

    def to_string(self, graph):
        if isinstance(graph, AssumptionNode):
            return repr(graph)
        return ("L:" if self.is_loop else "") + str(graph.mult) + ("*" if self.loss else "") + " x [" + ",".join(
            [self.to_string(assmp) for assmp in graph.assumptions]) + "]"

    def traverse(self, graph, func, *args, other=None):
        """
        Traverse the graph and apply the function to every leaf node. For binary operations, the two graphs are assumed to be of identical structure.
        :param graph: Graph to be traversed
        :param func: Function to be applied
        :return:
        """
        if other is None:
            if isinstance(graph, AssumptionNode):
                return getattr(graph, func)(*args)
            conj, disj = True, False
            for assmp in graph.assumptions:
                result = self.traverse(assmp, func, *args)
                if isinstance(result, bool):
                    conj = conj and result
                    disj = disj or result
                else:
                    assmp = result
            return conj, disj
        else:
            if isinstance(graph, AssumptionNode) and isinstance(other, AssumptionNode):
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
            Combining two elements from the assumptions graph when doing a pop operation
        :param lower:
        :return:
        """
        if lower is None:
            return self
        if len(self.assumptions) == 0:
            return lower
        if self.loss:
            lower.loss = True
        if lower.is_loop:
            if not lower.loss:
                self.mult = self.get_mult()
        # if this is the first iteration -> just put the upper layer in the lower one
        if not all([a in lower.ids for a in self.ids]):
            lower.assumptions = [self] + lower.assumptions
            lower.ids = deepcopy(self.ids)
        else:  # if inputs in the upper layer have been stored before -> replace assumptions one by one from upper layer to lower one
            lower.replace_all_assumptions(self)
        return lower

    def replace_all_assumptions(self, other: 'AssumptionGraph'):
        """
        Replaces all the assumptions in self with the assumptions existing in 'other'.
        :param other:
        :return:
        """
        if isinstance(other, AssumptionNode):
            self.replace_assumption(other)
            return
        for assmp in other.assumptions:
            self.replace_all_assumptions(assmp)

    def add_assumption(self, assumption: 'AssumptionNode'):
        """
        Adds a single assumption to an assumption graph if the program point has not had an assumption stored before. Otherwise, it replaces the existing assumption for this program point.
        :param assumption:
        :return:
        """
        if assumption.id in self.ids:
            self.replace_assumption(assumption)
        else:
            self.assumptions = [assumption] + self.assumptions
            self.ids.append(assumption.id)

    def replace_assumption(self, assumption: 'AssumptionNode'):
        self.traverse(self, "replace_assumption", assumption)

    def get_mult(self):
        condition = self.condition
        if isinstance(condition, UnaryBooleanOperation):
            condition = condition.expression
        if isinstance(condition, BinaryComparisonOperation):
            condition = condition.right
        if isinstance(condition, Range):
            val = int(condition.end.val) - int(condition.start.val)
            return Mult(IntegerLyraType, str(val))

    def to_json(self):
        js = dict()
        js["mult"] = self.mult.val
        js["assumptions"] = [a.to_json() for a in self.assumptions]
        return js

    def from_json(self, js: dict):
        if "mult" in js:
            ag = AssumptionGraph()
            ag.mult = Mult(val=js["mult"], typ=IntegerLyraType)
            ag.assumptions = [self.from_json(a) for a in js["assumptions"]]
            print(ag)
            return ag
        if "type" in js:
            an = AssumptionNode()
            an.from_json(js)
            return an


class AssumptionNode(AssumptionGraph):

    def __init__(self, id: int=None, lattice_elements: Tuple[Lattice]=None):
        super().__init__()
        self._id = id
        self.type_element = lattice_elements[0] if lattice_elements is not None else None
        self.lattice_element = lattice_elements[1] if lattice_elements is not None else None

    def __repr__(self):
        return f"(id{self.id}, {self.type_element}, {self.lattice_element})"

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        self._id = id

    def bottom(self):
        self.type_element.bottom()
        self.lattice_element.bottom()
        return self

    def top(self):
        self.type_element.top()
        self.lattice_element.top()
        return self

    def is_bottom(self) -> bool:
        return self.type_element.is_bottom() or self.lattice_element.is_bottom()

    def is_top(self) -> bool:
        return self.type_element.is_top() and self.lattice_element.is_top()

    def _less_equal(self, other: 'AssumptionNode') -> bool:
        return self.id >= other.id and self.type_element.less_equal(other.type_element) and self.lattice_element.less_equal(other.lattice_element)

    def _join(self, other: 'AssumptionNode') -> 'AssumptionNode':
        # print("Node Join", self, other)
        self.id = min(self.id, other.id)
        if self.type_element != other.type_element:
            self.lattice_element = self.lattice_element.top()
        else:
           self.lattice_element =  self.lattice_element.join(other.lattice_element)
        self.type_element = self.type_element.join(other.type_element)
        # print("RESULT NODE JOIN", self)
        # print()
        return self

    def _meet(self, other: 'AssumptionNode'):
        raise Exception("This should not happen.")

    def _widening(self, other: 'AssumptionNode'):
        self.join(other)
        return self

    def copy(self):
        return AssumptionNode(self.id, (self.type_element.copy(), self.lattice_element.copy()))

    def replace_variable(self, variable: Identifier, pp: ProgramPoint):
        self.lattice_element.replace_variable(variable, pp)

    def to_json(self):
        js = dict()
        js["id"] = self.id
        js["type"] = str(self.type_element)
        js["lattice"] = self.lattice_element.to_json()
        return js

    def replace_assumption(self, assumption: 'AssumptionNode'):
        if self.id == assumption.id:
            self.type_element = assumption.type_element
            self.lattice_element = assumption.lattice_element

    def check_input(self, input_line, start_offset, end_offset, input_value, id_value, id_input_line):
        type_error = self.type_element.check_input(self.id, input_line, start_offset, end_offset, input_value, id_value)
        # if there is a type error, ignore other errors and output type error
        if type_error is not None:
            return type_error
        # otherwise, cast the value to its appropriate type and check for value errors
        types = {
            'int': int,
            'float': float,
            'string': str,
            'bool': bool
        }
        input_value = types[str(self.type_element.type_element)](input_value)
        value_error = self.lattice_element.check_input(self.id, input_line, start_offset, end_offset, input_value, id_value, id_input_line)
        return value_error


class Mult(Literal):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __add__(self, other):
        assert isinstance(self, Literal) and self.typ == IntegerLyraType
        other = int(other.val) if isinstance(other, Mult) else other
        self.val = str(int(self.val) + other)
        return self

    def __sub__(self, other):
        assert isinstance(self, Literal) and self.typ == IntegerLyraType
        other = int(other.val) if isinstance(other, Mult) else other
        val = str(int(self.val) - other)
        return Mult(self.typ, val)

    def min(self, other: 'Mult'):
        val = str(min(int(self.val), int(other.val)))
        return Mult(self.typ, val)

    def __lt__(self, other):
        return int(self.val) < int(other.val)

    def __eq__(self, other):
        return int(self.val) == other

    def __hash__(self):
        return super().__eq__()

    def __str__(self):
        return super().__str__()


