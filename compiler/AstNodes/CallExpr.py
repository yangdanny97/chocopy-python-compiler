from .Expr import Expr
from .Identifier import Identifier

class CallExpr(Expr):

    def __init__(self, location:[int], function:Identifier, args:[Expr]):
        super().__init__(self, location, "CallExpr")
        self.function = function
        self.args = args

    def typecheck(self, typechecker):
        for a in self.args:
            typechecker.typecheck(a)
        typechecker.CallExpr(self)

    def toJSON(self):
        d = super().toJSON(self)
        return d


