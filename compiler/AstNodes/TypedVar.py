from .Node import Node
from .Identifier import Identifier
from .TypeAnnotation import TypeAnnotation

class TypedVar(Node):

    def __init__(self, location:[int], identifier:Identifier, typ:TypeAnnotation):
        super().__init__(self, location, "TypedVar")
        self.identifier = identifier
        self.type = typ

    def typecheck(self, typechecker):
        typechecker.TypedVar(self)

    def toJSON(self):
        d = super().toJSON(self)
        return d

