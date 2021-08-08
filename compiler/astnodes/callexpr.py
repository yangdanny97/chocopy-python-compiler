from .expr import Expr
from .identifier import Identifier

class CallExpr(Expr):

    def __init__(self, location:[int], function:Identifier, args:[Expr]):
        super().__init__(location, "CallExpr")
        self.function = function
        self.args = args
        self.isConstructor = False

    def argIsRef(self, idx:int)->bool:
        if self.isConstructor:
            return self.function.inferredType.parameters[idx+1].isRef
        else:
            return self.function.inferredType.parameters[idx].isRef

    def getPythonStr(self, builder):
        # special case for assertions
        if self.function.name == "__assert__":
            builder.addText("assert ")
            self.args[0].getPythonStr(builder)
            return
        self.function.getPythonStr(builder)
        builder.addText("(")
        for i in range(len(self.args)):
            isRef = self.argIsRef(i)
            if isRef:
                self.builder.addText("[")
            self.args[i].getPythonStr(builder)
            if isRef:
                self.builder.addText("]")
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


