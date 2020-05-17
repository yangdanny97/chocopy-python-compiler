from .Stmt import Stmt
from .Expr import Expr

class AssignStmt(Stmt):

    def __init__(self, location:[int], targets:[Expr], value:Expr):
        super().__init__(self, location, "AssignStmt")
        self.targets = targets
        self.value = value

    def typecheck(self, typechecker):
        for t in self.targets:
            typechecker.typecheck(t)
        typechecker.typecheck(self.value)
        typechecker.AssignStmt(self)

    def toJSON(self):
        d = super().toJSON(self)
        return d
