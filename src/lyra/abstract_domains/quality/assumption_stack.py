# from lyra.abstract_domains.quality.assumption_domain import AssumptionState
from lyra.abstract_domains.quality.assumption_graph import AssumptionGraph, AssumptionNode
from lyra.abstract_domains.stack import Stack
from lyra.core.expressions import Expression, Identifier
from lyra.core.statements import ProgramPoint


class AssumptionStack(Stack):

    def __init__(self, typ: AssumptionGraph):
        self._assumption_state = None
        super().__init__(typ, {})

    @property
    def assumption_state(self):
        return self._assumption_state
    @assumption_state.setter
    def assumption_state(self, assumption_state):
        self._assumption_state = assumption_state

    def _assume(self, condition: Expression):
        pass

    def _substitute(self, left: Expression, right: Expression):
        pass

    def _join(self, other: 'AssumptionStack'):
        # print("JOIN")
        # print("SELF", self)
        # print("OTHER", other)
        a = self.copy()
        b = other.copy()
        result = AssumptionStack(AssumptionGraph)
        result.stack = [None] * len(self.stack)
        assert len(self.stack) == len(other.stack)
        LEN = len(self.stack)
        while len(a.stack) > 0 and len(b.stack) > 0:
            # print("first", a)
            # print("second", b)
            idx = min(len(a.stack), len(b.stack)) - 1
            a_top = a.stack.pop(-1)
            b_top = b.stack.pop(-1)
            res, rem = None, None
            if a_top.is_loop or b_top.is_loop: # at least one of the two layers is a loop
                if len(a.stack) == len(b.stack): # loops are in the same scope
                    res, rem = a_top.loop_join(b_top)
                    assert isinstance(res, AssumptionGraph)
                    assert isinstance(rem[0], AssumptionGraph) and isinstance(rem[1], AssumptionGraph)
                else: # different scopes
                    # mark current result layer and all subsequent ones for information loss
                    # lose all information below current layer
                    result.lose_info(idx)
                    self.stack = result.stack
                    # some sanity checks for the result
                    assert len(self.stack) == LEN
                    assert not any(el is None for el in self.stack)
                    # do not continue joining further
                    return self
            else:
                res, rem = a_top._join(b_top)
                assert isinstance(res, AssumptionGraph) and isinstance(rem[0], AssumptionGraph) and isinstance(rem[1],
                                                                                                               AssumptionGraph)

            # print("TOP LAYER", a_top, "---", b_top)
            # print("res", res, "rem", rem)
            assert isinstance(res, AssumptionGraph) and isinstance(rem[0], AssumptionGraph) and isinstance(rem[1], AssumptionGraph)
            result.stack[idx] = res if result.stack[idx] is None else AssumptionGraph(1, result.stack[idx] + res)
            if rem is not None and not rem[0].is_bottom():
                a.stack.append(rem[0])
            if rem is not None and not rem[1].is_bottom():
                b.stack.append(rem[1])

        if len(a.stack) > 0 or len(b.stack) > 0:
            result.stack[0].loss = True

        self.stack = result.stack
        # print("RESULT", self)
        # print()
        assert len(self.stack) == LEN
        assert not any(el is None for el in self.stack)

        return self

    def lose_info(self, idx: int):
        """
        Loses all information below given index.
        :param idx:
        :return:
        """
        # lose all information gathered below the current layer
        loss_layer = AssumptionGraph(1, [])
        loss_layer.loss = True
        for i in range(idx - 1):
            old_layer = self.stack[i]
            self.stack[i] = loss_layer.copy()
            # preserving loop status of the old layer, might be needed later
            if old_layer is not None:
                self.stack[i].is_loop = old_layer.is_loop
        # keep information gathered in the current layer before this point, but mark it for info loss
        if self.stack[idx] is not None:
            self.stack[idx].loss = True
        else:
            self.stack[idx] = loss_layer.copy()

    def _less_equal(self, other: 'AssumptionStack'):
        a = self.copy()
        b = other.copy()
        result = True
        # print("LESS EQUAL")
        # print("SELF", self)
        # print("OTHER", other)
        while len(a.stack) > 0 and len(b.stack) > 0:
            # print("iteration")
            # print(a)
            # print(b)
            a_top = a.stack.pop(-1)
            b_top = b.stack.pop(-1)
            # if a_top.is_loop or b_top.is_loop:
            #     if len(a.stack) == len(b.stack): # loops are in the same scope
            #         res, rem = a_top.loop_less_equal(b_top)
            #     else:
            #         raise Exception("This should not happen.")
            # else:
            res, rem = a_top._less_equal(b_top)
            # print(res, rem)
            result = result and res
            if rem is not None and not rem[0].is_bottom():
                a.stack.append(rem[0])
            if rem is not None and not rem[1].is_bottom():
                b.stack.append(rem[1])
        # print("RESULT", result)
        # print()
        return result

    def raise_error(self):
        pass

    def push(self):

        # add a pointer to the parent assumption state to the
        ag = AssumptionGraph()
        ag.assumption_state = self.assumption_state
        self.stack.append(ag)
        return self

    def copy(self):
        new_stack = AssumptionStack(AssumptionGraph)
        array = []
        for element in self.stack:
            array.append(element.copy())
        new_stack.stack = array
        return new_stack

    def pop(self):
        # print("POPPING", self)
        upper = self.stack.pop(-1)
        lower = None
        if len(self.stack) > 0:
            lower = self.stack.pop(-1)
        # print("UPPER", upper)
        # print("LOWER", lower)
        # print("AFTER", self)
        # combine the two top elements to make one element
        new_top = upper.combine(lower)
        # print("NEW TOP", new_top)
        # push new element to top of stack
        if new_top is not None:
            self.stack.append(new_top)
        # print("NEW STACK", self)
        return self

    def replace_variable(self, variable: Identifier, pp: ProgramPoint):
        for element in self.stack:
            element.replace_variable(variable, pp)

    def top_layer(self, is_loop: bool=None, condition: Expression=None, prepend:AssumptionNode=None):
        stack_top = self.stack[-1]
        if is_loop is not None:
            self.stack[-1].is_loop = is_loop
        if condition is not None:
            self.stack[-1].condition = condition
        if prepend is not None:
            self.stack[-1].add_assumption(prepend)