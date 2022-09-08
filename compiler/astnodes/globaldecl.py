from .declaration import Declaration
from .identifier import Identifier
from typing import List


class GlobalDecl(Declaration):

    def __init__(self, location: List[int], variable: Identifier):
        super().__init__(location, "GlobalDecl")
        self.variable = variable

    def visit(self, visitor):
        return visitor.GlobalDecl(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["variable"] = self.variable.toJSON(dump_location)
        return d

    def getIdentifier(self):
        return self.variable
