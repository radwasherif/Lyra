from lyra.abstract_domains.quality.assumption_graph import AssumptionGraph, AssumptionNode
from lyra.abstract_domains.stack import Stack
from lyra.core.expressions import Expression, Identifier
from lyra.core.statements import ProgramPoint


class AssumptionStack(Stack):

    def __init__(self, typ: AssumptionGraph):
        super().__init__(typ, {})

    def _assume(self, condition: Expression):
        pass

    def _substitute(self, left: Expression, right: Expression):
        pass

    def _join(self, other: 'AssumptionStack'):
        print("SELF", self)
        print("OTHER", other)
        a = self.copy()
        b = other.copy()
        result = AssumptionStack(AssumptionGraph)
        result.stack = [None] * len(self.stack)
        assert len(self.stack) == len(other.stack)
        LEN = len(self.stack)
        while len(a.stack) > 0 and len(b.stack) > 0:
            # print(stack1, "---", stack2)
            idx = min(len(a.stack), len(b.stack)) - 1
            a_top = a.stack.pop(-1)
            b_top = b.stack.pop(-1)
            res, rem = None, None
            if a_top.is_loop or b_top.is_loop: # at least one of the two layers is a loop
                if len(a.stack) == len(b.stack): # loops are in the same scope
                    res, rem = a_top.loop_join(b_top)
                else: # different scopes
                    # lose all information gathered below the current layer
                    loss_layer = AssumptionGraph(1, [])
                    loss_layer.loss = True
                    for i in range(idx - 1):
                        old_layer = result.stack[i]
                        result.stack[i] = loss_layer.copy()
                        # preserving loop status of the old layer, might be needed later
                        if old_layer is not None:
                            result.stack[i].is_loop = old_layer.is_loop
                    # keep information gathered in the current layer before this point, but mark it for info loss
                    if result.stack[idx] is not None:
                        result.stack[idx].loss = True
                    else:
                        result.stack[idx] = loss_layer.copy()
            else:
                res, rem = a_top.join(b_top)
                print(a_top, b_top)
                print("res", res)
                result.stack[idx] = res if result.stack[idx] is None else AssumptionGraph(1, result.stack[idx] + res)
                if rem is not None and len(rem[0]) > 0:
                    a.stack.append(rem[0][0])
                if rem is not None and len(rem[1]) > 0:
                    b.stack.append(rem[1][0])
        self.stack = result.stack
        assert len(self.stack) == LEN
        print("RESULT", self)
        print()
        return self

    def _less_equal(self, other: 'AssumptionStack'):
        a = self.copy()
        b = other.copy()
        result = True
        while len(a.stack) > 0 and len(b.stack) > 0:
            # print(stack1, "---", stack2)
            res, rem = a.stack.pop(-1).less_equal(b.stack.pop(-1))
            # print(res)
            result = result and res
            if rem is not None and len(rem[0]) > 0:
                a.stack.append(rem[0][0])
            if rem is not None and len(rem[1]) > 0:
                b.stack.append(rem[1][0])
        return result

    def raise_error(self):
        pass

    def push(self):
        self.stack.append(AssumptionGraph())
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