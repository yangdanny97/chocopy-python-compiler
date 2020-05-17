from .Node import Node
from .Declaration import Declaration
from .Stmt import Stmt
from .Errors import Errors

# root AST for source file
class Program(Node):

    def __init__(self, location:[int], declarations:[Declaration], statements:[Stmt], errors:Errors):
        super().__init__(self, location, "Program")
        self.declarations = declarations
        self.statements = statements
        self.errors = errors

    def typecheck(self, typechecker):
        typechecker.Program(self)

    def toJSON(self):
        d = super().toJSON(self)
        d['declarations'] = declarations
        d['statements'] = statements
        d['errors'] = errors
        return d

