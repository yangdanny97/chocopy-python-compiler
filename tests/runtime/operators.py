w: int = 1
x: int = 1
y: int = 2
z: object = None
a: str = "123"
b: str = "123"
c: str = "456"
assert w == x
assert y != x
assert b == b
assert a == b
assert b != c
assert y > x
assert y >= x
assert w >= x
assert x < y
assert x <= y
assert w <= x
assert w + x == y
assert y - x == w
assert w * x == x
assert 5 // 2 == y
assert 5 % 2 == x
assert not False
assert not (w != x)
assert -x == -1
assert True and True
assert True or False
assert False or True
assert (False or True) and True
assert True if x != y else False
assert False if x == y else True

assert z is z
assert None is None
assert not (object() is object())
assert z is None
z = object()
assert z is z
