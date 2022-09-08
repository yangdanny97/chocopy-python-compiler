from .typeannotation import TypeAnnotation
from typing import List


class ListType(TypeAnnotation):

    def __init__(self, location: List[int], elementType: TypeAnnotation):
        super().__init__(location, "ListType")
        self.elementType = elementType

    def visit(self, visitor):
        return visitor.ListType(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["elementType"] = self.elementType.toJSON(dump_location)
        return d
