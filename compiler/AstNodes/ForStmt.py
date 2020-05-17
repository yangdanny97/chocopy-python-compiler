from .Stmt import Stmt
from .Expr import Expr
from .Identifier import Identifier

class ForStmt(Stmt):

    def __init__(self, location:[int], identifier:Identifier, iterable:Expr, body:[Stmt]):
        super().__init__(self, location, "ForStmt")
        self.identifier = identifier
        self.iterable = iterable
        self.body = body

    def typecheck(self, typechecker):
        typechecker.typecheck(self.iterable)
        typechecker.ForStmt(self)
        typechecker.enterScope()
        for s in self.body:
            typechecker.typecheck(s)
        typechecker.exitScope()

    def toJSON(self):
        d = super().toJSON(self)
        return d

