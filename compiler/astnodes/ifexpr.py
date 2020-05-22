from .expr import Expr

class IfExpr(Expr):

    def __init__(self, location:[int], condition:Expr, thenExpr:Expr, elseExpr:Expr):
        super().__init__(location, "IfExpr")
        self.condition = condition
        self.thenExpr = thenExpr
        self.elseExpr = elseExpr

    def typecheck(self, typechecker):
        typechecker.typecheck(self.condition)
        typechecker.typecheck(self.thenExpr)
        typechecker.typecheck(self.elseExpr)
        typechecker.IfExpr(self)

    def toJSON(self):
        d = super().toJSON()
        d["condition"] = self.condition.toJSON()
        d["thenExpr"] = self.thenExpr.toJSON()
        d["elseExpr"] = self.elseExpr.toJSON()
        return d
