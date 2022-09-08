from .stmt import Stmt
from .expr import Expr
from typing import List


class IfStmt(Stmt):

    def __init__(self, location: List[int], condition: Expr, thenBody: List[Stmt], elseBody: List[Stmt]):
        super().__init__(location, "IfStmt")
        self.condition = condition
        self.thenBody = [s for s in thenBody if s is not None]
        self.elseBody = [s for s in elseBody if s is not None]

    def postorder(self, visitor):
        visitor.visit(self.condition)
        for s in self.thenBody:
            visitor.visit(s)
        for s in self.elseBody:
            visitor.visit(s)
        return visitor.IfStmt(self)

    def preorder(self, visitor):
        visitor.IfStmt(self)
        visitor.visit(self.condition)
        for s in self.thenBody:
            visitor.visit(s)
        for s in self.elseBody:
            visitor.visit(s)
        return self

    def visit(self, visitor):
        return visitor.IfStmt(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["condition"] = self.condition.toJSON(dump_location)
        d["thenBody"] = [s.toJSON(dump_location) for s in self.thenBody]
        d["elseBody"] = [s.toJSON(dump_location) for s in self.elseBody]
        return d
