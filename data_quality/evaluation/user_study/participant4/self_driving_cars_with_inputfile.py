import sys

sys.stdin = open('self_driving_cars.in', 'r')

cases: int = int(input())
for cc in range(cases):
    distance: float = float(input())
    n: int = int(input())
    max_time: float = 0
    for i in range(n):
        position: int = int(input())
        if distance < position:
            raise ValueError("The distance cannot be smaller than the starting position.")
        speed: float = float(input())
        if speed < 0:
            raise ValueError("The speed cannot be negative.")
        val: float = (distance - position) / speed
        if val > max_time:
            max_time: int = val
    print('Trip #')
    print(cc+1)
    print("with speed")
    print(distance / max_time)
    print("")