from .literal import Literal


class StringLiteral(Literal):

    def __init__(self, location: [int], value: str):
        super().__init__(location, "StringLiteral")
        self.value = value

    def visit(self, visitor):
        return visitor.StringLiteral(self)
