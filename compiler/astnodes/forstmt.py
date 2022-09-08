from .stmt import Stmt
from .expr import Expr
from .identifier import Identifier
from typing import List


class ForStmt(Stmt):

    def __init__(self, location: List[int], identifier: Identifier, iterable: Expr, body: List[Stmt]):
        super().__init__(location, "ForStmt")
        self.identifier = identifier
        self.iterable = iterable
        self.body = [s for s in body if s is not None]

    def postorder(self, visitor):
        visitor.visit(self.identifier)
        visitor.visit(self.iterable)
        for s in self.body:
            visitor.visit(s)
        return visitor.ForStmt(self)

    def preorder(self, visitor):
        visitor.ForStmt(self)
        visitor.visit(self.identifier)
        visitor.visit(self.iterable)
        for s in self.body:
            visitor.visit(s)
        return self

    def visit(self, visitor):
        return visitor.ForStmt(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["identifier"] = self.identifier.toJSON(dump_location)
        d["iterable"] = self.iterable.toJSON(dump_location)
        d["body"] = [s.toJSON(dump_location) for s in self.body]
        return d
