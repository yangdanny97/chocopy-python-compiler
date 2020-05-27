from .expr import Expr
from .identifier import Identifier

class CallExpr(Expr):

    def __init__(self, location:[int], function:Identifier, args:[Expr]):
        super().__init__(location, "CallExpr")
        self.function = function
        self.args = args

    def visit(self, typechecker):
        for a in self.args:
            typechecker.visit(a)
        return typechecker.CallExpr(self)

    def toJSON(self):
        d = super().toJSON()
        d["function"] = self.function.toJSON()
        d["args"] = [a.toJSON() for a in self.args]
        return d


