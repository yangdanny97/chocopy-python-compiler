from .expr import Expr

class Identifier(Expr):

    def __init__(self, location:[int], name:str):
        super().__init__(location, "Identifier")
        self.name = name

    def visitChildren(self, typechecker):
        return typechecker.Identifier(self)

    def visit(self, visitor):
        return visitor.Identifier(self)

    def toJSON(self):
        d = super().toJSON()
        d["name"] = self.name
        return d

