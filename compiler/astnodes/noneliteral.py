from .literal import Literal


class NoneLiteral(Literal):

    def __init__(self, location: [int]):
        super().__init__(location, "NoneLiteral")
        self.value = None

    def visit(self, visitor):
        return visitor.NoneLiteral(self)
