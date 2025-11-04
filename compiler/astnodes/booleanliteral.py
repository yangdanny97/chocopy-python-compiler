from .literal import Literal
from typing import List


class BooleanLiteral(Literal):

    def __init__(self, location: List[int], value: bool):
        super().__init__(location, "BooleanLiteral")
        # pyrefly: ignore [bad-assignment]
        self.value = value

    def visit(self, visitor):
        return visitor.BooleanLiteral(self)
