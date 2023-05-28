x: int = 1
y: int = 2
a: bool = True
b: bool = False

if a:
    assert True

if a:
    assert True
else:
    assert False

if b:
    assert False

if b:
    assert False
else:
    assert True

if x == y:
    assert False
else:
    assert True

if x == x:
    assert True
else:
    assert False

assert (5 if a else 0) == 5
assert (0 if b else 5) == 5
