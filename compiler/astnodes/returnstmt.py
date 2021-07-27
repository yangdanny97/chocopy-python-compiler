from .stmt import Stmt
from .expr import Expr

class ReturnStmt(Stmt):

    def __init__(self, location:[int], value:Expr):
        super().__init__(location, "ReturnStmt")
        self.value = value
        self.isReturn = True
        self.expType = None

    def getPythonStr(self, builder):
        builder.newLine("return ")
        if self.value is not None:
            self.value.getPythonStr(builder)

    def visitChildrenForTypecheck(self, visitor):
        if self.value is not None:
            visitor.visit(self.value)
        return visitor.ReturnStmt(self)

    def visit(self, visitor):
        return visitor.ReturnStmt(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        if self.value is not None:
            d["value"] = self.value.toJSON(dump_location)
        else:
            d["value"] = None
        return d

