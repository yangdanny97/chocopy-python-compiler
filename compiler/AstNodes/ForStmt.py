from .stmt import Stmt
from .expr import Expr
from .identifier import Identifier

class ForStmt(Stmt):

    def __init__(self, location:[int], identifier:Identifier, iterable:Expr, body:[Stmt]):
        super().__init__(location, "ForStmt")
        self.identifier = identifier
        self.iterable = iterable
        self.body = [s for s in body if s is not None]

    def typecheck(self, typechecker):
        typechecker.typecheck(self.iterable)
        typechecker.ForStmt(self)
        typechecker.enterScope()
        for s in self.body:
            typechecker.typecheck(s)
        typechecker.exitScope()

    def toJSON(self):
        d = super().toJSON()
        d["identifier"] = self.identifier.toJSON()
        d["iterable"] = self.iterable.toJSON()
        d["body"] = [s.toJSON() for s in self.body]
        return d

