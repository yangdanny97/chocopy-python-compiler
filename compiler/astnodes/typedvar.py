from .node import Node
from .identifier import Identifier
from .typeannotation import TypeAnnotation
from ..types import ValueType, VarInstance
from typing import List


class TypedVar(Node):
    t: ValueType = None  # the typechecked type goes here
    varInstance: VarInstance = None

    def __init__(self, location: List[int], identifier: Identifier, typ: TypeAnnotation):
        super().__init__(location, "TypedVar")
        self.identifier = identifier
        self.type = typ

    def name(self):
        return self.identifier.name

    def visit(self, visitor):
        return visitor.TypedVar(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["identifier"] = self.identifier.toJSON(dump_location)
        d["type"] = self.type.toJSON(dump_location)
        return d
