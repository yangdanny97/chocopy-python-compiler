from .expr import Expr

class Identifier(Expr):

    def __init__(self, location:[int], name:str):
        super().__init__(location, "Identifier")
        self.name = name
        self.isGlobal = False # whether the identifier points to a global variable
        self.isRef = False # whether the identifier points to a nonlocal variable

    def visit(self, visitor):
        return visitor.Identifier(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["name"] = self.name
        return d

