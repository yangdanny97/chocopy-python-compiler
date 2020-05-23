from .declaration import Declaration
from .identifier import Identifier

class ClassDef(Declaration):

    def __init__(self, location:[int], name:Identifier, superclass:Identifier, declarations:[Declaration]):
        super().__init__(location, "ClassDef")
        self.name = name
        self.superclass = superclass
        self.declarations = declarations

    def typecheck(self, typechecker):
        typechecker.ClassDef(self)

    def toJSON(self):
        d = super().toJSON()
        d["name"] = self.name.toJSON()
        d["superClass"] = self.superclass.toJSON()
        d["declarations"] = [decl.toJSON() for decl in self.declarations]
        return d

    def getIdentifier(self):
        return self.name


