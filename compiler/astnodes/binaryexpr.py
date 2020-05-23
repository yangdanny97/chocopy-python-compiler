from .expr import Expr

class BinaryExpr(Expr):

    def __init__(self, location:[int], left:Expr, operator:str, right:Expr):
        super().__init__(location, "BinaryExpr")
        self.left = left
        self.right = right
        self.operator = operator

    def typecheck(self, typechecker):
        typechecker.typecheck(self.left)
        typechecker.typecheck(self.right)
        return typechecker.BinaryExpr(self)

    def toJSON(self):
        d = super().toJSON()
        d["left"] = self.left.toJSON()
        d["right"] = self.right.toJSON()
        d["operator"] = self.operator
        return d


