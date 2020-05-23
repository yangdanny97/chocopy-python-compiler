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

    def typecheck(self, typechecker):
        typechecker.FuncDef(self)

    def toJSON(self):
        d = super().toJSON()
        d["name"] = self.name.toJSON()
        d["params"] = [t.toJSON() for t in self.params]
        d["returnType"] = self.returnType.toJSON()
        d["declarations"] = [decl.toJSON() for decl in self.declarations]
        d["statements"] = [s.toJSON() for s in self.statements]
        return d

    def getIdentifier(self):
        return self.name

