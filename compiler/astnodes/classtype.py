from .typeannotation import TypeAnnotation

class ClassType(TypeAnnotation):

    def __init__(self, location:[int], className:str):
        super().__init__(location, "ClassType")
        self.className = className

    def tcvisit(self, typechecker):
        return typechecker.ClassType(self)

    def visit(self, visitor):
        return visitor.ClassType(self)

    def toJSON(self):
        d = super().toJSON()
        d["className"] = self.className
        return d


