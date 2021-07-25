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

    def getPythonStr(self, builder):
        builder.newLine("def ")
        self.name.getPythonStr(builder)
        builder.addText("(")
        for i in range(len(self.params)):
            self.params[i].getPythonStr(builder)
            if i != len(self.params) - 1:
                builder.addText(", ")
        builder.addText("):")
        builder.indent()
        for d in self.declarations:
            d.getPythonStr(builder)
        for s in self.statements:
            s.getPythonStr(builder)
        if len(self.declarations) == 0 and len(self.statements) == 0:
            builder.addText("pass")
        builder.unindent()
        builder.newLine()

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

