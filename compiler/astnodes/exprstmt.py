from .stmt import Stmt
from .expr import Expr

class ExprStmt(Stmt):

    def __init__(self, location:[int], expr:Expr):
        super().__init__(location, "ExprStmt")
        self.expr = expr

    def visitChildren(self, typechecker):
        typechecker.visit(self.expr)

    def visit(self, visitor):
        return visitor.ExprStmt(self)

    def toJSON(self):
        d = super().toJSON()
        d["expr"] = self.expr.toJSON()
        return d

