from .expr import Expr

class Identifier(Expr):

    def __init__(self, location:[int], name:str):
        super().__init__(location, "Identifier")
        self.name = name
        self.isGlobal = False # whether the identifier points to a global variable

    def getPythonStr(self, builder):
        builder.addText(self.name)

    def visitChildrenForTypecheck(self, visitor):
        return visitor.Identifier(self)

    def visit(self, visitor):
        return visitor.Identifier(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["name"] = self.name
        return d

