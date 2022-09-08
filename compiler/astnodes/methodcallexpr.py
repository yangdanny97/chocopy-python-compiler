from .expr import Expr
from .memberexpr import MemberExpr
from typing import List


class MethodCallExpr(Expr):

    def __init__(self, location: List[int], method: MemberExpr, args: List[Expr]):
        super().__init__(location, "MethodCallExpr")
        self.method = method
        self.args = args

    def preorder(self, visitor):
        visitor.MethodCallExpr(self)
        visitor.visit(self.method.object)
        for a in self.args:
            visitor.visit(a)
        return self

    def postorder(self, visitor):
        visitor.visit(self.method.object)
        for a in self.args:
            visitor.visit(a)
        return visitor.MethodCallExpr(self)

    def visit(self, visitor):
        return visitor.MethodCallExpr(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["method"] = self.method.toJSON(dump_location)
        d["args"] = [a.toJSON(dump_location) for a in self.args]
        return d
