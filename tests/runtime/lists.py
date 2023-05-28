w: [object] = None
x: [int] = None
x2: [int] = None
y: [str] = None
y2: [str] = None
z: object = None
a: [[object]] = None
b: [[int]] = None


def setIdx(lst: [int], idx: int, value: int):
    lst[idx] = value


def setNestedIdx(lst: [[int]], idx1: int, idx2: int, value: int):
    lst[idx1][idx2] = value


def getNestedIdx(lst: [[int]], idx: int) -> [int]:
    return lst[idx]


w = []
x = []
x2 = []
y = []
y2 = []
z = []
a = []
b = []

assert b is b
assert not (a is b)
assert not (a is None)

assert len(x) == 0
assert len([]) == 0
assert len([1, 2, 3]) == 3

x = [1, 2, 3]
assert len(x) == 3
assert x[0] == 1
assert x[1] == 2
assert x[2] == 3

x = [1, 2, 3]
x = [0] + x
assert len(x) == 4
assert x[0] == 0
assert x[1] == 1
assert x[2] == 2
assert x[3] == 3

x = [1, 2, 3]
x = x + [4]
assert len(x) == 4
assert x[0] == 1
assert x[1] == 2
assert x[2] == 3
assert x[3] == 4

y = ["1", "2", "3"]
assert len(y) == 3
assert y[0] == "1"
assert y[1] == "2"
assert y[2] == "3"

z = [None]
assert len([None]) == 1
assert [None][0] is None

z = [[]]
assert len([[]]) == 1
assert len([[]][0]) == 0

a = [[object()]]
assert len(a) == 1
assert len(a[0]) == 1

y = ["1", "2", "3"]
y = y + y
assert len(y) == 6
assert y[0] == "1"
assert y[1] == "2"
assert y[2] == "3"
assert y[3] == "1"
assert y[4] == "2"
assert y[5] == "3"

x = [1, 2, 3]
x = x + x
assert len(x) == 6
assert x[0] == 1
assert x[1] == 2
assert x[2] == 3
assert x[3] == 1
assert x[4] == 2
assert x[5] == 3

w = [None]
assert len(w) == 1
assert w[0] is None

w = [object()]
assert len(w) == 1
assert not (w[0] is None)

w = [object()]
w[0] = None
assert w[0] is None
w[0] = object()
assert not (w[0] is None)

x = [1, 2, 3]
x[0] = 999
assert len(x) == 3
assert x[0] == 999
assert x[1] == 2
assert x[2] == 3

x2 = x
x[1] = 999
assert x[1] == 999
assert x2[1] == 999

x = [0, 1]
x2[1] = 30
assert x[1] != 30
assert x2[1] == 30

x = x2
x2 = x

y = ["1", "2", "3"]
y[2] = "a"
assert len(y) == 3
assert y[0] == "1"
assert y[1] == "2"
assert y[2] == "a"

y2 = y
y2[1] = "aa"
assert y2[1] == "aa"
assert y2[1] == "aa"

a = [None, [], [object(), None]]
assert a[0] is None
assert len(a[1]) == 0
assert len(a[2]) == 2
assert not (a[2][0] is None)
assert a[2][1] is None

w = []
assert len(w) == 0
assert len(w + w) == 0

x = []
assert len(x) == 0
assert len(x + x) == 0

y = []
y = y + [""]
assert len(y) == 1
assert len(y[0]) == 0

x = [1, 2, 3]
setIdx(x, 1, 0)
assert x[1] == 0

b = [[1, 1], [2], [3]]
setNestedIdx(b, 0, 0, 1)
assert b[0][0] == 1

assert b[1][0] == 2
x = getNestedIdx(b, 1)
assert x[0] == 2
x[0] = 1
assert b[1][0] == 1

x = [1, 2, 3]
x2 = x
x[0] = 0
assert x2[0] == 0

x = [1]
y = ["1"]
w = x + y
