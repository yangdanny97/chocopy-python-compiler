from .stmt import Stmt
from .expr import Expr

class ReturnStmt(Stmt):

    def __init__(self, location:[int], value:Expr):
        super().__init__(location, "ReturnStmt")
        self.value = value

    def typecheck(self, typechecker):
        if self.value is not None:
            typechecker.typecheck(self.value)
        return typechecker.ReturnStmt(self)

    def toJSON(self):
        d = super().toJSON()
        if self.value is not None:
            d["value"] = self.value.toJSON()
        else:
            d["value"] = None
        return d

