from Declaration import Declaration
from Identifier import Identifier

class ClassDef(Declaration):

    def __init__(self, location:[int], name:Identifier, superclass:Identifier, declarations:[Declaration]):
        super().__init__(self, location, "ClassDef")
        self.name = name
        self.superclass = superclass
        self.declarations = declaration

    def typecheck(self, typechecker):
        # TODO
        typechecker.ClassDef(self)
        for d in self.declarations:
            typechecker.typecheck(d)

    def toJSON(self):
        d = super().toJSON(self)
        return d


