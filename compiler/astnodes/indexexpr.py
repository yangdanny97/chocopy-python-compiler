from .expr import Expr

class IndexExpr(Expr):

    def __init__(self, location:[int], lst:Expr, index:Expr):
        super().__init__(location, "IndexExpr")
        self.list = lst
        self.index = index

    def getPythonStr(self, builder):
        self.list.getPythonStr(builder)
        builder.addText("[")
        self.index.getPythonStr(builder)
        builder.addText("]")

    def visitChildrenForTypecheck(self, visitor):
        visitor.visit(self.list)
        visitor.visit(self.index)
        return visitor.IndexExpr(self)

    def visit(self, visitor):
        return visitor.IndexExpr(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["list"] = self.list.toJSON(dump_location)
        d["index"] = self.index.toJSON(dump_location)
        return d
