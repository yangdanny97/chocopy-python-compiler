from .expr import Expr

class UnaryExpr(Expr):

    def __init__(self, location:[int], operator:str, operand:Expr):
        super().__init__(location, "UnaryExpr")
        self.operand = operand
        self.operator = operator

    def visitChildren(self, typechecker):
        typechecker.visit(self.operand)
        return typechecker.UnaryExpr(self)

    def visit(self, visitor):
        return visitor.UnaryExpr(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["operator"] = self.operator
        d["operand"] = self.operand.toJSON(dump_location)
        return d


