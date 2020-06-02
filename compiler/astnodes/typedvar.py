from .node import Node
from .identifier import Identifier
from .typeannotation import TypeAnnotation

class TypedVar(Node):

    def __init__(self, location:[int], identifier:Identifier, typ:TypeAnnotation):
        super().__init__(location, "TypedVar")
        self.identifier = identifier
        self.type = typ

    def tcvisit(self, typechecker):
        return typechecker.TypedVar(self)

    def visit(self, visitor):
        return visitor.TypedVar(self)

    def toJSON(self):
        d = super().toJSON()
        d["identifier"] = self.identifier.toJSON()
        d["type"] = self.type.toJSON()
        return d

