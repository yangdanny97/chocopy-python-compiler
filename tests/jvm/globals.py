x:int = 0
y:str = "a"

def t():
    global x
    global y
    x = x + 1
    y = y + y


__assert__(x == 0)
__assert__(y == "a")
t()
__assert__(x == 1)
__assert__(y == "aa")