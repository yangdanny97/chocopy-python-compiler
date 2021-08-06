x:[int] = None
y:str = "123"
z:str = ""
char:str = ""
a:bool = True
b:int = 0
c:int = 100
d:[bool] = None
e:[[int]] = None

x = []

b = 0
if b == 0:
    b = 1
__assert__(b == 1)

b = 0
if b != 0:
    b = 2
__assert__(b == 0)

b = 0
if b != 0:
    b = 0
else:
    b = 1
__assert__(b == 1)

b = 0
if b == 0:
    b = 1
else:
    b = 0
__assert__(b == 1)

b = 0
if b > 0:
    b = 0
elif b < 0:
    b = 0
else:
    b = 1
__assert__(b == 1)

b = 0
if b == 0:
    pass
elif b < 0:
    b = 1
else:
    b = 1
__assert__(b == 0)

b = 5
if b == 0:
    b = 1
elif b < 0:
    b = 2
else:
    pass
__assert__(b == 5)

b = -1
if b > 0:
    b = 0
elif b < 0:
    b = 1
else:
    b = 0
__assert__(b == 1)

b = -1
while b > 0:
    b = b - 1
__assert__(b == -1)

b = 5
while b > 0:
    b = b - 1
__assert__(b == 0)

for char in y:
    z = char + z
__assert__(z == "321")
__assert__(char == "3")

x = [1, 2, 3]
for b in x:
    x[0] = b
__assert__(x[0] == 3)

x = [1, 2, 3]
for b in x:
    c = c * 2
__assert__(c == 800)
__assert__(b == 3)

c = 100
x = []
for b in x:
    c = c * 2
__assert__(c == 100)

a = True
d = [True, True, True, False]
for a in d:
    pass
__assert__(not a)

# x = None
# e = [[1],[1,1,1],[1,1],[]]
# b = 0
# for x in e:
#     b = b + len(x)
# __assert__(len(x) == 0)
# __assert__(b == 6)