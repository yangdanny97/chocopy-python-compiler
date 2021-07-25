from .expr import Expr
from .memberexpr import MemberExpr

class MethodCallExpr(Expr):

    def __init__(self, location:[int], method:MemberExpr, args:[Expr]):
        super().__init__(location, "MethodCallExpr")
        self.method = method
        self.args = args

    def getPythonStr(self, builder):
        self.method.getPythonStr(builder)
        builder.addText("(")
        for i in range(len(self.args)):
            self.args[i].getPythonStr(builder)
            if i != len(self.args) - 1:
                builder.addText(", ")
        builder.addText(")")

    def visitChildrenForTypecheck(self, visitor):
        visitor.visit(self.method.object)
        for a in self.args:
            visitor.visit(a)
        return visitor.MethodCallExpr(self)

    def visit(self, visitor):
        return visitor.MethodCallExpr(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["method"] = self.method.toJSON(dump_location)
        d["args"] = [a.toJSON(dump_location) for a in self.args]
        return d


