# Super is not defined
class A(B):
    x:int = 1

z:int = 2

# Super is not a class
class B(z):
    x:int = 1

# Cannot extend special classes
class C(int):
    x:int = 1

A()
