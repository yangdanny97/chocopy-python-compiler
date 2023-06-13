from .node import Node
from typing import List
from ..types import ValueType


class Expr(Node):
    inferredType: ValueType

    def __init__(self, location: List[int], kind: str):
        super().__init__(location, kind)
        self.inferredType = None
        self.shouldBoxAsRef = False

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        if self.inferredType is not None:
            d['inferredType'] = self.inferredType.toJSON(dump_location)
        return d
