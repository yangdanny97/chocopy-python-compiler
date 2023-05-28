x: int = 1
y: int = 2
z: object = None
a: bool = True
b: bool = False
c: str = ""
d: str = ""

b = a

assert x != y
x = y
assert x == y
x = 2
y = 2
assert x == y
x = y = 0
assert x == 0
assert y == 0


z = None
assert z is None

assert a == b
b = False
assert a != b

assert c == d
d = c = "123"
assert c == d
d = "456"
assert c != d
d = "123"
assert c == d

z = print("1234")
assert z is None
