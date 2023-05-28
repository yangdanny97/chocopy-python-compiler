x: int = 0
y: str = "a"
z: int = 0


def t():
    global x
    global y
    x = x + 1
    y = y + y
    assert z == 0


assert x == 0
assert y == "a"
t()
assert x == 1
assert y == "aa"
