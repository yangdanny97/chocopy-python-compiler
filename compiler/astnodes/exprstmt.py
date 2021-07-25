from .stmt import Stmt
from .expr import Expr

class ExprStmt(Stmt):

    def __init__(self, location:[int], expr:Expr):
        super().__init__(location, "ExprStmt")
        self.expr = expr

    def visitChildrenForTypecheck(self, visitor):
        visitor.visit(self.expr)

    def visit(self, visitor):
        return visitor.ExprStmt(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["expr"] = self.expr.toJSON(dump_location)
        return d

