x:int = 0
y:int = 0
z:bool = False

x = z = 1    # Only one error here (assignment to `x = 1` should succeed)
x = y = None
x = y = []
x = a = None
x = a = []
x = y = True

