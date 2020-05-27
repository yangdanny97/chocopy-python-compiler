from .declaration import Declaration
from .identifier import Identifier

class NonLocalDecl(Declaration):

    def __init__(self, location:[int], variable:Identifier):
        super().__init__(location, "NonLocalDecl")
        self.variable = variable

    def typecheck(self, typechecker):
        return typechecker.NonLocalDecl(self)

    def toJSON(self):
        d = super().toJSON()
        d["variable"] = self.variable.toJSON()
        return d

    def getIdentifier(self):
        return self.variable
