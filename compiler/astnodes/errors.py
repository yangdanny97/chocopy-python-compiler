from .node import Node
from .compilererror import CompilerError

class Errors(Node):

    def __init__(self, location:[int], errors:[CompilerError]):
        super().__init__(location, "Errors")
        self.errors = errors

    def visit(self, typechecker):
        pass

    def toJSON(self):
        d = super().toJSON()
        d["errors"] = [e.toJSON() for e in self.errors]
        return d

