ref: str = input()
alt: str = input()
genotype: str = input()
if genotype == ref+ref:
    x: int = 1
elif (genotype == ref+alt) or (genotype == alt+ref):
    x: int = 2
elif genotype == alt+alt:
    x: int = 3
else: # missing genotype, or incorrect annotation, we assume ref/ref
    raise ValueError
