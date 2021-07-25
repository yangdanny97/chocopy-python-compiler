from .expr import Expr

class ListExpr(Expr):

    def __init__(self, location:[int], elements:[Expr]):
        super().__init__(location, "ListExpr")
        self.elements = elements

    def getPythonStr(self, builder):
        builder.addText("[")
        for i in range(len(self.elements)):
            self.elements[i].getPythonStr(builder)
            if i != len(self.elements) - 1:
                builder.addText(", ")
        builder.addText("]")

    def visitChildrenForTypecheck(self, visitor):
        for e in self.elements:
            visitor.visit(e)
        return visitor.ListExpr(self)

    def visit(self, visitor):
        return visitor.ListExpr(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["elements"] = [e.toJSON(dump_location) for e in self.elements]
        return d


