from .literal import Literal
from typing import List


class StringLiteral(Literal):

    def __init__(self, location: List[int], value: str):
        super().__init__(location, "StringLiteral")
        # pyrefly: ignore [bad-assignment]
        self.value = value

    def visit(self, visitor):
        return visitor.StringLiteral(self)
