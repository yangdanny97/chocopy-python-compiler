x:str = "123"
y:str = "123"

__assert__(len(x) == 3)
__assert__(x == y)
__assert__(x == "123")
__assert__(y == x)
__assert__(x != "456")
__assert__(x[0] == "1")
__assert__(x[1] == "2")
__assert__(x[2] == "3")

x = "123"
x = x + ""
__assert__(x == "123")
__assert__(len(x) == 3)
__assert__(x[0] == "1")
__assert__(x[1] == "2")
__assert__(x[2] == "3")

x = "123"
x = "" + x
__assert__(x == "123")
__assert__(len(x) == 3)
__assert__(x[0] == "1")
__assert__(x[1] == "2")
__assert__(x[2] == "3")

x = "123"
x = x + "4"
__assert__(x == "1234")
__assert__(len(x) == 4)
__assert__(x[0] == "1")
__assert__(x[1] == "2")
__assert__(x[2] == "3")
__assert__(x[3] == "4")

x = "123"
x = "0" + x
__assert__(x == "0123")
__assert__(len(x) == 4)

x = "123"
x = x + y
__assert__(x == "123123")
__assert__(y == "123")
__assert__(len(x) == 6)
__assert__(len(y) == 3)

x = "123"
x = x + x
__assert__(x == "123123")
__assert__(len(x) == 6)

x = "123"
y = x
x = "0"
__assert__(y == "123")
__assert__(len(x) == 1)
__assert__(len(y) == 3)

# TODO indexing


