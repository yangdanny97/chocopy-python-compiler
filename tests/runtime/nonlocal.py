a: int = 0


def test(x: int) -> int:
    def test2():
        nonlocal x
        x = 2
    test2()
    return x


def test3() -> int:
    x: int = 4

    def test4():
        nonlocal x

        def test5():
            assert x == 4

        def test6():
            nonlocal x
            x = 3
        test5()
        test(x)
        assert x == 4
        test6()
        assert x == 3
    test4()
    return x


def test7():
    x: [int] = None

    def test8():
        x[0] = 0
    x = [1, 2, 3]
    test8()
    assert x[0] == 0


def test9(x: int):
    def test9helper():
        nonlocal x
        x = 0
    test9helper()


def test10():
    y: int = 1

    def test11(m: int) -> int:
        return m + y

    def test12() -> int:
        nonlocal y

        def test13(m: int) -> int:
            return m + y
        y = test13(y)
        assert y == 2
        return test13(y)
    assert test11(y) == 2
    assert test12() == 4
    assert y == 2


class Nonlocals:
    def testMethod3(self: "Nonlocals"):
        pass

    def testMethod(self: "Nonlocals", x: int):
        y: int = 2

        def testMethod2():
            nonlocal x
            nonlocal y
            self.testMethod3()
            x = 3
            y = 3
        testMethod2()
        assert y == 3

    def testMethod4(self: "Nonlocals"):
        test13(self)
        assert not (self is None)


def test13(x: "Nonlocals"):
    def test14():
        nonlocal x
        x = None
    test14()


b: Nonlocals = None

# nonlocals can be mutated
assert test(1) == 2

assert test3() == 3


# nonlocals passed into functions cannot be mutated
a = 0
test9(a)
assert a == 0

# array idx's can be mutated w/o nonlocal
test7()

test10()

a = 0
b = Nonlocals()
b.testMethod(a)
b.testMethod(0)
assert a == 0
b.testMethod(1)
b.testMethod4()
