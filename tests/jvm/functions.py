def f1():
    x:int = 1

def f2()->int:
    return 1

def f3()->object:
    return None

def f4(x:int, y:object)->int:
    return x + 1

def f5():
    return None

def f6()->int:
    return f4(5, None)

def f7()->int:
    x:int = 0
    y:int = 0
    x = f4(10, None)
    y = f6()
    return x - y

def f8(x:int)->int:
    return x

x:int = 0
y:object = None

f1()
__assert__(f2() == 1)
__assert__(f3() is None)
__assert__(f4(1, None) == 2)
__assert__(f4(f2(), f3()) == 2)
__assert__(f5() is None)
x = f4(f2(), f3())
y = f3()
__assert__(f4(x, y) == 3)
__assert__(f6() == 6)
__assert__(f7() == 5)
__assert__(f8(0) == 0)
__assert__(f8(1) == 1)
__assert__(f8(f7()) == 5)