a:[[int]] = None
b:[int] = None
c:int = 0
d:int = 0

# TODO - check if these are legal
# a = []
# __assert__(len(a) == 0)
# a = [[]]
# __assert__(len(a) == 1)
# __assert__(len(a[0]) == 0)

a = [[1]]
__assert__(len(a) == 1)
__assert__(len(a[0]) == 1)

a = [[1],[2, 2, 2],[3,3],[]]
__assert__(len(a) == 4)
__assert__(len(a[0]) == 1)
__assert__(len(a[1]) == 3)
__assert__(len(a[2]) == 2)
__assert__(len(a[3]) == 0)

__assert__(a[0][0] == 1)
__assert__(a[1][0] == 2)
__assert__(a[1][1] == 2)
__assert__(a[1][2] == 2)

a[0][0] = 5
__assert__(a[0][0] == 5)

a[0] = [2, 2]
__assert__(len(a[0]) == 2)

a[0] = a[0] + [3]
__assert__(len(a[0]) == 3)


a = [[1],[1,1,1],[1,1],[]]
c = 0
for b in a:
    c = c + len(b)
__assert__(c == 6)

a = [[1],[2,3,4],[5,0],[]]
c = 0
for b in a:
    for d in b:
        c = c + d
__assert__(c == 15)