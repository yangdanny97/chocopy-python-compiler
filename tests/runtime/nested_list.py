a: [[int]] = None
b: [int] = None
c: int = 0
d: int = 0

# TODO - check if these are legal
# a = []
# assert len(a) == 0
# a = [[]]
# assert len(a) == 1
# assert len(a[0]) == 0

a = [[1]]
assert len(a) == 1
assert len(a[0]) == 1

a = [[1], [2, 2, 2], [3, 3], []]
assert len(a) == 4
assert len(a[0]) == 1
assert len(a[1]) == 3
assert len(a[2]) == 2
assert len(a[3]) == 0

assert a[0][0] == 1
assert a[1][0] == 2
assert a[1][1] == 2
assert a[1][2] == 2

a[0][0] = 5
assert a[0][0] == 5

a[0] = [2, 2]
assert len(a[0]) == 2

a[0] = a[0] + [3]
assert len(a[0]) == 3


a = [[1], [1, 1, 1], [1, 1], []]
c = 0
for b in a:
    c = c + len(b)
assert c == 6

a = [[1], [2, 3, 4], [5, 0], []]
c = 0
for b in a:
    for d in b:
        c = c + d
assert c == 15
