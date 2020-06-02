from .expr import Expr

class BinaryExpr(Expr):

    def __init__(self, location:[int], left:Expr, operator:str, right:Expr):
        super().__init__(location, "BinaryExpr")
        self.left = left
        self.right = right
        self.operator = operator

    def tcvisit(self, typechecker):
        typechecker.visit(self.left)
        typechecker.visit(self.right)
        return typechecker.BinaryExpr(self)

    def visit(self, visitor):
        return visitor.BinaryExpr(self)

    def toJSON(self):
        d = super().toJSON()
        d["left"] = self.left.toJSON()
        d["right"] = self.right.toJSON()
        d["operator"] = self.operator
        return d


