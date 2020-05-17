from Expr import Expr

class BinaryExpr(Expr):

    def __init__(self, location:[int], left:Expr, operator:str, right:Expr):
        super().__init__(self, location, "BinaryExpr")
        self.left = left
        self.right = right
        self.operator = operator

    def typecheck(self, typechecker):
        typechecker.typecheck(self.left)
        typechecker.typecheck(self.right)
        typechecker.BinaryExpr(self)

    def toJSON(self):
        d = super().toJSON(self)
        return d


