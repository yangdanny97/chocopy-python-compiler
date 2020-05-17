from .Stmt import Stmt
from .Expr import Expr

class WhileStmt(Stmt):

    def __init__(self, location:[int], condition:Expr, body:[Stmt]):
        super().__init__(self, location, "WhileStmt")
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
        d = super().toJSON(self)
        return d

