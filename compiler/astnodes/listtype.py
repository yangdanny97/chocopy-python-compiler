from .typeannotation import TypeAnnotation

class ListType(TypeAnnotation):

    def __init__(self, location:[int], elementType:TypeAnnotation):
        super().__init__(location, "ListType")
        self.elementType = elementType

    def visitChildren(self, typechecker):
        return typechecker.ListType(self)

    def visit(self, visitor):
        return visitor.ListType(self)

    def toJSON(self):
        d = super().toJSON()
        d["elementType"] = self.elementType.toJSON()
        return d

