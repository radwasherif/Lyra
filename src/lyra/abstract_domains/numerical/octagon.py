
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

    def __init__(self, dim: int, rev_dict: dict):
        self.dim = dim
        self.rev_dict = rev_dict
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

    def join(self, other):
        # self.print_constraints("self before join")
        # other.print_constraints("other before join")
        self.abstract = elina_abstract0_join(self.man, False, self.abstract, other.abstract)
        self.equalize()
        # self.print_constraints("after join")


    #TODO: might want to change right to Expression/BinaryArithmeticOperation
    def substitute(self, vi: int, vars: [int], signs: [int], c: int):
        print(f"inside substitution {vi, vars, signs, c}")
        linexpr = self.create_linexpr(vars, signs, c)
        elina_linexpr0_print(linexpr, None)
        # print(vi, vj, c)
        self.abstract = elina_abstract0_substitute_linexpr(self.man, False, self.abstract, ElinaDim(vi), linexpr, None)
        self.equalize()
        # self.print_constraints("substitute")

    def widening(self, other):
        self.abstract = elina_abstract0_widening(self.man, self.abstract, other.abstract)
        self.equalize()
        self.print_constraints("widening")



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

    def equalize(self):
        self.lincons_array = elina_abstract0_to_lincons_array(self.man, self.abstract)

    def print_constraints(self, message: str):
        print(message)
        elina_lincons0_array_print(self.lincons_array, None)
        print("-----------------------------------------------------------")

    def to_string (self):
        lincons_array = self.lincons_array
        string = ""
        # print("In OCT REPR")
        # elina_lincons0_array_print(lincons_array, None)
        if self.is_top():
            return "TOP"
        if self.is_bottom():
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
                coeff = linterm.coeff
                # print(f"COEFF = {coeff.val.scalar.contents.val}, {elina_coeff_equal_int(coeff, 1)}")
                string += (" + " if elina_coeff_equal_int(coeff, 1) else " - ")
                string += (self.rev_dict[linterm.dim])

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


class OctagonDomain(State):
    def __init__(self, variables: List[VariableIdentifier]):
        self.variables = variables
        self.dict = self.generate_dict()
        self.rev_dict = {v: k for k, v in self.dict.items()}
        # print(self.rev_dict)
        self.elina = Elina(dim=len(variables), rev_dict= self.rev_dict)

    def __repr__(self):
        return self.elina.to_string()


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
        vi, vars, signs, c = self.check_expressions(left, right)
        self.elina.substitute(vi, vars, signs, c)
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

    # ==================================================
    #             HELPER FUNCTIONS
    # ==================================================

    def check_expressions(self, left: Expression, right: Expression):
        """

        :param left:
        :param right:
        :return:

        """
        print(f"left {left}, right {right}")
        vi, vj, c, = None, None, None
        var_ids, signs, c = self.normalize_arithmetic(right)
        if isinstance(left, VariableIdentifier):
            vi = self.dict[left.name]
            if len(var_ids) > 1:
                raise ValueError(f"For now we only support substitution with at most one variable, {right} doesn't work")
            vars = [self.dict[id.name] for id in var_ids]
        return vi, vars[:1], signs[:1], c


    def check_condition(self, condition: Expression):
        '''
        So far only checking for expression of the form x + y [comparison operator] c
        :param condition: condition to be checked
        :return:
        '''
        # print(f"Checking condition {condition}")
        negation_free_normal = NegationFreeNormalExpression()
        normal_condition = negation_free_normal.visit(condition)
        print(f"Normalized condition {normal_condition}")
        # print(Expression._walk(normal_condition))
        vars, signs = [], []
        expr = normal_condition.left # x + y - c
        var_ids, signs, c = self.normalize_arithmetic(expr)
        # print(f"Normalized arithmetic expression {expr}")
        vars = [self.dict[id.name] for id in var_ids]
        return vars, signs, c

    def normalize_arithmetic(self, expr: Expression):
        """

        :param expr: Linear expression with 1 coefficients and any number of constant terms
        :return: new expression of the form ((+/-v1) + (+/-v2) + (+/-v3) + ... ) + C, where C = sum of all constants in         expr
        """
        vars, signs = self.flatten_expr(expr, 1)
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
        return vars, signs, constant

    def flatten_expr(self, expr: Expression, sign: int):
        """
        
        :param expr: Expression to be flattened
        :param sign: Keeping track of the sign of the current expression
        :return: array of VariableIdentifier and Literal, array of signs that correspond to each VariableIdentifier/Literal, 1 for positive, -1 for negative
        """
        if isinstance(expr, VariableIdentifier) or isinstance(expr, Literal):
            return [expr], [sign]
        if isinstance(expr, BinaryArithmeticOperation):
            expr_right, sign_right = self.flatten_expr(expr.left, sign)
            expr_left, sign_left = self.flatten_expr(expr.right,
                                                sign if expr.operator == BinaryArithmeticOperation.Operator.Add else -sign)
            return expr_right + expr_left, sign_right + sign_left
        if isinstance(expr, UnaryArithmeticOperation):
            return self.flatten_expr(expr.expression, sign if expr.operator == UnaryArithmeticOperation.Operator.Add else -sign)
