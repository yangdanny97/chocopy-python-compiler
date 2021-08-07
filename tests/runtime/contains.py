# Search in a list
def contains(items:[int], x:int) -> bool:
    i:int = 0
    while i < len(items):
        if items[i] == x:
            return True
        i = i + 1
    return False

def contains2(items:[int], x:int) -> bool:
    i:int = 0
    for i in items:
        if i == x:
            return True
    return False

__assert__(contains([4, 8, 15, 16, 23], 15))
__assert__(contains([4, 8, 15, 16, 23], 4))
__assert__(contains([4, 8, 15, 16, 23], 8))
__assert__(contains([4, 8, 15, 16, 23], 16))
__assert__(contains([4, 8, 15, 16, 23], 23))
__assert__(not contains([4, 8, 15, 16, 23], 999))
__assert__(not contains([4], 15))
__assert__(not contains([], 15))

__assert__(contains2([4, 8, 15, 16, 23], 15))
__assert__(contains2([4, 8, 15, 16, 23], 4))
__assert__(contains2([4, 8, 15, 16, 23], 8))
__assert__(contains2([4, 8, 15, 16, 23], 16))
__assert__(contains2([4, 8, 15, 16, 23], 23))
__assert__(not contains2([4, 8, 15, 16, 23], 999))
__assert__(not contains2([4], 15))
__assert__(not contains2([], 15))
