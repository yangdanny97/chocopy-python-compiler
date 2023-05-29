def test():
    x: int = 1
    y: [int] = None

    def inner():
        nonlocal x
        for x in y:
            pass
    y = [1, 2, 3]
    inner()
    assert x == 3


test()
