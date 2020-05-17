from Literal import Literal

class BooleanLiteral(Literal):

    def __init__(self, location:[int], value:int):
        super().__init__(self, location, "IntegerLiteral")
        self.value = value

    def typecheck(self, typechecker):
        typechecker.IntegerLiteral(self)
