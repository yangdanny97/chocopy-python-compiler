x: int = 1
y: int = 2
a: bool = True
b: bool = False

print(x)
print(y)
print(a)
print(b)

assert x + y == 3
assert x < y
assert y > x
assert x + x == 2
assert y * y == 4
assert 5 // 2 == y
assert 5 % 2 == x
assert x == x
assert x != y
assert not b
assert a
assert True
assert not False
assert a == a
assert a != b
assert a and a
assert a or b
assert not (b or b)
assert not (b and b)

x = y
assert x == y
assert x == 2

x = y = 3
assert x == y
assert x == 3
