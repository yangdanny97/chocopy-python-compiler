from .declaration import Declaration
from .expr import Expr
from .typedvar import TypedVar

class VarDef(Declaration):

    def __init__(self, location:[int], var:[TypedVar], value:Expr, isAttr:bool=False):
        super().__init__(location, "VarDef")
        self.var = var
        self.value = value
        self.isAttr = isAttr

    def visit(self, typechecker):
        typechecker.visit(self.value)
        return typechecker.VarDef(self)

    def toJSON(self):
        d = super().toJSON()
        d["var"] = self.var.toJSON()
        d["value"] = self.value.toJSON()
        return d

    def getIdentifier(self):
        return self.var.identifier
