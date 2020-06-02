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

    def tcvisit(self, typechecker):
        typechecker.ClassDef(self)

    def visit(self, visitor):
        return visitor.ClassDef(self)

    def toJSON(self):
        d = super().toJSON()
        d["name"] = self.name.toJSON()
        d["superClass"] = self.superclass.toJSON()
        d["declarations"] = [decl.toJSON() for decl in self.declarations]
        return d

    def getIdentifier(self):
        return self.name


