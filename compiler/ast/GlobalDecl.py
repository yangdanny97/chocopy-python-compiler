from Declaration import Declaration
from Identifier import Identifier

class GlobalDecl(Declaration):

    def __init__(self, location:[int], variable:Identifier):
        super().__init__(self, location, "GlobalDecl")
        self.variable = variable

    def typecheck(self, typechecker):
        typechecker.GlobalDecl(self)

    def toJSON(self):
        d = super().toJSON(self)
        return d
