x: int = 1
y: int = 2
a: bool = True
b: bool = False


def test1(a1: int, a2: int) -> int:
    return a1 + a2


def test2(a1: bool) -> bool:
    return not a1


def test3():
    return None


def test4():
    return


test3()
test4()

assert test1(x, y) == 3
assert test1(x, x) == 2
assert test2(b)
assert not test2(a)
assert test4() is None
assert test3() is None
