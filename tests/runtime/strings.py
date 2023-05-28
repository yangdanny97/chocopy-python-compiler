x: str = "123"
y: str = "123"

assert len(x) == 3
assert x == y
assert x == "123"
assert y == x
assert x != "456"
assert x[0] == "1"
assert x[1] == "2"
assert x[2] == "3"

x = "123"
x = x + ""
assert x == "123"
assert len(x) == 3
assert x[0] == "1"
assert x[1] == "2"
assert x[2] == "3"

x = "123"
x = "" + x
assert x == "123"
assert len(x) == 3
assert x[0] == "1"
assert x[1] == "2"
assert x[2] == "3"

x = "123"
x = x + "4"
assert x == "1234"
assert len(x) == 4
assert x[0] == "1"
assert x[1] == "2"
assert x[2] == "3"
assert x[3] == "4"

x = "123"
x = "0" + x
assert x == "0123"
assert len(x) == 4

x = "123"
x = x + y
assert x == "123123"
assert y == "123"
assert len(x) == 6
assert len(y) == 3

x = "123"
x = x + x
assert x == "123123"
assert len(x) == 6

x = "123"
y = x
x = "0"
assert y == "123"
assert len(x) == 1
assert len(y) == 3

assert "1" + "2" + "3" + "4" + "5" == "12345"

x = "123123"
assert x[0] + x[1] + x[2] == x[3] + x[4] + x[5]
