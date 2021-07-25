from .declaration import Declaration
from .identifier import Identifier
from .typedvar import TypedVar
from .typeannotation import TypeAnnotation
from .stmt import Stmt

class FuncDef(Declaration):

    # The AST for
    #     def NAME(PARAMS) -> RETURNTYPE:
    #         DECLARATIONS
    #         STATEMENTS

    def __init__(self, location:[int], name:Identifier, params:[TypedVar], returnType:TypeAnnotation, 
        declarations:[Declaration], statements:[Stmt], isMethod:bool = False):
        super().__init__(location, "FuncDef")
        self.name = name
        self.params = params
        self.returnType = returnType
        self.declarations = declarations
        self.statements = [s for s in statements if s is not None]
        self.isMethod = isMethod
        self.freevars = [] # used in AST transformations, not printed out
        self.type = None # type signature of function

    def visitChildrenForTypecheck(self, visitor):
        return visitor.FuncDef(self)

    def visit(self, visitor):
        return visitor.FuncDef(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["name"] = self.name.toJSON(dump_location)
        d["params"] = [t.toJSON(dump_location) for t in self.params]
        d["returnType"] = self.returnType.toJSON(dump_location)
        d["declarations"] = [decl.toJSON(dump_location) for decl in self.declarations]
        d["statements"] = [s.toJSON(dump_location) for s in self.statements]
        return d

    def getIdentifier(self):
        return self.name

