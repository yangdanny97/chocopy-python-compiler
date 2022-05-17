from .declaration import Declaration
from .expr import Expr
from .typedvar import TypedVar

class VarDef(Declaration):

    def __init__(self, location:[int], var:TypedVar, value:Expr, isAttr:bool=False, attrOfClass=None):
        super().__init__(location, "VarDef")
        self.var = var
        self.value = value
        self.isAttr = isAttr
        self.attrOfClass = attrOfClass

    def preorder(self, visitor):
        visitor.VarDef(self)
        visitor.visit(self.value)
        return self

    def postorder(self, visitor):
        visitor.visit(self.value)
        return visitor.VarDef(self)

    def visit(self, visitor):
        return visitor.VarDef(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["var"] = self.var.toJSON(dump_location)
        d["value"] = self.value.toJSON(dump_location)
        return d

    def getIdentifier(self):
        return self.var.identifier

    def getName(self)->str:
        return self.var.identifier.name
