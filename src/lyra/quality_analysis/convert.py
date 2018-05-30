x: str = input()
if (x == 'pounds' or x == 'lb') or x == 'lbs':
    y: float = 453.592 * 1e-3
elif x == 'ounces' or (x == 'oz' or x == 'oz.'):
    y: float = 28.35 * 1e-3
elif x == 'grams' or (x == 'gms' or x == 'g'):
    y: float = 1e-3
elif (x == 'kilograms' or x == 'kilo') or x == 'kg':
    y: float = 1
else:
    raise ValueError
