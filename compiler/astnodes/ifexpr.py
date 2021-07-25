from .expr import Expr

class IfExpr(Expr):

    def __init__(self, location:[int], condition:Expr, thenExpr:Expr, elseExpr:Expr):
        super().__init__(location, "IfExpr")
        self.condition = condition
        self.thenExpr = thenExpr
        self.elseExpr = elseExpr

    def visitChildrenForTypecheck(self, visitor):
        visitor.visit(self.condition)
        visitor.visit(self.thenExpr)
        visitor.visit(self.elseExpr)
        return visitor.IfExpr(self)

    def visit(self, visitor):
        return visitor.IfExpr(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["condition"] = self.condition.toJSON(dump_location)
        d["thenExpr"] = self.thenExpr.toJSON(dump_location)
        d["elseExpr"] = self.elseExpr.toJSON(dump_location)
        return d
