from .expr import Expr
from typing import List


class Literal(Expr):

    def __init__(self, location: List[int], kind: str):
        super().__init__(location, kind)
        self.value = None

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        if self.value is not None:
            d['value'] = self.value
        return d
