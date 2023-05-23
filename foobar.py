x:[int] = None
y:int = 0
x = [1, 2, 3]
for y in x:
    print(y)
x[0] = 2
x[1] = 2
x[2] = 9
for y in x:
    print(y)