# INITIAL [2:(Int, [-inf, inf])]
a: int = int(input())
if a > 10:
    values: List[str] = input().split(",")
else:
    values: List[str] = input().split(";")
print(values[20])