x: [int] = None
y: str = "123"
z: str = ""
char: str = ""
a: bool = True
b: int = 0
c: int = 100
d: [bool] = None
e: object = None
f: [object] = None

x = []

for char in y:
    pass

for char in y:
    z = char + z
assert z == "321"
assert char == "3"

x = [1, 2, 3]
for b in x:
    x[0] = b
assert x[0] == 3

x = [1, 2, 3]
for b in x:
    c = c * 2
assert c == 800
assert b == 3

c = 100
x = []
for b in x:
    c = c * 2
assert c == 100

a = True
d = [True, True, True, False]
for a in d:
    pass
assert not a

a = True
d = [True, True, True]
for a in d:
    assert a
    print(a)

e = None
f = [None, object(), None, object()]
for e in f:
    pass
assert not (e is None)
