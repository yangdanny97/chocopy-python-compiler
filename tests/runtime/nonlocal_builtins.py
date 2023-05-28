

def f():
    x: bool = True
    y: str = "a"

    def g():
        nonlocal x
        nonlocal y
        print(y)
        assert x
    g()


f()
