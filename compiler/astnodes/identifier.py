from .expr import Expr

class Identifier(Expr):

    def __init__(self, location:[int], name:str):
        super().__init__(location, "Identifier")
        self.name = name
        self.varInstance = None

    def visit(self, visitor):
        return visitor.Identifier(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["name"] = self.name
        return d

    def copy(self):
        cpy = Identifier(self.location, self.name)
        cpy.inferredType = self.inferredType
        cpy.varInstance = self.varInstance
        return cpy

