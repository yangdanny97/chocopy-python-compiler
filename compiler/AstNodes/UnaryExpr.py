from .Expr import Expr

class UnaryExpr(Expr):

    def __init__(self, location:[int], operator:str, operand:Expr):
        super().__init__(self, location, "UnaryExpr")
        self.operand = operand
        self.operator = operator

    def typecheck(self, typechecker):
        typechecker.typecheck(self.operand)
        typechecker.UnaryExpr(self)

    def toJSON(self):
        d = super().toJSON(self)
        return d


