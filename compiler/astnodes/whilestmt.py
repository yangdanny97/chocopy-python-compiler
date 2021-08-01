from .stmt import Stmt
from .expr import Expr

class WhileStmt(Stmt):

    def __init__(self, location:[int], condition:Expr, body:[Stmt]):
        super().__init__(location, "WhileStmt")
        self.condition = condition
        self.body = [s for s in body if s is not None]

    def getPythonStr(self, builder):
        builder.newLine("while ")
        self.condition.getPythonStr(builder)
        builder.addText(":")
        builder.indent()
        for b in self.body:
            b.getPythonStr(builder)
        if len(self.body) == 0:
            builder.addText("pass")
        builder.unindent()

    def postorder(self, visitor):
        visitor.visit(self.condition)
        for s in self.body:
            visitor.visit(s)
        return visitor.WhileStmt(self)

    def preorder(self, visitor):
        visitor.WhileStmt(self)
        visitor.visit(self.condition)
        for s in self.body:
            visitor.visit(s)
        return self

    def visit(self, visitor):
        return visitor.WhileStmt(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["condition"] = self.condition.toJSON(dump_location)
        d["body"] = [s.toJSON(dump_location) for s in self.body]
        return d

