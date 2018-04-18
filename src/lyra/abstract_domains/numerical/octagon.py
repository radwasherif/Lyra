
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
from elina.python_interface.elina_coeff import *
from elina.python_interface.elina_coeff_h import *
from elina.python_interface.elina_scalar import *
from elina.python_interface.elina_scalar_h import *

import gc

class Elina:

    def __init__(self, dim):
        self.dim = dim
        self.man = opt_oct_manager_alloc()
        self.abstract = self.top()
        self.equalize()

    def copy(self):
        copy = Elina(self.dim)
        copy.abstract =  elina_abstract0_copy(self.man, self.abstract)
        copy.equalize()
        return copy

    def top(self):
        return elina_abstract0_top(self.man, self.dim, 0)

    def bottom(self):
        return elina_abstract0_bottom(self.man, self.dim, 0)

    def is_top(self):
        return elina_abstract0_is_top(self.man, self.abstract)

    def is_bottom(self):
        return elina_abstract0_is_bottom(self.man, self.abstract)

    def is_leq(self, other):
        return elina_abstract0_is_leq(self.man, self.abstract, other.abstract)

    def create_linexpr(self, var, sign, c):
        """
        Return Elina linear expression sign[0]var[0]  sign[1]var[1] +c
        :param var: list of variables involved in the expression, as indexes
        :param sign: signs corresponding to every variable
        :param c: the constant of the expression
        :return: Elina linear expression
        """
        if len(var) != len(sign):
            raise ValueError("var and sign should have the same length")

        size = len(var)
        if size > 2:
            raise ValueError("The size of each constraint of the Octagons domain should be 2 at most")
        linexpr = elina_linexpr0_alloc(ElinaLinexprDiscr.ELINA_LINEXPR_SPARSE, size)
        if(c is not None):
            cst = pointer(linexpr.contents.cst)
            # set the constant of the expression to c
            elina_scalar_set_int(cst.contents.val.scalar, c_long(c))
            # set the variables and coefficients (signs) of the linear expression
        for i in range(size):
            linterm = pointer(linexpr.contents.p.linterm[i])
            linterm.contents.dim = ElinaDim(var[i])
            coeff = pointer(linterm.contents.coeff)
            elina_scalar_set_double(coeff.contents.val.scalar, sign[i])

        return linexpr

    def add_linear_constr(self, var: List[int], sign: List[int], c: int):
        #flip signs and constant
        linexpr = self.create_linexpr(var, sign, c)
        lincons_array = elina_lincons0_array_make(1)
        #change expression from expr <=0 to -expr >= 0
        lincons_array.p[0].constyp = ElinaConstyp.ELINA_CONS_SUPEQ
        lincons_array.p[0].linexpr0 = linexpr
        top = self.top()
        self.abstract = elina_abstract0_meet_lincons_array(self.man, False, self.abstract, lincons_array)
        self.equalize()
        self.print_constraints("add linear constraint" + str(var) + str(sign))

    def join(self, other):
        # self.print_constraints("self before join")
        # other.print_constraints("other before join")
        self.abstract = elina_abstract0_join(self.man, False, self.abstract, other.abstract)
        self.equalize()
        # self.print_constraints("after join")


    #TODO: might want to change right to Expression/BinaryArithmeticOperation
    def substitute(self, vi: int, vj: int, c: int):
        (var, sign) = ([vj], [1]) if vj is not None else ([], [])
        print(f"inside substitution {vi, vj, c}")
        linexpr = self.create_linexpr(var, sign, c)
        elina_linexpr0_print(linexpr, None)
        # print(vi, vj, c)
        print(ElinaDim(vi))
        self.abstract = elina_abstract0_substitute_linexpr(self.man, False, self.abstract, ElinaDim(vi), linexpr, None)
        self.equalize()
        # self.print_constraints("substitute")

    def widening(self, other):
        self.abstract = elina_abstract0_widening(self.man, self.abstract, other.abstract)
        self.equalize()
        self.print_constraints("widening")


    def equalize(self):
        self.lincons_array = elina_abstract0_to_lincons_array(self.man, self.abstract)

    def print_constraints(self, message: str):
        print(message)
        elina_lincons0_array_print(self.lincons_array, None)
        print("-----------------------------------------------------------")

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        lincons_array = self.lincons_array
        string = ""
        # print("In REPR")
        elina_lincons0_array_print(lincons_array, None)
        if(self.is_top()):
            return "TOP"
        if(self.is_bottom()):
            return "BOTTOM"
        counter = 0
        # print (lincons_array.size)
        for j in range(lincons_array.size):
            lincons = lincons_array.p[j]
            # print("outer loop " + str(counter))
            counter+=1

            # c = lincons.linexpr0.contents.cst
            # print (lincons.linexpr0.contents.cst.val.scalar.contents.val.dbl)
            #elina_scalar_fprint(cstdout, lincons.linexpr0.cst.val.scalar)
            for i in range(lincons.linexpr0.contents.size):
                # print("inner " + str(i))
                linterm = lincons.linexpr0.contents.p.linterm[i]
                string += ("x" + str(linterm.dim))
                coeff = linterm.coeff
                string += (" + " if coeff == 1 else " - ")
                # print(string)
            if lincons.constyp == ElinaConstyp.ELINA_CONS_SUPEQ:
                string += " >= "
                # print(string)
            elif lincons.constyp == ElinaConstyp.ELINA_CONS_SUP:
                string += " > "
                # print(string)
            elif lincons.constyp == ElinaConstyp.ELINA_CONS_EQ:
                string += " = "
                # print(string)
            string += str(lincons.linexpr0.contents.cst.val.scalar.contents.val.dbl)
            string += "\n"
        # print(string)
        # print(type(string))
        return string


class OctagonDomain(State):
    def __init__(self, variables: List[VariableIdentifier]):
        self.variables = variables
        self.dict = self.generate_dict()
        self.elina = Elina(dim=len(variables))

    def __repr__(self):
        lincons_array = self.elina.lincons_array
        string = ""
        # print("In OCT REPR")
        # elina_lincons0_array_print(lincons_array, None)
        if (self.is_top()):
            return "TOP"
        if (self.is_bottom()):
            return "BOTTOM"
        counter = 0
        # print(lincons_array.size)
        for j in range(lincons_array.size):
            lincons = lincons_array.p[j]
            # print("outer loop " + str(counter))
            counter += 1

            # c = lincons.linexpr0.contents.cst
            # print(lincons.linexpr0.contents.cst.val.scalar.contents.val.dbl)
            # elina_scalar_fprint(cstdout, lincons.linexpr0.cst.val.scalar)
            for i in range(lincons.linexpr0.contents.size):
                # print("inner " + str(i))
                linterm = lincons.linexpr0.contents.p.linterm[i]
                string += ("x" + str(linterm.dim))
                coeff = linterm.coeff
                string += (" + " if coeff == 1 else " - ")
                # print(string)
            if lincons.constyp == ElinaConstyp.ELINA_CONS_SUPEQ:
                string += " >= "
                print(string)
            elif lincons.constyp == ElinaConstyp.ELINA_CONS_SUP:
                string += " > "
                # print(string)
            elif lincons.constyp == ElinaConstyp.ELINA_CONS_EQ:
                string += " = "
                # print(string)
            string += str(lincons.linexpr0.contents.cst.val.scalar.contents.val.dbl)
            string += "\n"
        # print(string)
        # print(type(string))
        return string


    def generate_dict(self):
        """
        :return: dictionary in which every Lyra variable is mapped to an integer index to be passed to Elina
        """
        return {var.name: i for i, var in enumerate(set(self.variables))}


    def _assign(self, left: Expression, right: Expression) -> 'State':
        print("ASSIGN")
        return self

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
        return self.bottom()

    def _substitute(self, left: Expression, right: Expression) -> 'State':
        self.elina.print_constraints("before substitute")
        if(isinstance(right, Input)):
            return self
        vi, vj, c = self.check_expressions(left, right)
        self.elina.substitute(vi, vj, c)
        self.elina.print_constraints("after substitute")
        return self

    def bottom(self):
        self.elina.abstract = self.elina.bottom()
        self.elina.equalize()
        return self

    def top(self):
        self.elina.abstract = self.elina.top()
        self.elina.equalize()
        return self
    def is_bottom(self) -> bool:
        return self.elina.is_bottom()

    def is_top(self) -> bool:
        return self.elina.is_top()

    def _less_equal(self, other: 'Lattice') -> bool:
        return self.elina.is_leq(other.elina)

    def _join(self, other: 'Lattice') -> 'Lattice':
        self.elina.join(other.elina)
        return self

    def _meet(self, other: 'Lattice'):
        print(f"in _meet, condiiton {other}")
        var, sign, c = self.check_condition(other)
        self.elina.add_linear_constr(var, sign, c)
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
        :return: 1 if vi <- c, 2 if vi <- vj + c, 3 if vi <- c + vj, 0 otherwise

        """
        vi, vj, c, = None, None, None
        if isinstance(left, VariableIdentifier):
            #if assignment is of the form v <- c
            if isinstance(right, Literal) and isinstance(right.typ, IntegerLyraType):
                vi, vj, c = self.dict[left.name], None, int(right.val)
            elif isinstance(right, BinaryArithmeticOperation):
                #if assignment is of the form v <- v + c
                if isinstance(right.right, VariableIdentifier) and isinstance(right.left, Literal) and isinstance(right.left.typ, IntegerLyraType):
                    vi, vj, c = self.dict[left.name], self.dict[right.right.name], int(right.left.val)
                #if assignment is of the form v <- c + v
                if isinstance(right.left, VariableIdentifier) and isinstance(right.right, Literal) and isinstance(
                        right.left.typ, IntegerLyraType):
                    vi, vj, c = self.dict[left.name], self.dict[right.left.name], int(right.right.val)
            elif isinstance(right, VariableIdentifier):
                    vi, vj, c = self.dict[left.name], self.dict[right.name], None

        return vi, vj, c


    def check_condition(self, condition: Expression):
        '''
        So far only checking for expression of the form x + y (op) c
        :param condition: condition to be checked
        :return:
        '''
        # print(f"Checking condition {condition}")
        negation_free_normal = NegationFreeNormalExpression()
        normal_condition = negation_free_normal.visit(condition)
        print(f"Normalized condition {normal_condition}")
        # print(Expression._walk(normal_condition))
        var, sign = [], []
        expr = normal_condition.left # x + y - c
        expr = normalize_arithmetic(expr)
        print(f"Normalized arithmetic expression {expr}")

        left = expr.left
        if(isinstance(left, UnaryArithmeticOperation)):
            sign= [1 if left.operator == UnaryArithmeticOperation.Operator.Add else -1]
            var = [self.dict[left.expression.name]]
        else:
            print(f"left {left}")
            ll = left.left
            lr = left.right
            sign = [1 if ll.operator == UnaryArithmeticOperation.Operator.Add else -1, 1 if lr.operator == UnaryArithmeticOperation.Operator.Add else -1]
            var = [self.dict[ll.expression.name], self.dict[lr.expression.name]]
        right = expr.right
        c = int(right.expression.val)
        c = -c if right.operator == UnaryArithmeticOperation.Operator.Sub else c

        return var, sign, c

def normalize_arithmetic(expr: Expression):
    vars, signs = flatten_expr(expr, 1)
    constant = 0
    idx_to_del = []
    #calculate the total sum of all constants (Literals)
    for i, v in enumerate(vars):
        if(isinstance(v, Literal)):
            constant += (signs[i] * (int(v.val)))
            idx_to_del.append(i)

    #remove Literals from array so that only variables remain
    for i in sorted(idx_to_del, reverse=True):
        del vars[i]
        del signs[i]

    if len(vars) > 2:
        raise ValueError("Expression should have only 2 variables")
    ll = UnaryArithmeticOperation(IntegerLyraType, UnaryArithmeticOperation.Operator.Add if signs[0] == 1 else UnaryArithmeticOperation.Operator.Sub, vars[0])
    if(len(vars) == 2):
        lr = UnaryArithmeticOperation(IntegerLyraType, UnaryArithmeticOperation.Operator.Add if signs[1] == 1 else UnaryArithmeticOperation.Operator.Sub, vars[1])
        left = BinaryArithmeticOperation(IntegerLyraType, ll, BinaryArithmeticOperation.Operator.Add, lr)
    else:
        left = ll
    literal = Literal(IntegerLyraType, str(abs(constant)))
    C = UnaryArithmeticOperation(IntegerLyraType, UnaryArithmeticOperation.Operator.Sub if constant < 0 else UnaryArithmeticOperation.Operator.Add, literal)
    return  BinaryArithmeticOperation(IntegerLyraType, left, BinaryArithmeticOperation.Operator.Add, C)

def flatten_expr(expr: Expression, sign: int):
    if isinstance(expr, VariableIdentifier) or isinstance(expr, Literal):
        return [expr], [sign]
    if isinstance(expr, BinaryArithmeticOperation):
        expr_right, sign_right = flatten_expr(expr.left, sign)
        expr_left, sign_left = flatten_expr(expr.right,
                                            sign if expr.operator == BinaryArithmeticOperation.Operator.Add else -sign)
        return expr_right + expr_left, sign_right + sign_left
    if isinstance(expr, UnaryArithmeticOperation):
        return flatten_expr(expr.expression, sign if expr.operator == UnaryArithmeticOperation.Operator.Add else -sign)
