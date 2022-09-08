from .stmt import Stmt
from .expr import Expr
from typing import List


class AssignStmt(Stmt):

    def __init__(self, location: List[int], targets: List[Expr], value: Expr):
        super().__init__(location, "AssignStmt")
        self.targets = targets
        self.value = value

    def preorder(self, visitor):
        visitor.AssignStmt(self)
        for t in self.targets:
            visitor.visit(t)
        visitor.visit(self.value)
        return self

    def postorder(self, visitor):
        for t in self.targets:
            visitor.visit(t)
        visitor.visit(self.value)
        return visitor.AssignStmt(self)

    def visit(self, visitor):
        return visitor.AssignStmt(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["targets"] = [t.toJSON(dump_location) for t in self.targets]
        d["value"] = self.value.toJSON(dump_location)
        return d
