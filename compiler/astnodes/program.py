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

    def typecheck(self, typechecker):
        typechecker.Program(self)

    def toJSON(self):
        d = super().toJSON()
        d['declarations'] = [d.toJSON() for d in self.declarations]
        d['statements'] = [s.toJSON() for s in self.statements]
        d['errors'] = self.errors.toJSON()
        return d

