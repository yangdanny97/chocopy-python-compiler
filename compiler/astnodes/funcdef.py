from .declaration import Declaration
from .identifier import Identifier
from .typedvar import TypedVar
from .typeannotation import TypeAnnotation
from .stmt import Stmt
from ..types import FuncType
from typing import List, Optional


class FuncDef(Declaration):
    freevars: List[Identifier]  # used in AST transformations, not printed out
    type: Optional[FuncType] = None  # type signature of function

    # The AST for
    #     def NAME(PARAMS) -> RETURNTYPE:
    #         DECLARATIONS
    #         STATEMENTS

    def __init__(self, location: List[int], name: Identifier, params: List[TypedVar], returnType: TypeAnnotation,
                 declarations: List[Declaration], statements: List[Stmt], isMethod: bool = False):
        super().__init__(location, "FuncDef")
        self.name = name
        self.params = params
        self.returnType = returnType
        self.declarations = declarations
        self.statements = [s for s in statements if s is not None]
        self.isMethod = isMethod
        self.freevars = []

    def getFreevarNames(self):
        return set([v.name for v in self.freevars])

    def preorder(self, visitor):
        visitor.FuncDef(self)
        for d in self.declarations:
            visitor.visit(d)
        for s in self.statements:
            visitor.visit(s)
        return self

    def postorder(self, visitor):
        for d in self.declarations:
            visitor.visit(d)
        for s in self.statements:
            visitor.visit(s)
        return visitor.FuncDef(self)

    def visit(self, visitor):
        return visitor.FuncDef(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["name"] = self.name.toJSON(dump_location)
        d["params"] = [t.toJSON(dump_location) for t in self.params]
        d["returnType"] = self.returnType.toJSON(dump_location)
        d["declarations"] = [decl.toJSON(dump_location)
                             for decl in self.declarations]
        d["statements"] = [s.toJSON(dump_location) for s in self.statements]
        return d

    def getIdentifier(self) -> Identifier:
        return self.name

    def getTypeX(self) -> FuncType:
        assert self.type is not None
        return self.type
