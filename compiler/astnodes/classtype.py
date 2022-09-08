from .typeannotation import TypeAnnotation
from typing import List


class ClassType(TypeAnnotation):

    def __init__(self, location: List[int], className: str):
        super().__init__(location, "ClassType")
        self.className = className

    def visit(self, visitor):
        return visitor.ClassType(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["className"] = self.className
        return d
