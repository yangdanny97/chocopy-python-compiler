a:int = 0

def test(x:int)->int:
    def test2():
        nonlocal x
        x = 2
    test2()
    return x

def test3()->int:
    x:int = 4
    def test4():
        nonlocal x
        def test5():
            __assert__(x == 4)
        def test6():
            nonlocal x
            x = 3
        test5()
        test(x)
        __assert__(x == 4)
        test6()
        __assert__(x == 3)
    test4()
    return x

def test7():
    x:[int] = None
    def test8():
        x[0] = 0
    x = [1, 2, 3]
    test8()
    __assert__(x[0] == 0)

def test9(x:int):
    def test9helper():
        nonlocal x
        x = 0
    test9helper()

def test10():
    y:int = 1
    def test11(m:int)->int:
        return m + y
    def test12()->int:
        nonlocal y
        def test13(m:int)->int:
            return m + y
        y = test13(y)
        __assert__(y == 2)
        return test13(y)
    __assert__(test11(y) == 2)
    __assert__(test12() == 4)
    __assert__(y == 2)

class Nonlocals:
    def testMethod3(self:"Nonlocals"):
        pass
    def testMethod(self:"Nonlocals", x:int):
        y:int = 2
        def testMethod2():
            nonlocal x
            nonlocal self
            nonlocal y
            self.testMethod3()
            x = 3
            self = None
            y = 3
        testMethod2()
        __assert__(self is None)
        __assert__(y == 3)

b:Nonlocals = None

# nonlocals can be mutated 
__assert__(test(1) == 2)

__assert__(test3() == 3)


# nonlocals passed into functions cannot be mutated
a = 0
test9(a)
__assert__(a == 0)

# array idx's can be mutated w/o nonlocal
test7()

test10()

a = 0
b = Nonlocals()
b.testMethod(a)
__assert__(a == 0)
b.testMethod(1)
