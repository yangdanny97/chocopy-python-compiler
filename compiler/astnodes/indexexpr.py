from .expr import Expr

class IndexExpr(Expr):

    def __init__(self, location:[int], lst:Expr, index:Expr):
        super().__init__(location, "IndexExpr")
        self.list = lst
        self.index = index

    def tcvisit(self, typechecker):
        typechecker.visit(self.list)
        typechecker.visit(self.index)
        return typechecker.IndexExpr(self)

    def visit(self, visitor):
        return visitor.IndexExpr(self)

    def toJSON(self):
        d = super().toJSON()
        d["list"] = self.list.toJSON()
        d["index"] = self.index.toJSON()
        return d
