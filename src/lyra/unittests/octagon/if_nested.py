# x: int = int(input())
# a: float = x
# if a < 10:
#     raise ValueError
# if a > 100:
#     raise ValueError
x: int = int(input())
a: float = x + 1
if a < 10 or a > 100:
    raise ValueError
