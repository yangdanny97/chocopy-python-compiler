from .stmt import Stmt
from .expr import Expr

class ReturnStmt(Stmt):

    def __init__(self, location:[int], value:Expr):
        super().__init__(location, "ReturnStmt")
        self.value = value
        self.isReturn = True

    def tcvisit(self, typechecker):
        if self.value is not None:
            typechecker.visit(self.value)
        return typechecker.ReturnStmt(self)

    def visit(self, visitor):
        return visitor.ReturnStmt(self)

    def toJSON(self):
        d = super().toJSON()
        if self.value is not None:
            d["value"] = self.value.toJSON()
        else:
            d["value"] = None
        return d

