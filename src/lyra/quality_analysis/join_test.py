from copy import deepcopy


class Node:
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return str(self.val)


class Graph:
    def __init__(self, mult, l):
        self.mult = mult
        self.list = l

    def __repr__(self):
        string = str(self.mult) + " x "
        if self.list is None:
            string += "None"
        else:
            string += str(self.list)
        return string

    def empty(self):
        return self.mult == 0 or len(self.list) == 0

    def all_nodes(self):
        return all([isinstance(n, Node) for n in self.list])
class Stack:
    def __init__(self):
        self.stack = []
    def __repr__(self):
        return "| ".join([str(element) for element in self.stack])

stack1 = Stack()
stack2 = Stack()
stack1.stack = [Graph(1, [Node("x"), Node("y")]), Graph(1, [Node("c1")])]
stack2.stack = [Graph(1, [Node("x"), Node("y")]), Graph(1, [Node("c2"), Node("c3")])]


def stack_join(stack1: 'Stack', stack2: 'Stack'):
    assert len(stack1.stack) == len(stack2.stack)
    result = Stack()
    result.stack = [None]*len(stack1.stack)
    while len(stack1.stack) > 0 and len(stack2.stack) > 0:
        print(stack1, "---", stack2)
        idx = min(len(stack1.stack), len(stack2.stack)) - 1
        res, rem = join(stack1.stack.pop(-1), stack2.stack.pop(-1))
        print(res)
        result.stack[idx] = res if result.stack[idx] is None else Graph(1, result.stack[idx] + res)
        if len(rem[0]) > 0:
            stack1.stack.append(rem[0][0])
        if len(rem[1]) > 0:
            stack2.stack.append(rem[1][0])
        print(result)
    return result

g1 = Graph(3, [Node("x"), Graph(2, [Node("m")]), Node("z")])
g2 = Graph(1, [Node("a"), Graph(2, [Node("b"), Node("c")])])

g3 = Graph(3, [Graph(5, [Node("a"), Node("b")])])
g4 = Graph(1, [Graph(3, [Node("x"), Node("y")]), Node("z")])


global_result = []
def join(a_in, b_in):
    a = deepcopy(a_in)
    b = deepcopy(b_in)
    if isinstance(a, Node) and isinstance(b, Node):
        # global_result.append(f"{a.val} * {b.val}")
        return [Node(f"{a.val} * {b.val}")], ([], [])
    if not isinstance(a, Graph) or not isinstance(b, Graph):
        anew, bnew = a, b
        if isinstance(a, Node):
            anew = Graph(1, [a])
        if isinstance(a, list):
            anew = Graph(1, a)
        if isinstance(b, Node):
            bnew = Graph(1, [b])
        if isinstance(b, list):
            bnew = Graph(1, b)
        return join(anew, bnew)

    result = []
    remainder = ([], [])
    if a.empty():
        if not b.empty():
            return result, ([], [b])
        return result, remainder
    if b.empty():
        if not a.empty():
            return result, ([a], [])
        return result, remainder

    if a.all_nodes() and b.all_nodes() and len(a.list) == len(b.list):
        return easy_join(a, b)

    if a.mult == 1 and b.mult == 1:
        if b.list is None:
            raise ValueError
        while len(a.list) > 0 and len(b.list) > 0:
            a1 = a.list.pop(0)
            b1 = b.list.pop(0)
            res, rem = join(a1, b1)
            # print(f"ONE {a1} + {b1} -> RES: {res}, REM: {rem}")
            result = result + res
            if len(rem[0]) > 0:
                a.list = rem[0] + a.list
            if len(rem[1]) > 0:
                b.list = rem[1] + b.list
        remainder0 = []
        remainder1 = []
        if len(a.list) > 0:
            remainder0 = a.list
        if len(b.list) > 0:
            remainder1 = b.list
        # print((remainder0, remainder1))
        return result, (remainder0, remainder1)
    else:
        # print("JOIN n m 1 1")
        if a.mult == 1:
            left = Graph(1, [])
        else:
            left = Graph(a.mult - 1, deepcopy(a.list))
        if b.mult == 1:
            right = Graph(1, [])
        else:
            right = Graph(b.mult - 1, deepcopy(b.list))

        one_a = Graph(1, deepcopy(a.list))
        one_b = Graph(1, deepcopy(b.list))
        res, rem = join(one_a, one_b)
        # print(f"MULT {one_a}, {one_b} -> RES: {res}, REM: {rem}")
        # print(f"RES -> {res}, REM -> {rem}")
        result = result + res
        # print(f"left {left}, right {right}")
        if len(rem[0]) > 0:
            left = Graph(1, rem[0] + [left])
        if len(rem[1]) > 0:
            # print(f"REM[1]: {rem[1]}, RIGHT: {right}")
            right = Graph(1, rem[1] + [right])
            # print(f"right: {right}, after adding rem {rem[1]}")
        # print("JOIN left right", left, right)
        res, rem = join(deepcopy(left), deepcopy(right))
        # print(f"MULT2 {left}, {right} -> RES: {res}, REM: {rem}")
        result = result + res
        rem0 = rem[0] + remainder[0]
        rem1 = rem[1] + remainder[1]
        return result, (rem0, rem1)


def easy_join(a, b):
    res_mult = min(a.mult, b.mult)
    res_list = []
    for a1, b1 in zip(a.list, b.list):
        res_list.append(join(a1, b1)[0])
    remainder = ([], [])
    if res_mult < a.mult:
        remainder = ([Graph(a.mult - res_mult, [Graph(1, deepcopy(a.list))])], [])
    elif res_mult < b.mult:
        remainder = ([], [Graph(b.mult - res_mult, [Graph(1, deepcopy(b.list))])])
    result = Graph(res_mult, res_list)
    return [result], remainder



# g = join(g2, g1)
# g = join(g3, g4)
# print("Result")
# print(g[0])
# print("Remainder:\n", g[1])
#
# result = stack_join(stack1, stack2)
# print(result)

class Mult:
    def __init__(self):
        self.val = "3"
    def __add__(self, other):
        assert isinstance(other, int)
        self.val = str(int(self.val) + other)
        return self
m = Mult()
m = m + 1
# print(m.val)


class TestPointer:
    def __init__(self):
        self.dct = {"idx": Mult()}
        self.attrib = self.dct["idx"]

tp = TestPointer()
tp.dct["idx"] = "Something else"

print(tp.attrib)