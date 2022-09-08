from .stmt import Stmt
from .expr import Expr
from typing import List


class ExprStmt(Stmt):

    def __init__(self, location: List[int], expr: Expr):
        super().__init__(location, "ExprStmt")
        self.expr = expr

    def preorder(self, visitor):
        visitor.ExprStmt(self)
        visitor.visit(self.expr)
        return self

    def postorder(self, visitor):
        visitor.visit(self.expr)
        return visitor.ExprStmt(self)

    def visit(self, visitor):
        return visitor.ExprStmt(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["expr"] = self.expr.toJSON(dump_location)
        return d
