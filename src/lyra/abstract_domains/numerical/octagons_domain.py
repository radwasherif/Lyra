
from typing import List

from lyra.abstract_domains.lattice import Lattice
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
from elina.python_interface.elina_dimension import *

import gc

from lyra.core.statements import ProgramPoint


class ElinaLattice(Lattice):

    def __init__(self, dim: int, idx_to_varname: dict):
        self.dim = dim
        self.idx_to_varname = idx_to_varname
        self.man = opt_oct_manager_alloc()
        self.abstract = self.top()
        self.equate()

    def __repr__(self):
        return self.to_string()

    def copy(self):
        copy = ElinaLattice(self.dim, self.idx_to_varname)
        copy.abstract = elina_abstract0_copy(self.man, self.abstract)
        copy.equate()
        return copy

    def top(self):
        return elina_abstract0_top(self.man, self.dim, 0)

    def bottom(self):
        return elina_abstract0_bottom(self.man, self.dim, 0)

    def is_top(self):
        return elina_abstract0_is_top(self.man, self.abstract)

    def is_bottom(self):
        return elina_abstract0_is_bottom(self.man, self.abstract)

    def _less_equal(self, other: 'ElinaLattice'):
        return elina_abstract0_is_leq(self.man, self.abstract, other.abstract)

    def _join(self, other: 'ElinaLattice'):
        # self.print_constraints("self before join")
        # other.print_constraints("other before join")
        self.abstract = elina_abstract0_join(self.man, False, self.abstract, other.abstract)
        self.equate()
        return self
        # self.print_constraints("after join")

    def _meet(self, other: 'ElinaLattice'):
        self.abstract = elina_abstract0_meet(self.man, False, self.abstract, other.abstract)
        self.equate()
        return self

    def substitute(self, vi: int, vars: [int], signs: [int], c: int):
        # print(f"inside substitution {vi, vars, signs, c}")
        linexpr = self.create_linexpr(vars, signs, c)
        elina_linexpr0_print(linexpr, None)
        # print(vi, vj, c)
        self.abstract = elina_abstract0_substitute_linexpr(self.man, False, self.abstract, ElinaDim(vi), linexpr, None)
        self.equate()
        # self.print_constraints("substitute")

    def _widening(self, other):
        self.abstract = elina_abstract0_widening(self.man, self.abstract, other.abstract)
        self.equate()
        # self.print_constraints("widening")

    def replace_variable(self, variable: Identifier, pp: ProgramPoint):
        for idx, varname in self.idx_to_varname.items():
            if varname == variable.name:
                self.idx_to_varname[idx] = f"id{pp.line}"

    # ==================================================
    #             HEURISTICS
    # ==================================================

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
        linexpr = self.create_linexpr(var, sign, c)
        lincons_array = elina_lincons0_array_make(1)
        lincons_array.p[0].constyp = ElinaConstyp.ELINA_CONS_SUPEQ
        lincons_array.p[0].linexpr0 = linexpr
        top = self.top()
        self.abstract = elina_abstract0_meet_lincons_array(self.man, False, self.abstract, lincons_array)
        self.equate()


    def add_dim(self, var_name: str):
        """
            Adding dimension to Elina abstract to accommodate new variable
        :param var_name: name of the new variable to be added
        :return:
        """
        # create dimchange array and add the index of the new variable to it
        dimchange = elina_dimchange_alloc(0, 1)
        dimchange.dim[0] = self.dim
        # add the new dimension to Elina
        self.abstract = elina_abstract0_add_dimensions(self.man, False, self.abstract, dimchange, False)
        # update dictionary of Elina with the new variable
        self.idx_to_varname[self.dim] = var_name
        # update the number of dimensions of Elina
        self.dim += 1
        # equate ElinaAbstract with ElinaLinconsArray
        self.equate()

    def remove_dim(self, dim: int):
        """
            Removing dimension from Elina Abstract as a result of variable being removed
        :param dim: index of dimension to be removed
        :return:
        """
        # create dimchange array with the variable to be removed
        dimchange = elina_dimchange_alloc(0, 1)
        dimchange.contents.dim[0] = dim
        # remove variable from Elina
        self.abstract = elina_abstract0_remove_dimensions(self.man, False, self.abstract, dimchange)
        # update dictionary (Elina index -> variable name) accordingly
        for k,v in self.idx_to_varname.items():
            # every index that is greater than the removed index is decremented
            if k > dim:
                self.idx_to_varname[k-1] = self.idx_to_varname.pop(k)
        # equate ElinaAbstract with ElinaLinconsArray
        self.equate()

    def extract_dim(self, dim:int):
        """
            Find all constraints in which a certain variable is involved
        :param dim: dimension whose constraints should be returned
        :return: new Elina object with constraints related to a certain variable
        """
        # call closure to make sure all possible constraints are captured
        self.abstract = elina_abstract0_closure(self.man, False, self.abstract)
        # equate Elina abstract with ELina lincons_array
        self.equate()
        size = 0
        # allocate new lincons_array
        lincons_array = elina_lincons0_array_make(size)
        new_dict = {}
        # iterate over all constraints in the lincons_array
        for i in range(self.lincons_array.size):
            lincons = self.lincons_array.p[i]
            for i in range(lincons.linexpr0.contents.size):
                linterm = lincons.linexpr0.contents.p.linterm[i]
                cur_dim = linterm.dim
                # if the current constraint contains the desired dimension
                if cur_dim == dim:
                    # increment result array by 1
                    elina_lincons0_array_resize(lincons_array, size+1)
                    # add copy of lincons to result array
                    lincons_array.p[size] = elina_lincons0_copy(lincons)
                    # increment size
                    size += 1
                    # create a new dictionary to be passed to the resulting elina object
                    for j in range(lincons.linexpr0.contents.size):
                        l = lincons.linexpr0.contents.p.linterm[j]
                        new_dict[l.dim] = self.idx_to_varname[l.dim]
                    break
        new_elina = ElinaLattice(dim=len(new_dict), idx_to_varname=new_dict)
        new_elina.lincons_array = lincons_array
        new_elina.abstract = elina_abstract0_of_lincons_array(new_elina.man, size, 0, lincons_array)
        # if self.idx_to_varname[dim] == 'x':
        #     print("SIZE", size)
        #     self.print_constraints(f"original{dim}")
        #     print("after extraction")
        #     elina_lincons0_array_print(lincons_array, None)
        #     new_elina.print_constraints("NEW ELINA")
        #     print(elina_abstract0_is_top(new_elina.man, new_elina.abstract))
        #     print(new_elina.is_top())
        return new_elina


    def project(self, dim:int):
        """
        Performs the project/forget operation of the given dimension
        :param
        """
        self.abstract = elina_abstract0_forget_array(self.man, False, self.abstract, ElinaDim(dim), 1, False)
        self.equate()

    def equate(self):
        self.lincons_array = elina_abstract0_to_lincons_array(self.man, self.abstract)

    def print_constraints(self, message: str):
        print(message)
        elina_lincons0_array_print(self.lincons_array, None)
        print("-----------------------------------------------------------")

    def to_string (self):
        lincons_array = self.lincons_array
        if self.is_top():
            return "T"
        if self.is_bottom():
            return "⊥"
        result = []
        for j in range(lincons_array.size):
            string = ""
            lincons = lincons_array.p[j]
            for i in range(lincons.linexpr0.contents.size):
                linterm = lincons.linexpr0.contents.p.linterm[i]
                coeff = linterm.coeff
                string += (" + " if elina_coeff_equal_int(coeff, 1) else " - ")
                string += (self.idx_to_varname[linterm.dim])
            if lincons.constyp == ElinaConstyp.ELINA_CONS_SUPEQ:
                string += " >= "
            elif lincons.constyp == ElinaConstyp.ELINA_CONS_SUP:
                string += " > "
            elif lincons.constyp == ElinaConstyp.ELINA_CONS_EQ:
                string += " = "
            string += str(lincons.linexpr0.contents.cst.val.scalar.contents.val.dbl)
            result.append(string)
        return f"OCT({','.join(result)})"

    def dim_to_pp(self, dim, pp):
        self.idx_to_varname[dim] = pp


class OctagonState(State):


    def __init__(self, variables: List[VariableIdentifier]):
        self.variables = list(set(variables))
        self.varname_to_idx, idx_to_varname = self.generate_dict()
        self.elina = ElinaLattice(dim=len(variables), idx_to_varname=idx_to_varname)

    def __repr__(self):
        return self.elina.to_string()

    def _assign(self, left: Expression, right: Expression) -> 'State':
       raise Exception("Assign should not be called in backward analysis.")

    def _assume(self, condition: Expression) -> 'State':
        if not self.belong_here(condition.ids()):
            return self
        return self._meet(condition)

    def enter_if(self) -> 'OctagonState':
        return self

    def exit_if(self) -> 'OctagonState':
        return self

    def enter_loop(self) -> 'OctagonState':
        return self

    def exit_loop(self) -> 'OctagonState':
        return self

    def _output(self, output: Expression) -> 'OctagonState':
        return self

    def raise_error(self) -> 'OctagonState':
        return self.bottom()

    def _substitute(self, left: Expression, right: Expression) -> 'OctagonState':
        if not self.belong_here(left.ids().union(right.ids())):
            return self
        if(isinstance(right, Input)):
            return self
        vi, vars, signs, c = self.check_expressions(left, right)
        self.elina.substitute(vi, vars, signs, c)
        return self

    def bottom(self):
        self.elina.abstract = self.elina.bottom()
        self.elina.equate()
        return self

    def top(self):
        self.elina.abstract = self.elina.top()
        self.elina.equate()
        return self

    def is_bottom(self) -> bool:
        return self.elina.is_bottom()

    def is_top(self) -> bool:
        return self.elina.is_top()

    def _less_equal(self, other: 'OctagonState') -> bool:
        return self.elina.less_equal(other.elina)

    def _join(self, other: 'OctagonState') -> 'OctagonState':
        self.elina.join(other.elina)
        return self

    def _meet(self, other: 'OctagonState'):
        # We have VARS*SIGNS + C <= 0
        var, sign, c = self.check_condition(other)
        # Convert to Elina format -VARS*SIGNS >= C
        sign = list(map(lambda x: -x, sign))
        self.elina.add_linear_constr(var, sign, c)
        return self

    def _widening(self, other: 'OctagonState'):
        self.elina.widening(other.elina)
        return self

    def copy(self):
        copy = OctagonState(self.variables)
        copy.elina = self.elina.copy()
        return copy

    def add_variable(self, variable: VariableIdentifier):
        # add variable to elina
        self.elina.add_dim(variable.name)
        # add to variables list of octagon
        self.variables.add(variable)
        # update dictionary {idx -> varname}
        self.varname_to_idx[variable.name] = len(self.variables) - 1

    def forget_variable(self, variable: VariableIdentifier):
        dim = self.varname_to_idx[variable.name]
        element = self.elina.extract_dim(dim)
        self.elina.project(dim)
        return element

    def remove_variable(self, variable: VariableIdentifier):
        dim = self.varname_to_idx[variable.name]
        self.elina.remove_dim(dim)
        for k,v in self.varname_to_idx.items():
            if v > dim and k != variable.name:
                self.varname_to_idx[dim] -= 1
        del self.varname_to_idx[variable.name]

    def replace_variable(self, variable: Identifier, pp: ProgramPoint):
        pass

    def belong_here(self, vars):
        return all(var in self.variables for var in vars)
    # ==================================================
    #             HEURISTICS
    # ==================================================
    def generate_dict(self):
        """
        :return: dictionary in which every Lyra variable is mapped to an integer index to be passed to Elina
        """
        return {var.name: i for i, var in enumerate(self.variables)}, {i: var.name for i, var in enumerate(self.variables)}

    def check_expressions(self, left: Expression, right: Expression):
        """
            Checks if left and right expressions make a valid substitution.
        :param left:
        :param right:
        :return:vi: variable to substitute

        """
        # print(f"left {left}, right {right}")
        vi, vj, c, = None, None, None
        var_ids, signs, c = self.normalize_arithmetic(right)
        if isinstance(left, VariableIdentifier):
            vi = self.varname_to_idx[left.name]
            if len(var_ids) > 1:
                raise ValueError(f"For now we only support substitution with at most one variable, {right} doesn't work")
            vars = [self.varname_to_idx[id.name] for id in var_ids]
        return vi, vars, signs, c


    def check_condition(self, condition: Expression):
        '''
        So far only checking for expression of the form x + y [comparison operator] c
        :param condition: condition to be checked
        :return:
        '''
        print(f"Checking condition {condition}")
        negation_free_normal = NegationFreeNormalExpression()
        normal_condition = negation_free_normal.visit(condition)
        vars, signs = [], []
        expr = normal_condition.left # x + y - c
        var_ids, signs, c = self.normalize_arithmetic(expr)
        vars = [self.varname_to_idx[id.name] for id in var_ids]
        return vars, signs, c

    def normalize_arithmetic(self, expr: Expression):
        """

        :param expr: Linear expression with coefficients of -1 or 1 and any number of constant terms
        :return: new expression of the form ((+/-v1) + (+/-v2) + (+/-v3) + ... ) + C, where C = sum of all constants in expr
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
        #
        # if len(vars) > 2:
        #     raise ValueError("Expression should have only 2 variables")
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
