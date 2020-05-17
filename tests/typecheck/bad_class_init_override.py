class A(object):
    x:int = 1

    def __init__(self:"A", x:int): # Bad override
        pass

A(1)

