from .expr import Expr

class UnaryExpr(Expr):

    def __init__(self, location:[int], operator:str, operand:Expr):
        super().__init__(location, "UnaryExpr")
        self.operand = operand
        self.operator = operator

    def visit(self, typechecker):
        typechecker.visit(self.operand)
        return typechecker.UnaryExpr(self)

    def toJSON(self):
        d = super().toJSON()
        d["operator"] = self.operator
        d["operand"] = self.operand.toJSON()
        return d


