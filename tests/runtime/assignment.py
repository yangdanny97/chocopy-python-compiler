x:int = 1
y:int = 2
z:object = None
a:bool = True
b:bool = False
c:str = ""
d:str = ""

b = a

__assert__(x != y)
x = y
__assert__(x == y)
x = 2
y = 2
__assert__(x == y)
x = y = 0
__assert__(x == 0)
__assert__(y == 0)


z = None
__assert__(z is None)

__assert__(a == b)
b = False
__assert__(a != b)

__assert__(c == d)
d = c = "123"
__assert__(c == d)
d = "456"
__assert__(c != d)
d = "123"
__assert__(c == d)

z = print("1234")
__assert__(z is None)