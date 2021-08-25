from .literal import Literal

class BooleanLiteral(Literal):

    def __init__(self, location:[int], value:bool):
        super().__init__(location, "BooleanLiteral")
        self.value = value

    def visit(self, visitor):
        return visitor.BooleanLiteral(self)


