x: int = int(input())
y: int = int(input())
if 3 > x:  # x decision
    # inside nested if only b is modified!
    if 2 > y:  # y decision
        b:int = 10
    else:
        b:int = 20
    a:int = 10
else:
    # inside nested if only b is modified!
    if 2 > y:  # y decision
        b:int = 10
    else:
        b:int = 20
    a:int = 20
    if a > 0:
        pass
    else:
        raise ValueError

# RESULT: 10≤a≤20, 10≤b≤20, b+a≤40, b-a≤10, -b+a≤10, -b-a≤-20
print(a)