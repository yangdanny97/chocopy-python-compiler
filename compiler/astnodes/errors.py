from .node import Node
from .compilererror import CompilerError
from typing import List


class Errors(Node):

    def __init__(self, location: List[int], errors: List[CompilerError]):
        super().__init__(location, "Errors")
        self.errors = errors

    def visit(self, visitor):
        return self

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["errors"] = [e.toJSON(dump_location) for e in self.errors]
        return d
