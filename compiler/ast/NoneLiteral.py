from Literal import Literal

class NoneLiteral(Literal):

    def __init__(self, location:[int]):
        super().__init__(self, location, "NoneLiteral")
        self.value = value

    def typecheck(self, typechecker):
        typechecker.NoneLiteral(self)
