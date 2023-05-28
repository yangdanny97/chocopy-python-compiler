def f1():
    x: int = 1


def f2() -> int:
    return 1


def f3() -> object:
    return None


def f4(x: int, y: object) -> int:
    return x + 1


def f5():
    return None


def f6() -> int:
    return f4(5, None)


def f7() -> int:
    x: int = 0
    y: int = 0
    x = f4(10, None)
    y = f6()
    return x - y


def f8(x: int) -> int:
    return x


x: int = 0
y: object = None

f1()
assert f2() == 1
assert f3() is None
assert f4(1, None) == 2
assert f4(f2(), f3()) == 2
assert f5() is None
x = f4(f2(), f3())
y = f3()
assert f4(x, y) == 3
assert f6() == 6
assert f7() == 5
assert f8(0) == 0
assert f8(1) == 1
assert f8(f7()) == 5

print(1)
print(True)
