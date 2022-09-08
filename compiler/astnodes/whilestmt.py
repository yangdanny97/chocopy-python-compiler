from .stmt import Stmt
from .expr import Expr
from typing import List


class WhileStmt(Stmt):

    def __init__(self, location: List[int], condition: Expr, body: List[Stmt]):
        super().__init__(location, "WhileStmt")
        self.condition = condition
        self.body = [s for s in body if s is not None]

    def postorder(self, visitor):
        visitor.visit(self.condition)
        for s in self.body:
            visitor.visit(s)
        return visitor.WhileStmt(self)

    def preorder(self, visitor):
        visitor.WhileStmt(self)
        visitor.visit(self.condition)
        for s in self.body:
            visitor.visit(s)
        return self

    def visit(self, visitor):
        return visitor.WhileStmt(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["condition"] = self.condition.toJSON(dump_location)
        d["body"] = [s.toJSON(dump_location) for s in self.body]
        return d
