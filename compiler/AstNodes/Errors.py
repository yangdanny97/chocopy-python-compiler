from .Node import Node
from .CompilerError import CompilerError

class Errors(Node):

    def __init__(self, location:[int], errors:[CompilerError]):
        super().__init__(self, location, "Errors")
        self.errors = errors

    def typecheck(self, typechecker):
        pass

    def toJSON(self):
        d = super().toJSON(self)
        return d

