from .declaration import Declaration
from .identifier import Identifier
from .vardef import VarDef
from .funcdef import FuncDef

class ClassDef(Declaration):

    def __init__(self, location:[int], name:Identifier, superclass:Identifier, declarations:[Declaration]):
        super().__init__(location, "ClassDef")
        self.name = name
        self.superclass = superclass
        for d in declarations:
            if isinstance(d, VarDef):
                d.isAttr = True
            if isinstance(d, FuncDef):
                d.isMethod = True
        self.declarations = declarations

    def visitChildren(self, visitor):
        visitor.ClassDef(self)

    def visit(self, visitor):
        return visitor.ClassDef(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["name"] = self.name.toJSON(dump_location)
        d["superClass"] = self.superclass.toJSON(dump_location)
        d["declarations"] = [decl.toJSON(dump_location) for decl in self.declarations]
        return d

    def getIdentifier(self):
        return self.name


