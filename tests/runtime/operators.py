w:int = 1
x:int = 1
y:int = 2
z:object = None
a:str = "123"
b:str = "123"
c:str = "456"
__assert__(w == x)
__assert__(y != x)
__assert__(b == b)
__assert__(a == b)
__assert__(b != c)
__assert__(y > x)
__assert__(y >= x)
__assert__(w >= x)
__assert__(x < y)
__assert__(x <= y)
__assert__(w <= x)
__assert__(w + x == y)
__assert__(y - x == w)
__assert__(w * x == x)
__assert__(5 // 2 == y)
__assert__(5 % 2 == x)
__assert__(z is z)
__assert__(not False)
__assert__(not (w != x))
__assert__(-x == -1)
__assert__(True and True)
__assert__(True or False)
__assert__(False or True)
__assert__((False or True) and True)
__assert__(True if x != y else False)
__assert__(False if x == y else True)

