from .literal import Literal

class StringLiteral(Literal):

    def __init__(self, location:[int], value:str):
        super().__init__(location, "StringLiteral")
        self.value = value

    def visitChildrenForTypecheck(self, visitor):
        visitor.StringLiteral(self)

    def visit(self, visitor):
        return visitor.StringLiteral(self)
