from .expr import Expr

class ListExpr(Expr):

    def __init__(self, location:[int], elements:[Expr]):
        super().__init__(location, "ListExpr")
        self.elements = elements

    def visitChildren(self, typechecker):
        for e in self.elements:
            typechecker.visit(e)
        return typechecker.ListExpr(self)

    def visit(self, visitor):
        return visitor.ListExpr(self)

    def toJSON(self):
        d = super().toJSON()
        d["elements"] = [e.toJSON() for e in self.elements]
        return d


