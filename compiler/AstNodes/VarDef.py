from .Declaration import Declaration
from .Expr import Expr
from .TypedVar import TypedVar

class VarDef(Declaration):

    def __init__(self, location:[int], var:[TypedVar], value:Expr):
        super().__init__(self, location, "VarDef")
        self.var = var
        self.value = value

    def typecheck(self, typechecker):
        typechecker.typecheck(self.var)
        typechecker.typecheck(self.value)
        typechecker.VarDef(self)

    def toJSON(self):
        d = super().toJSON(self)
        return d
