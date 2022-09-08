from .literal import Literal
from typing import List


class NoneLiteral(Literal):

    def __init__(self, location: List[int]):
        super().__init__(location, "NoneLiteral")
        self.value = None

    def visit(self, visitor):
        return visitor.NoneLiteral(self)
