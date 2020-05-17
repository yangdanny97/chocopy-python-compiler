from .TypeAnnotation import TypeAnnotation

class ClassType(TypeAnnotation):

    def __init__(self, location:[int], className:str):
        super().__init__(self, location, "ClassType")
        self.className = className

    def typecheck(self, typechecker):
        typechecker.ClassType(self)

    def toJSON(self):
        d = super().toJSON(self)
        return d


