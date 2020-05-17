from .Literal import Literal

class StringLiteral(Literal):

    def __init__(self, location:[int], value:str):
        super().__init__(self, location, "StringLiteral")
        self.value = value

    def typecheck(self, typechecker):
        typechecker.StringLiteral(self)
