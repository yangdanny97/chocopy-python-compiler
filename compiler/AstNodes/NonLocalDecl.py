from .Declaration import Declaration
from .Identifier import Identifier

class NonLocalDecl(Declaration):

    def __init__(self, location:[int], variable:Identifier):
        super().__init__(self, location, "NonLocalDecl")
        self.variable = variable

    def typecheck(self, typechecker):
        typechecker.NonLocalDecl(self)

    def toJSON(self):
        d = super().toJSON(self)
        return d
