class A:
    y: int = 1

    def __init__(self: A):
        pass

    def t(self: A):
        global x
        x = 1


class B(A):
    z: int = 0

    def __init__(self: B):
        self.z = 5
        self.y = 5

    def t(self: B):
        global x
        x = 2

    def setZ(self: B, z: int):
        self.z = z


x: int = 0
c1: A = None
c2: B = None
c3: A = None

# constructors, getters, setters
c1 = A()
assert c1.y == 1
c2 = B()
assert c2.y == 5
assert c2.z == 5
c3 = B()
assert c3.y == 5

c2.y = 0
assert c2.y == 0

# methods, dynamic dispatch

c2.setZ(2)
assert c2.z == 2

x = 0
c1.t()
assert x == 1

x = 0
c2.t()
assert x == 2

x = 0
c3.t()
assert x == 2
