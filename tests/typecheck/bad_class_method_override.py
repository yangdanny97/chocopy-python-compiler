class A(object):
    def foo(self:"A", x:int) -> int:
        return x

    def bar(self:"A", x:int) -> int:
        return x

    def baz(self:"A", x:int) -> int:
        return x

    def qux(self:"A", x:int) -> int:
        return x

class B(A):

    # OK override
    def foo(self:"B", x:int) -> int:
        return 0

    # Bad override
    def bar(self:"B") -> int:
        return 0

    # Bad override
    def baz(self:"B", x:int) -> bool:
        return True

    # Bad override
    def qux(self:"B", x:bool) -> int:
        return 0

B()

