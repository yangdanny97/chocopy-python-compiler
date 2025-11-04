from .literal import Literal
from typing import List


class IntegerLiteral(Literal):

    def __init__(self, location: List[int], value: int):
        super().__init__(location, "IntegerLiteral")
        # pyrefly: ignore [bad-assignment]
        self.value = value

    def visit(self, visitor):
        return visitor.IntegerLiteral(self)
