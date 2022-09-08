from .expr import Expr
from typing import List


class UnaryExpr(Expr):

    def __init__(self, location: List[int], operator: str, operand: Expr):
        super().__init__(location, "UnaryExpr")
        self.operand = operand
        self.operator = operator

    def preorder(self, visitor):
        visitor.UnaryExpr(self)
        visitor.visit(self.operand)
        return self

    def postorder(self, visitor):
        visitor.visit(self.operand)
        return visitor.UnaryExpr(self)

    def visit(self, visitor):
        return visitor.UnaryExpr(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["operator"] = self.operator
        d["operand"] = self.operand.toJSON(dump_location)
        return d
