from .declaration import Declaration
from .expr import Expr
from .typedvar import TypedVar

class VarDef(Declaration):

    def __init__(self, location:[int], var:[TypedVar], value:Expr):
        super().__init__(location, "VarDef")
        self.var = var
        self.value = value

    def typecheck(self, typechecker):
        typechecker.typecheck(self.var)
        typechecker.typecheck(self.value)
        return typechecker.VarDef(self)

    def toJSON(self):
        d = super().toJSON()
        d["var"] = self.var.toJSON()
        d["value"] = self.value.toJSON()
        return d

    def getIdentifier(self):
        return self.var.identifier
