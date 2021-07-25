from .literal import Literal

class IntegerLiteral(Literal):

    def __init__(self, location:[int], value:int):
        super().__init__(location, "IntegerLiteral")
        self.value = value

    def visitChildrenForTypecheck(self, visitor):
        return visitor.IntegerLiteral(self)

    def visit(self, visitor):
        return visitor.IntegerLiteral(self)
