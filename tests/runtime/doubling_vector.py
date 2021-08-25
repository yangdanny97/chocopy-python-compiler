# A resizable list of integers
class Vector(object):
    # Attributes
    items: [int] = None
    size: int = 0

    # Constructor
    def __init__(self:"Vector"):
        self.items = [0]

    # Returns current capacity
    def capacity(self:"Vector") -> int:
        return len(self.items)

    # Increases capacity of vector by one element
    def increase_capacity(self:"Vector") -> int:
        self.items = self.items + [0]
        return self.capacity()

    # Appends one item to end of vector
    def append(self:"Vector", item: int):
        if self.size == self.capacity():
            self.increase_capacity()

        self.items[self.size] = item
        self.size = self.size + 1

# A faster (but more memory-consuming) implementation of vector
class DoublingVector(Vector):
    doubling_limit:int = 16

    # Overriding to do fewer resizes
    def increase_capacity(self:"DoublingVector") -> int:
        if (self.capacity() <= self.doubling_limit // 2):
            self.items = self.items + self.items
        else:
            # If doubling limit has been reached, fall back to
            # standard capacity increases
            self.items = self.items + [0]
        return self.capacity()

def vrange(i:int, j:int) -> Vector:
    v:Vector = None
    v = DoublingVector()
    
    while i < j:
        v.append(i)
        i = i + 1

    return v
      
vec:Vector = None
num:int = 0

# Create a vector and populate it with The Numbers
vec = DoublingVector()
for num in [4, 8, 15, 16, 23, 42]:
    vec.append(num)

__assert__(vec.capacity() == 8)
__assert__(vec.size == 6)
__assert__(vec.items[0] == 4)
__assert__(vec.items[1] == 8)
__assert__(vec.items[2] == 15)
__assert__(vec.items[3] == 16)
__assert__(vec.items[4] == 23)
__assert__(vec.items[5] == 42)
# extras from doubling
__assert__(vec.items[6] == 15)
__assert__(vec.items[7] == 16)

vec = Vector()
for num in [4, 8, 15, 16, 23, 42]:
    vec.append(num)

__assert__(vec.capacity() == 6)
__assert__(vec.size == 6)
__assert__(vec.items[0] == 4)
__assert__(vec.items[1] == 8)
__assert__(vec.items[2] == 15)
__assert__(vec.items[3] == 16)
__assert__(vec.items[4] == 23)
__assert__(vec.items[5] == 42)

vec = vrange(0, 1)
__assert__(vec.capacity() == 1)
__assert__(vec.size == 1)
__assert__(vec.items[0] == 0)

vec = vrange(0, 2)
__assert__(vec.capacity() == 2)
__assert__(vec.size == 2)
__assert__(vec.items[0] == 0)
__assert__(vec.items[1] == 1)

vec = vrange(1, 3)
__assert__(vec.capacity() == 2)
__assert__(vec.size == 2)
__assert__(vec.items[0] == 1)
__assert__(vec.items[1] == 2)

vec = vrange(1, 1)
__assert__(vec.capacity() == 1)
__assert__(vec.size == 0)

vec = vrange(0, -1)
__assert__(vec.capacity() == 1)
__assert__(vec.size == 0)

vec = vrange(1, 100)
__assert__(vec.size == 99)
