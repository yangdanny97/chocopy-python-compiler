from .Stmt import Stmt
from .Expr import Expr

class ExprStmt(Stmt):

    def __init__(self, location:[int], expr:Expr):
        super().__init__(location, "ExprStmt")
        self.expr = expr

    def typecheck(self, typechecker):
        typechecker.typecheck(self.expr)
        typechecker.ExprStmt(self)

    def toJSON(self):
        d = super().toJSON()
        d["expr"] = self.expr.toJSON()
        return d

