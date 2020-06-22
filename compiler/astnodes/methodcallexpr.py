from .expr import Expr
from .memberexpr import MemberExpr

class MethodCallExpr(Expr):

    def __init__(self, location:[int], method:MemberExpr, args:[Expr]):
        super().__init__(location, "MethodCallExpr")
        self.method = method
        self.args = args

    def visitChildren(self, typechecker):
        typechecker.visit(self.method.object)
        for a in self.args:
            typechecker.visit(a)
        return typechecker.MethodCallExpr(self)

    def visit(self, visitor):
        return visitor.MethodCallExpr(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["method"] = self.method.toJSON(dump_location)
        d["args"] = [a.toJSON(dump_location) for a in self.args]
        return d


