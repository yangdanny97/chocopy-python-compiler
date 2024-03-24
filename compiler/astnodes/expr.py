from .node import Node
from typing import List, Optional, Union
from ..types import ValueType, FuncType


class Expr(Node):
    inferredType: Optional[Union[ValueType, FuncType]]

    def __init__(self, location: List[int], kind: str):
        super().__init__(location, kind)
        self.inferredType = None
        self.shouldBoxAsRef = False

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        if self.inferredType is not None:
            d['inferredType'] = self.inferredType.toJSON(dump_location)
        return d

    def inferredValueType(self) -> ValueType:
        assert self.inferredType is not None and isinstance(
            self.inferredType, ValueType)
        return self.inferredType
