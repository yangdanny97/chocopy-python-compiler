from .expr import Expr
from .identifier import Identifier
from typing import List


class CallExpr(Expr):

    def __init__(self, location: List[int], function: Identifier, args: List[Expr]):
        super().__init__(location, "CallExpr")
        self.function = function
        self.args = args
        self.isConstructor = False
        self.freevars = []  # captured free vars

    def postorder(self, visitor):
        for a in self.args:
            visitor.visit(a)
        return visitor.CallExpr(self)

    def preorder(self, visitor):
        visitor.CallExpr(self)
        for a in self.args:
            visitor.visit(a)
        return self

    def visit(self, visitor):
        return visitor.CallExpr(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["function"] = self.function.toJSON(dump_location)
        d["args"] = [a.toJSON(dump_location) for a in self.args]
        return d
