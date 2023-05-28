w: [int] = None
x: int = 0

w = []
assert len(w) == 0

w = [1, 2, 3]
assert len(w) == 3
assert w[0] == 1
assert w[1] == 2
assert w[2] == 3

print(w[0])
print(w[1])
print(w[2])

w[1] = 10
assert w[1] == 10

for x in w:
    print(x)

w = w + [5, 1, 0]
assert len(w) == 6
assert w[3] == 5
assert w[4] == 1
assert w[5] == 0
