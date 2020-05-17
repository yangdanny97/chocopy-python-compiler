from .Expr import Expr

class ListExpr(Expr):

    def __init__(self, location:[int], elements:[Expr]):
        super().__init__(self, location, "ListExpr")
        self.elements = elements

    def typecheck(self, typechecker):
        for e in self.elements:
            typechecker.typecheck(e)
        typechecker.ListExpr(self)

    def toJSON(self):
        d = super().toJSON(self)
        return d


