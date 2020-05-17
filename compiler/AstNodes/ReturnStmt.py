from .Stmt import Stmt
from .Expr import Expr

class ReturnStmt(Stmt):

    def __init__(self, location:[int], value:Expr):
        super().__init__(self, location, "ReturnStmt")
        self.value = value

    def typecheck(self, typechecker):
        typechecker.typecheck(self.value)
        typechecker.ReturnStmt(self)

    def toJSON(self):
        d = super().toJSON(self)
        return d

