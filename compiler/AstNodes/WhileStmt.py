from .Stmt import Stmt
from .Expr import Expr

class WhileStmt(Stmt):

    def __init__(self, location:[int], condition:Expr, body:[Stmt]):
        super().__init__(location, "WhileStmt")
        self.condition = condition
        self.body = body

    def typecheck(self, typechecker):
        typechecker.typecheck(self.condition)
        typechecker.WhileStmt(self)
        typechecker.enterScope()
        for s in self.body:
            typechecker.typecheck(s)
        typechecker.exitScope()

    def toJSON(self):
        d = super().toJSON()
        d["condition"] = self.condition.toJSON()
        d["body"] = [s.toJSON() for s in self.body]
        return d

