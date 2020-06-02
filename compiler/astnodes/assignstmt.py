from .stmt import Stmt
from .expr import Expr

class AssignStmt(Stmt):

    def __init__(self, location:[int], targets:[Expr], value:Expr):
        super().__init__(location, "AssignStmt")
        self.targets = targets
        self.value = value

    def tcvisit(self, typechecker):
        for t in self.targets:
            typechecker.visit(t)
        typechecker.visit(self.value)
        return typechecker.AssignStmt(self)

    def visit(self, visitor):
        return visitor.AssignStmt(self)

    def toJSON(self):
        d = super().toJSON()
        d["targets"] = [t.toJSON() for t in self.targets]
        d["value"] = self.value.toJSON()
        return d
