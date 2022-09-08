from .expr import Expr
from typing import List


class BinaryExpr(Expr):

    def __init__(self, location: List[int], left: Expr, operator: str, right: Expr):
        super().__init__(location, "BinaryExpr")
        self.left = left
        self.right = right
        self.operator = operator

    def preorder(self, visitor):
        visitor.BinaryExpr(self)
        visitor.visit(self.left)
        visitor.visit(self.right)
        return self

    def postorder(self, visitor):
        visitor.visit(self.left)
        visitor.visit(self.right)
        return visitor.BinaryExpr(self)

    def visit(self, visitor):
        return visitor.BinaryExpr(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["left"] = self.left.toJSON(dump_location)
        d["right"] = self.right.toJSON(dump_location)
        d["operator"] = self.operator
        return d
