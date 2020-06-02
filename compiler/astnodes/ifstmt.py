from .stmt import Stmt
from .expr import Expr

class IfStmt(Stmt):

    def __init__(self, location:[int], condition:Expr, thenBody:[Stmt], elseBody:[Stmt]):
        super().__init__(location, "IfStmt")
        self.condition = condition
        self.thenBody = [s for s in thenBody if s is not None]
        self.elseBody = [s for s in elseBody if s is not None]

    def tcvisit(self, typechecker):
        typechecker.visit(self.condition)
        for s in self.thenBody:
            typechecker.visit(s)
        for s in self.elseBody:
            typechecker.visit(s)
        return typechecker.IfStmt(self)

    def visit(self, visitor):
        return visitor.IfStmt(self)

    def toJSON(self):
        d = super().toJSON()
        d["condition"] = self.condition.toJSON()
        d["thenBody"] = [s.toJSON() for s in self.thenBody]
        d["elseBody"] = [s.toJSON() for s in self.elseBody]
        return d

