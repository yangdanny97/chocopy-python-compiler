from Expr import Expr

class Identifier(Expr):

    def __init__(self, location:[int], name:str):
        super().__init__(self, location, "Identifier")
        self.name = name

    def typecheck(self, typechecker):
        typechecker.Identifier(self)

    def toJSON(self):
        d = super().toJSON(self)
        return d

