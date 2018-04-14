
from typing import List
from lyra.core.expressions import *
from lyra.abstract_domains.state import State
from elina.python_interface.elina_auxiliary_imports import *
from elina.python_interface.opt_oct import *
# from elina.python_interface.test_imports import *
from elina.python_interface.elina_scalar import *
from elina.python_interface.elina_lincons0 import *
from elina.python_interface.elina_lincons0_h import *
from elina.python_interface.elina_manager import *
from elina.python_interface.elina_abstract0 import *
from elina.python_interface.elina_linexpr0 import *
from elina.python_interface.elina_linexpr0_h import *
from elina.python_interface.elina_dimension_h import *

import gc

class Elina:

    def __init__(self, vars: List[VariableIdentifier]):
        self.vars = vars
        self.man = opt_oct_manager_alloc()
        self.map = self.var_map(vars)
        self.dict = self.var_dict(vars)
        self.lincons_array = None
        self.elina_abstract = self.top()
        self.comp_op = {
            BinaryComparisonOperation.Operator.Lt: ElinaConstyp.ELINA_CONS_SUP,
            BinaryComparisonOperation.Operator.LtE: ElinaConstyp.ELINA_CONS_SUPEQ,
            BinaryComparisonOperation.Operator.Eq: ElinaConstyp.ELINA_CONS_EQ,
            BinaryComparisonOperation.Operator.Gt: ElinaConstyp.ELINA_CONS_SUP,
            BinaryComparisonOperation.Operator.GtE: ElinaConstyp.ELINA_CONS_SUPEQ
        }

    #TODO: Potential issue: if the conversion from Elina abstract
    def copy(self):
        copy = Elina(self.vars)
        copy.elina_abstract =  elina_abstract0_copy(self.man, self.elina_abstract)
        copy.lincons_array = elina_abstract0_to_lincons_array(copy.man, copy.elina_abstract)
        return copy

    def top(self):
        return elina_abstract0_top(self.man, len(self.map), 0)

    def bottom(self):
        return elina_abstract0_bottom(self.man, len(self.map), 0)

    def is_top(self):
        return elina_abstract0_is_top(self.man, self.elina_abstract)

    def is_bottom(self):
        return elina_abstract0_is_bottom(self.man, self.elina_abstract)

    """
        return: array that maps every variable number in Elina to its original program variable name
    """
    def var_map(self, vars: List[VariableIdentifier]):
        return [i for i in range(len(vars))]


    def var_dict(self, vars: List[VariableIdentifier]):
        """

        :param vars: list of variables of the program
        :return: dictionary in which every Lyra variable is mapped to an Elina variable index
        """
        return {var.name:i for i, var in enumerate(vars)}

    def create_linexpr(self, size, var, sign, c):
        """
        Return Elina linear expression sign[0]var[0]  sign[1]var[1] +c
        :param size: size of the linear expression
        :param var: list of indexes of variables
        :param sign: signs corresponding to every variable
        :param c: the constant of the expression
        :return: Elina linear expression
        """
        if size > 2:
            print("Size shouldn't be greater than 2")
            return None
        linexpr0 = elina_linexpr0_alloc(ElinaLinexprDiscr.ELINA_LINEXPR_SPARSE, size)
        cst = pointer(linexpr0.contents.cst)
        # set the constant of the expression to c
        elina_scalar_set_int(cst.contents.val.scalar, c_long(c))
        # let the variables and coefficients (signs) of the linear expression
        for i in range(size):
            linterm = pointer(linexpr0.contents.p.linterm[i])
            linterm.contents.dim = ElinaDim(var[i])
            coeff = pointer(linterm.contents.coeff)
            elina_scalar_set_double(coeff.contents.val.scalar, sign[i])

        return linexpr0

    def add_linear_constr(self, condition: BinaryComparisonOperation):
        # print(condition)
        c = int(condition.right.val)
        left = condition.left
        x = left.left.name
        y = left.right.name
        var = [self.dict[x], self.dict[y]]
        sign = [1, 1]
        if left.operator.value == BinaryArithmeticOperation.Operator.Sub:
            sign[1] = -1
        if condition.operator.value == BinaryComparisonOperation.Operator.Lt or condition.operator.value == BinaryComparisonOperation.Operator.LtE:
            sign = list(map(lambda x: -x, sign))
        lin_expr = self.create_linexpr(2, var, sign, c)
        lincons_array = elina_lincons0_array_make(1)
        lincons_array.p[0].constyp = self.comp_op[condition.operator]
        lincons_array.p[0].linexpr0 = lin_expr
        top = self.top()
        self.elina_abstract = elina_abstract0_meet_lincons_array(self.man, False, self.elina_abstract, lincons_array)
        self.lincons_array = elina_abstract0_to_lincons_array(self.man, self.elina_abstract)

    #TODO: might want to change right to Expression/BinaryArithmeticOperation
    def substitue(self, left: VariableIdentifier, right: Expression, type: int):

        if type == 0:
            return self
        dim = int(self.dict[left.name])
        var, sign, c = [], [], None
        if type == 1: # v <-- c
            c = int(right.val)
        elif type == 2: # v <-- v + c
            x = right.left.name
            var = [self.dict[x]]
            sign = [1]
            c = int(right.right.val)
            c = -c if right.operator.value == BinaryArithmeticOperation.Operator.Sub else c
        else: # v <-- c + v
            x = right.right.name
            var [self.dict[x]]
            sign = [1]
            c = -c if right.operator.value == BinaryArithmeticOperation.Operator.Sub else c
        linexpr = self.create_linexpr(len(var), var, sign, c)
        self.elina_abstract = elina_abstract0_substitute_linexpr(self.man, False, self.elina_abstract, dim, linexpr, 1)
        self.lincons_array = elina_abstract0_to_lincons_array(self.elina_abstract)

    def widening(self, other):
        self.elina_abstract = elina_abstract0_widening(self.man, self.elina_abstract, other.elina_abstract)
        self.lincons_array = elina_abstract0_to_lincons_array(self.elina_abstract)



class OctagonDomain(State):
    def __init__(self, variables: List[VariableIdentifier]):
        self.variables = variables
        self.elina = Elina(variables)

    def _assign(self, left: Expression, right: Expression) -> 'State':
        pass

    def _assume(self, condition: Expression) -> 'State': #MEET
        return self._meet(condition)


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
        return self

    def _substitute(self, left: Expression, right: Expression) -> 'State':
        self.elina.substitue(left, right, self.check_expressions(left, right))
        return self

    def bottom(self):
        self.elina.octagon = self.elina.bottom()
        return self

    def top(self):
        self.elina.octagon = self.elina.top()
        return self
    def is_bottom(self) -> bool:
        return self.elina.is_bottom()

    def is_top(self) -> bool:
        return self.elina.is_top()

    def _less_equal(self, other: 'Lattice') -> bool:
        oct = other
        return elina_abstract0_is_leq(self.man, self.elina.elina_abstract, oct.elina.elina_abstract)

    def _join(self, other: 'Lattice') -> 'Lattice':
        pass

    def _meet(self, other: 'Lattice'):

        expr = self.check_condition(other)
        print(expr)
        if expr is not None:
            self.elina.add_linear_constr(other)
        else:
            self.bottom()

        return self

    def _widening(self, other: 'Lattice'):
        self.elina.widening(other.elina)
        return self

    def copy(self):
        copy = OctagonDomain(self.variables)
        copy.elina = self.elina.copy()
        return copy

    def check_expressions(self, left: Expression, right: Expression):
        """

        :param left:
        :param right:
        :return: 1 if v <- c, 2 if v <- v + c, 3 if v <- c + v, 0 otherwise

        """
        if isinstance(left, VariableIdentifier):
            #if assignment is of the form v <- c
            if isinstance(right, Literal) and isinstance(right.typ, IntegerLyraType):
                return 1
            elif isinstance(right, BinaryArithmeticOperation):
                #if assignment is of the form v <- v + c
                if isinstance(right.right, VariableIdentifier) and isinstance(right.left, Literal) and isinstance(right.left.typ, IntegerLyraType):
                    return 2
                #if assignment is of the form v <- c + v
                if isinstance(right.left, VariableIdentifier) and isinstance(right.right, Literal) and isinstance(
                        right.left.typ, IntegerLyraType):
                    return 3

        return 0

    #for now checking only for expressions of the form x + y > 2
    def check_condition(self, condition: Expression):
        new_condition = condition
        if isinstance(condition, UnaryBooleanOperation) and condition.operator.value == UnaryBooleanOperation.Operator.Neg:
            new_condition = condition.expression
            # print(new_condition.__str__())
            # new_condition.operator(new_condition.operator.reverse_operator())

        left = new_condition.left
        right = new_condition.right
        if isinstance(new_condition, BinaryComparisonOperation):

            if isinstance(left, BinaryArithmeticOperation) and isinstance(left.left, VariableIdentifier) and isinstance(left.right, VariableIdentifier) and isinstance(right, Literal):

                return new_condition

        return None


