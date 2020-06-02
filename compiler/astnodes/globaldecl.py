from .declaration import Declaration
from .identifier import Identifier

class GlobalDecl(Declaration):

    def __init__(self, location:[int], variable:Identifier):
        super().__init__(location, "GlobalDecl")
        self.variable = variable

    def tcvisit(self, typechecker):
        return typechecker.GlobalDecl(self)

    def visit(self, visitor):
        return visitor.GlobalDecl(self)

    def toJSON(self):
        d = super().toJSON()
        d["variable"] = self.variable.toJSON()
        return d

    def getIdentifier(self):
        return self.variable
