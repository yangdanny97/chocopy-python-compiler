from .Declaration import Declaration
from .Identifier import Identifier
from .TypedVar import TypedVar
from .TypeAnnotation import TypeAnnotation
from .Stmt import Stmt

class FuncDef(Declaration):

    # The AST for
    #     def NAME(PARAMS) -> RETURNTYPE:
    #         DECLARATIONS
    #         STATEMENTS

    def __init__(self, location:[int], name:Identifier, params:[TypedVar], returnType:TypeAnnotation, 
        declarations:[Declaration], statements:[Stmt]):
        super().__init__(self, location, "FuncDef")
        self.name = name
        self.params = params
        self.returnType = returnType
        self.declarations = declarations
        self.statements = statements

    def typecheck(self, typechecker):
        typechecker.FuncDef(self)
        # TODO

    def toJSON(self):
        d = super().toJSON(self)
        return d

