from .node import Node
from .declaration import Declaration
from .stmt import Stmt
from .errors import Errors

# root AST for source file
class Program(Node):

    def __init__(self, location:[int], declarations:[Declaration], statements:[Stmt], errors:Errors):
        super().__init__(location, "Program")
        self.declarations = [d for d in declarations if d is not None]
        self.statements = [s for s in statements if s is not None]
        self.errors = errors

    def getPythonStr(self, builder):
        for d in self.declarations:
            d.getPythonStr(builder)
        for s in self.statements:
            s.getPythonStr(builder)

    def visitChildrenForTypecheck(self, visitor):
        return visitor.Program(self)

    def visit(self, visitor):
        return visitor.Program(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d['declarations'] = [d.toJSON(dump_location) for d in self.declarations]
        d['statements'] = [s.toJSON(dump_location) for s in self.statements]
        d['errors'] = self.errors.toJSON(dump_location)
        return d

