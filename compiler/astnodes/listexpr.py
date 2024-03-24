from .expr import Expr
from ..types import ValueType
from typing import List, Optional


class ListExpr(Expr):
    emptyListType: Optional[ValueType]

    def __init__(self, location: List[int], elements: List[Expr]):
        super().__init__(location, "ListExpr")
        self.elements = elements
        # this is populated by the EmptyListTyper pass
        self.emptyListType = None

    def preorder(self, visitor):
        visitor.ListExpr(self)
        for e in self.elements:
            visitor.visit(e)
        return self

    def postorder(self, visitor):
        for e in self.elements:
            visitor.visit(e)
        return visitor.ListExpr(self)

    def visit(self, visitor):
        return visitor.ListExpr(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["elements"] = [e.toJSON(dump_location) for e in self.elements]
        return d
