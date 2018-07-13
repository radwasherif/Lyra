import string
from copy import deepcopy
from typing import List

from lyra.abstract_domains.lattice import Lattice
from lyra.abstract_domains.state import State
from lyra.abstract_domains.store import Store
from lyra.core.expressions import Identifier, BinaryOperation, Expression, ExpressionVisitor, VariableIdentifier, \
    Literal, Input, BinaryComparisonOperation, BinaryBooleanOperation, BinaryArithmeticOperation, UnaryBooleanOperation
from lyra.core.statements import ProgramPoint
from lyra.core.types import LyraType, StringLyraType
from lyra.quality_analysis.input_checker import InputError


class CharacterInclusionState(Store, State):

    def __init__(self, variables: List[VariableIdentifier]):
        lattices = {StringLyraType: CharacterInclusionLattice}
        super().__init__(variables, lattices)

    def _assign(self, left: Expression, right: Expression) -> 'State':
        raise Exception(f"Assignment should not be called in backward analysis.")

    def _assume(self, condition: Expression) -> 'State':
        if not self.belong_here(condition.ids()):
            return self
        evaluation = ConditionEvaluator()
        map = evaluation.visit(condition)
        for k, v in map.items():
            self.store[k].meet(v)

        self.check_for_none()
        return self

    def enter_if(self) -> 'State':
        return self

    def exit_if(self) -> 'State':
        return self

    def enter_loop(self) -> 'State':
        return self

    def exit_loop(self) -> 'State':
        return self

    def _output(self, output: Expression) -> 'State':
        return self

    def raise_error(self) -> 'State':
        self.bottom()
        return self

    def _substitute(self, left: Expression, right: Expression) -> 'State':
        if not self.belong_here(left.ids().union(right.ids())):
            return self
        evaluation = ConditionEvaluator()
        expr = BinaryComparisonOperation(StringLyraType, left, BinaryComparisonOperation.Operator.Eq, right)
        map = evaluation.visit(expr)
        self.store[left] = map[left]
        self.check_for_none()
        return self

    def forget_variable(self, variable: VariableIdentifier, pp: int) -> 'Lattice':
        element = self.store[variable].copy()
        self.store[variable].top()
        return element

    def add_variable(self, variable: VariableIdentifier):
        self.store[variable] = CharacterInclusionLattice()

    def remove_variable(self, variable: VariableIdentifier):
        del self.store[variable]

    def replace_variable(self, variable: Identifier, pp: ProgramPoint):
        replacer = VariableReplacer()
        replacer.visit(pp=pp)

    def belong_here(self, vars):
        return all(var in self.variables for var in vars)

    def check_for_none(self):
        for k, v in self.store.items():
            if v is None:
                raise ValueError("This shouldn't happen.")
            v.check_for_none()

    @staticmethod
    def from_json(obj):
        if isinstance(obj, str):
            if obj[:2] == "id":
                return VariableIdentifier(StringLyraType, obj)
            elif obj == "T":
                ci = CharacterInclusionLattice()
                ci.top()
                return ci
            elif obj == "⊥":
                ci = CharacterInclusionLattice()
                ci.bottom()
                return ci
        elif "certainly" in obj and "maybe" in obj:
            ci = CharacterInclusionLattice()
            ci.certainly = CharacterInclusionState.from_json(obj["certainly"])
            ci.maybe = CharacterInclusionState.from_json(obj["maybe"])
            return ci
        elif "left" in obj and "right" in obj:
            operator = BinarySetOperation.Operator(obj["operator"])
            left = CharacterInclusionState.from_json(obj["left"])
            right = CharacterInclusionState.from_json(obj["right"])
            return BinarySetOperation(StringLyraType, left, operator, right)
        elif isinstance(obj, list):
            cs = CharSet(value=str(''.join(obj)))
            return cs


class CharacterInclusionLattice(Lattice):

    def __init__(self, certainly: Expression=None, maybe: Expression=None):
        self.A = string.printable
        self._bottom = False
        if certainly is not None and maybe is not None:
            self.certainly = certainly
            self.maybe = maybe
        else:
            self.top()
        self.check_for_none()

    def __repr__(self):
        if self.is_top():
            return "T"
        if self.is_bottom():
            return "⊥"
        return f"(C:{self.certainly}, M:{self.maybe})"


    def bottom(self):
        self._bottom = True
        self.check_for_none()
        return self

    def is_bottom(self) -> bool:
        self.check_for_none()
        return self._bottom


    def top(self):
        self.certainly = CharSet("")
        self.maybe = CharSet(self.A)
        self._bottom = False
        self.check_for_none()
        return self

    def is_top(self) -> bool:
        self.check_for_none()
        if not self.is_bottom() and isinstance(self.certainly, CharSet) and isinstance(self.maybe, CharSet):
            return self.certainly == CharSet("") and self.maybe == CharSet(self.A)
        self.check_for_none()
        return False

    # TODO define order properly
    def _less_equal(self, other: 'CharacterInclusionLattice') -> bool:
        res = self.issubset(other.certainly, self.certainly) and self.issubset(self.maybe, other.maybe)
        return res

    def _join(self, other: 'CharacterInclusionLattice') -> 'CharacterInclusionLattice':
        self.check_for_none()
        self.certainly = self.intersection(self.certainly, other.certainly)
        self.maybe = self.union(self.maybe, other.maybe)
        if not other.is_bottom:
            self._bottom = False
        self.check_for_none()
        return self

    def _meet(self, other: 'CharacterInclusionLattice'):
        self.check_for_none()
        self.certainly = self.union(self.certainly, other.certainly)
        self.maybe = self.intersection(self.maybe, other.maybe)
        if other.is_bottom:
            return other
        self.check_for_none()
        return self

    def _widening(self, other: 'CharacterInclusionLattice'):
        self.check_for_none()
        return self.join(other)

    def replace_variable(self, variable: Identifier, pp: ProgramPoint):
        replacer = VariableReplacer()
        self.certainly = replacer.visit(self.certainly, pp=pp, variable=variable)
        self.maybe = replacer.visit(self.maybe, pp=pp, variable=variable)
        pass

    def concat(self, other: 'CharacterInclusionLattice'):
        self.check_for_none()
        self.certainly = BinarySetOperation(StringLyraType, self.certainly, BinarySetOperation.Operator.Union, other.certainly)
        self.maybe = BinarySetOperation(StringLyraType, self.maybe, BinarySetOperation.Operator.Union, other.maybe)
        self.check_for_none()
        return self

    def union(self, expr1: 'Expression', expr2: 'Expression'):
        if isinstance(expr1, CharSet) and isinstance(expr2, CharSet):
            return CharSet(expr1.value.union(expr2.value))
        simple = self.simplify(expr1, expr2, BinarySetOperation.Operator.Union)
        if simple is not None:
            return simple
        return BinarySetOperation(StringLyraType, expr1, BinarySetOperation.Operator.Union, expr2)

    def intersection(self, expr1: 'Expression', expr2: 'Expression'):
        if isinstance(expr1, CharSet) and isinstance(expr2, CharSet):
            return CharSet(expr1.value.intersection(expr2.value))
        simple = self.simplify(expr1, expr2, BinarySetOperation.Operator.Intersection)
        if simple is not None:
            return simple
        return BinarySetOperation(StringLyraType, expr1, BinarySetOperation.Operator.Intersection, expr2)

    def simplify(self, expr1: 'Expression', expr2: 'Expression', operator: 'BinarySetOperation.Operator'):
        if type(expr1) is type(expr2) and expr1 == expr2:
            return deepcopy(expr1)
        if isinstance(expr1, BinarySetOperation) and isinstance(expr2, BinarySetOperation):
            if type(expr1.left) is type(expr1.right) and type(expr1.right) is type(expr2.left) and expr1.left == expr2.right and expr1.right == expr2.left:
                return deepcopy(expr1)
        if isinstance(expr1, BinarySetOperation):
            if (type(expr2) is type(expr1.left) or type(expr2) is type(expr1.right)) and (expr2 == expr1.left or expr2 == expr1.right):
                if expr1.operator == operator:
                    return deepcopy(expr1)
                else:
                    return deepcopy(expr2)
        if isinstance(expr2, BinarySetOperation):
            if (type(expr1) is type(expr2.left) or type(expr1) is type(expr2.right)) and (expr1 == expr2.left or expr1 == expr2.right):
                if expr2.operator == operator:
                    return deepcopy(expr2)
                else:
                    return deepcopy(expr1)

    def check_for_none(self):
        # if self.certainly is None or self.maybe is None:
        #     raise ValueError("This shouldn't happen.")
        pass

    def issubset(self, subset: 'Expression', superset: 'Expression'):
        # handles equal sets and also the case where both are variable identifiers
        if type(subset) is type(superset) and subset == superset:
            return True
        if isinstance(subset, VariableIdentifier) and isinstance(superset, VariableIdentifier):
            return subset == superset
        if isinstance(subset, CharSet) and isinstance(superset, CharSet):
            return subset.issubset(superset)
        if isinstance(superset, BinarySetOperation):
            return superset.issuperset(subset)
        if isinstance(subset, BinarySetOperation):
            return subset.issubset(superset)
        return False

    def to_json(self, obj=None):
        js = dict()
        if self.is_top() or self.is_bottom():
            return str(self)
        if obj is None:
            js["certainly"] = self.to_json(self.certainly)
            js["maybe"] = self.to_json(self.maybe)
            return js
        elif isinstance(obj, CharSet):
            return list(obj.value)
        elif isinstance(obj, BinarySetOperation):
            js["left"] = self.to_json(obj.left)
            js["operator"] = obj.operator.value
            js["right"] = self.to_json(obj.right)
            return js
        else:
            return str(obj)

    def check_input(self, id, line_number, start_offset, end_offset, input_value, id_value, id_input_line):
        certainly = self.evaluate_expression(self.certainly, id_value)
        maybe = self.evaluate_expression(self.maybe, id_value)
        # handling depending on erroneous value
        if isinstance(certainly, InputError):
            # make a copy of the previous error
            error = deepcopy(certainly)
            # change the position in which it will be displayed
            error.display_line = line_number
            error.start_offset = start_offset
            error.end_offset = end_offset
            return error
        if isinstance(maybe, InputError):
            error = deepcopy(maybe)
            error.display_line = line_number
            error.start_offset = start_offset
            error.end_offset = end_offset
            return error
        char_set = set(input_value)
        if not certainly.issubset(char_set):
            return InputError(code_line=id, input_line=line_number, start_offset=start_offset, end_offset=end_offset, message=f"must contain characters: {certainly}.")

        if not char_set.issubset(maybe):
            return InputError(code_line=id, input_line=line_number, start_offset=start_offset, end_offset=end_offset, message=f"must not contain characters outside the set: {maybe}.")


    def evaluate_expression(self, expr, id_val_map):
        """
        Evaluates a set expression to either a set of characters based on previously read inputs, or an InputError if the expression depends on erroneous input. To be used for input checking.
        :param expr: Expression to be evaluated. Can be of type VariableIdentifier, CharSet or BinarySetOperation
        :param id_val_map: Values of variables used for evaluation.
        :return: Either a set of characters to which the expression evaluates, or an InputError object of the expression depends on erroneous input.
        """
        if isinstance(expr, VariableIdentifier):
            expr = expr.name[2:]
            return set(id_val_map[int(expr)])
        if isinstance(expr, CharSet):
            return expr.value
        if isinstance(expr, BinarySetOperation):
            left = self.evaluate_expression(expr.left, id_val_map)
            right = self.evaluate_expression(expr.right, id_val_map)
            # if one side returns error -> the whole thing returns error
            if isinstance(left, InputError):
                return left
            if isinstance(right, InputError):
                return right
            if expr.operator == BinarySetOperation.Operator.Intersection:
                return left.intersection(right)
            if expr.operator == BinarySetOperation.Operator.Union:
                return left.union(right)


class ConditionEvaluator(ExpressionVisitor):

    def visit_Literal(self, expr: 'Literal') -> 'CharacterInclusionLattice':
        return CharacterInclusionLattice(certainly=CharSet(set(expr.val)), maybe=CharSet(set(expr.val)))

    def visit_Input(self, expr: 'Input'):
        pass

    def visit_VariableIdentifier(self, expr: 'VariableIdentifier') -> 'CharacterInclusionLattice':
        return CharacterInclusionLattice(certainly=expr, maybe=expr)

    def visit_LengthIdentifier(self, expr: 'VariableIdentifier'):
        pass

    def visit_ListDisplay(self, expr: 'ListDisplay'):
        pass

    def visit_Range(self, expr: 'Range'):
        pass

    def visit_Split(self, expr: 'Split'):
        pass

    def visit_AttributeReference(self, expr: 'AttributeReference'):
        pass

    def visit_Subscription(self, expr: 'Subscription'):
        pass

    def visit_Slicing(self, expr: 'Slicing'):
        pass

    def visit_UnaryArithmeticOperation(self, expr: 'UnaryArithmeticOperation'):
        pass

    def visit_UnaryBooleanOperation(self, expr: 'UnaryBooleanOperation'):
        expr = expr.expression
        if isinstance(expr, BinaryComparisonOperation):
            expr.operator = expr.operator.reverse_operator()
            return self.visit(expr)
        elif isinstance(expr, BinaryBooleanOperation):
            operator = expr.operator.reverse_operator()
            left = UnaryBooleanOperation(expr.left.typ, UnaryBooleanOperation.Operator.Neg, expr.left)
            right = UnaryBooleanOperation(expr.right.typ, UnaryBooleanOperation.Operator.Neg, expr.right)
            return self.visit(BinaryComparisonOperation(expr.typ, left, operator, right))

    def visit_BinaryArithmeticOperation(self, expr: 'BinaryArithmeticOperation') -> 'CharacterInclusionLattice':
        left = expr.left
        right = expr.right
        if isinstance(left, VariableIdentifier) and isinstance(right, VariableIdentifier) and expr.operator == BinaryArithmeticOperation.Operator.Add:
            if left != right:
                return self.visit(left).concat(self.visit(right))
            return self.visit(left)
        return CharacterInclusionLattice()

    def visit_BinaryBooleanOperation(self, expr: 'BinaryBooleanOperation') -> dict:
        left_map = self.visit(expr.left)
        right_map = self.visit(expr.right)
        new_map = dict()
        operation = {
            BinaryBooleanOperation.Operator.Or: "join",
            BinaryBooleanOperation.Operator.And: "meet"
        }
        all_keys = set(left_map.keys()).union(set(right_map.keys()))
        for key in all_keys:
            if key in left_map and key in right_map:
                new_map[key] = getattr(left_map[key], operation[expr.operator])(right_map[key])
            else:
                new_map[key] = left_map[key] if key in left_map else right_map[key]
        return new_map

    def visit_BinaryComparisonOperation(self, expr: 'BinaryComparisonOperation') -> dict:
        left = expr.left
        right = self.visit(expr.right)
        map = dict()
        if isinstance(left, VariableIdentifier):
            if expr.operator == BinaryComparisonOperation.Operator.Eq:
                map[left] = right
        return map


class VariableReplacer(ExpressionVisitor):

    def visit_Literal(self, expr: 'Literal'):
        pass

    def visit_Input(self, expr: 'Input'):
        pass

    def visit_VariableIdentifier(self, expr: 'VariableIdentifier', pp: ProgramPoint, variable: 'VariableIdentifier'):
        if expr == variable:
            return VariableIdentifier(expr.typ, f"id{pp.line}")
        else:
            return expr

    def visit_LengthIdentifier(self, expr: 'VariableIdentifier'):
        pass

    def visit_ListDisplay(self, expr: 'ListDisplay'):
        pass

    def visit_Range(self, expr: 'Range'):
        pass

    def visit_Split(self, expr: 'Split'):
        pass

    def visit_AttributeReference(self, expr: 'AttributeReference'):
        pass

    def visit_Subscription(self, expr: 'Subscription'):
        pass

    def visit_Slicing(self, expr: 'Slicing'):
        pass

    def visit_UnaryArithmeticOperation(self, expr: 'UnaryArithmeticOperation'):
        pass

    def visit_UnaryBooleanOperation(self, expr: 'UnaryBooleanOperation'):
        pass

    def visit_BinaryArithmeticOperation(self, expr: 'BinaryArithmeticOperation'):
        pass

    def visit_BinaryBooleanOperation(self, expr: 'BinaryBooleanOperation'):
        pass

    def visit_BinaryComparisonOperation(self, expr: 'BinaryComparisonOperation'):
        pass

    def visit_BinarySetOperation(self, expr: 'BinarySetOperation', pp:'ProgramPoint', variable:'VariableIdentifier'):
        left = self.visit(expr.left, pp, variable)
        right = self.visit(expr.right, pp, variable)
        return BinarySetOperation(expr.typ, left, expr.operator, right)

    def visit_CharSet(self, expr: 'CharSet', *args, **kwargs):
        return expr


class BinarySetOperation(BinaryOperation):

    class Operator(BinaryOperation.Operator):
        """Binary arithmetic operator representation."""
        Intersection = 1
        Union = 2

        def reverse_operator(self):
            """Returns the reverse operator of this operator."""
            if self.value == 1:
                return BinarySetOperation.Operator.Union
            elif self.value == 2:
                return BinarySetOperation.Operator.Intersection

        def __str__(self):
            return "∪" if self.value == 2 else "∩"

    def __init__(self, typ: LyraType, left: Expression, operator: Operator, right: Expression):
        """Binary boolean operation expression representation.

        :param typ: type of the operation
        :param left: left expression of the operation
        :param operator: operator of the operation
        :param right: right expression of the operation
        """
        super().__init__(typ, left, operator, right)

    def issuperset(self, other:'Expression'):
        """
        Checks if other value is a subset if the current expression
        :param other:
        :return:
        """
        if (type(other) is type(self.right) and other == self.right) or (type(other) is type(self.left) and other == self.left):
            return self.operator == BinarySetOperation.Operator.Union
        return False

    def issubset(self, other: 'Expression'):
        if (type(other) is type(self.right) and other == self.right) or (type(other) is type(self.left) and other == self.left):
            return self.operator == BinarySetOperation.Operator.Intersection
        return False
"""
CharSet class
    Class to represent a set of characters. Inherits Expression so that it can be incorporated in a BinarySetOperation with other expressions.
===
"""

class CharSet(Expression):

    def __init__(self, value: str):
        self.value = set(value)

    def __eq__(self, other: 'CharSet'):
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        return str(self.value)

    def issubset(self, other: 'CharSet'):
        return self.value.issubset(other.value)