class Rat(object):
    n: int = 0
    d: int = 0

    def __init__(self: Rat):
        pass

    def new(self: Rat, n: int, d: int) -> Rat:
        self.n = n
        self.d = d
        return self

    def mul(self: Rat, other: Rat) -> Rat:
        return Rat().new(self.n * other.n, self.d * other.d)


r1: Rat = None
r2: Rat = None
r3: Rat = None
r1 = Rat().new(4, 5)
r2 = Rat().new(2, 3)
assert r1.n == 4
assert r1.d == 5
assert r2.n == 2
assert r2.d == 3

r3 = r1.mul(r2)
assert r3.n == 8
assert r3.d == 15

r3 = r3.mul(r2).mul(r2)
assert r3.n == 32
assert r3.d == 135
