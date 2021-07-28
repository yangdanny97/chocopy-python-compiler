w:[object] = None
x:[int] = None
x2:[int] = None
y:[str] = None
y2:[str] = None
z:object = None
a:[[object]] = None

w = []
x = []
x2 = []
y = []
y2 = []
z = []

__assert__(len(x) == 0)
__assert__(len([]) == 0)
__assert__(len([1, 2, 3]) == 3)

x = [1, 2, 3]
__assert__(len(x) == 3)
__assert__(x[0] == 1)
__assert__(x[1] == 2)
__assert__(x[2] == 3)

x = [1, 2, 3]
x = [0] + x
__assert__(len(x) == 4)
__assert__(x[0] == 0)
__assert__(x[1] == 1)
__assert__(x[2] == 2)
__assert__(x[3] == 3)

x = [1, 2, 3]
x =  x + [4]
__assert__(len(x) == 4)
__assert__(x[0] == 1)
__assert__(x[1] == 2)
__assert__(x[2] == 3)
__assert__(x[3] == 4)

y = ["1", "2", "3"]
__assert__(len(y) == 3)
__assert__(y[0] == "1")
__assert__(y[1] == "2")
__assert__(y[2] == "3")

z = [None]
__assert__(len([None]) == 1)
__assert__([None][0] is None)

z = [[]]
__assert__(len([[]]) == 1)
__assert__(len([[]][0]) == 0)

a = [[object()]]
__assert__(len(a) == 1)
__assert__(len(a[0]) == 1)

y = ["1", "2", "3"]
y = y + y
__assert__(len(y) == 6)
__assert__(y[0] == "1")
__assert__(y[1] == "2")
__assert__(y[2] == "3")
__assert__(y[3] == "1")
__assert__(y[4] == "2")
__assert__(y[5] == "3")

x = [1, 2, 3]
x = x + x
__assert__(len(x) == 6)
__assert__(x[0] == 1)
__assert__(x[1] == 2)
__assert__(x[2] == 3)
__assert__(x[3] == 1)
__assert__(x[4] == 2)
__assert__(x[5] == 3)

w = [None]
__assert__(len(w) == 1)
__assert__(w[0] is None)

w = [object()]
__assert__(len(w) == 1)
__assert__(not (w[0] is None))

w = [object()]
w[0] = None
__assert__(w[0] is None)
w[0] = object()
__assert__(not (w[0] is None))

x = [1, 2, 3]
x[0] = 999
__assert__(len(x) == 3)
__assert__(x[0] == 999)
__assert__(x[1] == 2)
__assert__(x[2] == 3)

x2 = x
x[1] = 999
__assert__(x[1] == 999)
__assert__(x2[1] == 999)

x = [0, 1]
x2[1] = 30
__assert__(x[1] != 30)
__assert__(x2[1] == 30)

x = x2
x2 = x

y = ["1", "2", "3"]
y[2] = "a"
__assert__(len(y) == 3)
__assert__(y[0] == "1")
__assert__(y[1] == "2")
__assert__(y[2] == "a")

y2 = y
y2[1] = "aa"
__assert__(y2[1] == "aa")
__assert__(y2[1] == "aa")

a = [None, [], [object(), None]]
__assert__(a[0] is None)
__assert__(len(a[1]) == 0)
__assert__(len(a[2]) == 2)
__assert__(not (a[2][0] is None))
__assert__(a[2][1] is None)

w = []
__assert__(len(w) == 0)
__assert__(len(w + w) == 0)

x = []
__assert__(len(x) == 0)
# __assert__(len(x + x) == 0)

# x = [1]
# y = ["1"]
# w = x + y

# y = []
# y = y + [""]
# __assert__(len(y) == 1)
# __assert__(len(y[0]) == 0)

# TODO empty array type wrongly defaults to Object[]
# TODO concatenating arrays of diff types into [object]



