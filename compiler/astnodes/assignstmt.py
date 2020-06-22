from .stmt import Stmt
from .expr import Expr

class AssignStmt(Stmt):

    def __init__(self, location:[int], targets:[Expr], value:Expr):
        super().__init__(location, "AssignStmt")
        self.targets = targets
        self.value = value

    def visitChildren(self, typechecker):
        for t in self.targets:
            typechecker.visit(t)
        typechecker.visit(self.value)
        return typechecker.AssignStmt(self)

    def visit(self, visitor):
        return visitor.AssignStmt(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["targets"] = [t.toJSON(dump_location) for t in self.targets]
        d["value"] = self.value.toJSON(dump_location)
        return d
