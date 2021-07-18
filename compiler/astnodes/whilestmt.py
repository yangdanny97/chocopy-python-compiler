from .stmt import Stmt
from .expr import Expr

class WhileStmt(Stmt):

    def __init__(self, location:[int], condition:Expr, body:[Stmt]):
        super().__init__(location, "WhileStmt")
        self.condition = condition
        self.body = [s for s in body if s is not None]

    def visitChildren(self, visitor):
        visitor.visit(self.condition)
        for s in self.body:
            visitor.visit(s)
        return visitor.WhileStmt(self)

    def visit(self, visitor):
        return visitor.WhileStmt(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["condition"] = self.condition.toJSON(dump_location)
        d["body"] = [s.toJSON(dump_location) for s in self.body]
        return d

