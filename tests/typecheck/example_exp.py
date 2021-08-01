# Compute x**y
def exp(x: int, y: int) -> int:
    a: int = 0
    global invocations  # Count calls to this function

    def f(i: int) -> int:
        nonlocal a
        def geta() -> int:
            return a
        if i <= 0:
            return geta()
        else:
            a = a * x
            return f(i-1)
    a = 1
    invocations = invocations + 1
    return f(y)

invocations:int = 0
print(exp(2, 10))
print(exp(3, 3))
print(invocations)