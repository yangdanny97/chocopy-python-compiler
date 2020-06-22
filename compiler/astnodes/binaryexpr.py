from .expr import Expr

class BinaryExpr(Expr):

    def __init__(self, location:[int], left:Expr, operator:str, right:Expr):
        super().__init__(location, "BinaryExpr")
        self.left = left
        self.right = right
        self.operator = operator

    def visitChildren(self, typechecker):
        typechecker.visit(self.left)
        typechecker.visit(self.right)
        return typechecker.BinaryExpr(self)

    def visit(self, visitor):
        return visitor.BinaryExpr(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["left"] = self.left.toJSON(dump_location)
        d["right"] = self.right.toJSON(dump_location)
        d["operator"] = self.operator
        return d


