from .expr import Expr


class ListExpr(Expr):

    def __init__(self, location: [int], elements: [Expr]):
        super().__init__(location, "ListExpr")
        self.elements = elements
        self.emptyListType = None

    def preorder(self, visitor):
        visitor.ListExpr(self)
        for e in self.elements:
            visitor.visit(e)
        return self

    def postorder(self, visitor):
        for e in self.elements:
            visitor.visit(e)
        return visitor.ListExpr(self)

    def visit(self, visitor):
        return visitor.ListExpr(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["elements"] = [e.toJSON(dump_location) for e in self.elements]
        return d
