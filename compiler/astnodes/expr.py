from .node import Node
from typing import List


class Expr(Node):

    def __init__(self, location: List[int], kind: str):
        super().__init__(location, kind)
        self.inferredType = None
        self.shouldBoxAsRef = False

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        if self.inferredType is not None:
            d['inferredType'] = self.inferredType.toJSON(dump_location)
        return d
