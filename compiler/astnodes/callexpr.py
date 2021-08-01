from .expr import Expr
from .identifier import Identifier

class CallExpr(Expr):

    def __init__(self, location:[int], function:Identifier, args:[Expr]):
        super().__init__(location, "CallExpr")
        self.function = function
        self.args = args
        self.isConstructor = False

    def getPythonStr(self, builder):
        self.function.getPythonStr(builder)
        builder.addText("(")
        for i in range(len(self.args)):
            self.args[i].getPythonStr(builder)
            if i != len(self.args) - 1:
                builder.addText(", ")
        builder.addText(")")

    def postorder(self, visitor):
        for a in self.args:
            visitor.visit(a)
        return visitor.CallExpr(self)

    def preorder(self, visitor):
        visitor.CallExpr(self)
        for a in self.args:
            visitor.visit(a)
        return self

    def visit(self, visitor):
        return visitor.CallExpr(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["function"] = self.function.toJSON(dump_location)
        d["args"] = [a.toJSON(dump_location) for a in self.args]
        return d


