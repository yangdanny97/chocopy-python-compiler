x: int = 1


def test():
    y: [int] = None

    def inner():
        global x
        for x in y:
            pass
    y = [1, 2, 3]
    inner()
    assert x == 3


test()
