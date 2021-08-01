from .typeannotation import TypeAnnotation

class ClassType(TypeAnnotation):

    def __init__(self, location:[int], className:str):
        super().__init__(location, "ClassType")
        self.className = className

    def getPythonStr(self, builder):
        builder.addText(self.className)

    def visit(self, visitor):
        return visitor.ClassType(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["className"] = self.className
        return d


