x: str = "123"
y: str = ""
z: str = "12345"
char: str = "c"
print(x)
print(y)
print(z)
assert len(x) == 3
assert len(y) == 0
assert len(z) == 5
assert char == char[0]

print(x[0])

for char in y:
    print(char)

for char in z:
    print(char)

assert x[0] == "1"
assert x[1] == "2"
assert x[2] == "3"

x = x + x[0]
assert x == "1231"

x = x + ""
assert x == "1231"

x = "" + x
assert x == "1231"

assert y == ""
assert y != x
assert x != "321"
assert "123" == "123"
assert x == x
assert "" == ""
assert x != ""
