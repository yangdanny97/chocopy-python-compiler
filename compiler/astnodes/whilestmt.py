from .stmt import Stmt
from .expr import Expr

class WhileStmt(Stmt):

    def __init__(self, location:[int], condition:Expr, body:[Stmt]):
        super().__init__(location, "WhileStmt")
        self.condition = condition
        self.body = [s for s in body if s is not None]

    def visit(self, typechecker):
        typechecker.visit(self.condition)
        for s in self.body:
            typechecker.visit(s)
        return typechecker.WhileStmt(self)

    def toJSON(self):
        d = super().toJSON()
        d["condition"] = self.condition.toJSON()
        d["body"] = [s.toJSON() for s in self.body]
        return d

