from .node import Node
from .compilererror import CompilerError

class Errors(Node):

    def __init__(self, location:[int], errors:[CompilerError]):
        super().__init__(location, "Errors")
        self.errors = errors

    def visit(self, visitor):
        pass

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["errors"] = [e.toJSON(dump_location) for e in self.errors]
        return d

