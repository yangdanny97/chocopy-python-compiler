# Search in a list
def contains(items: [int], x: int) -> bool:
    i: int = 0
    while i < len(items):
        if items[i] == x:
            return True
        i = i + 1
    return False


def contains2(items: [int], x: int) -> bool:
    i: int = 0
    for i in items:
        if i == x:
            return True
    return False


assert contains([4, 8, 15, 16, 23], 15)
assert contains([4, 8, 15, 16, 23], 4)
assert contains([4, 8, 15, 16, 23], 8)
assert contains([4, 8, 15, 16, 23], 16)
assert contains([4, 8, 15, 16, 23], 23)
assert not contains([4, 8, 15, 16, 23], 999)
assert not contains([4], 15)
assert not contains([], 15)

assert contains2([4, 8, 15, 16, 23], 15)
assert contains2([4, 8, 15, 16, 23], 4)
assert contains2([4, 8, 15, 16, 23], 8)
assert contains2([4, 8, 15, 16, 23], 16)
assert contains2([4, 8, 15, 16, 23], 23)
assert not contains2([4, 8, 15, 16, 23], 999)
assert not contains2([4], 15)
assert not contains2([], 15)
