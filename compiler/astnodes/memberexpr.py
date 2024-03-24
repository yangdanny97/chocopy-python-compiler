from .expr import Expr
from .identifier import Identifier
from typing import List, Union
from ..types import FuncType, ValueType


class MemberExpr(Expr):

    def __init__(self, location: List[int], obj: Expr, member: Identifier):
        super().__init__(location, "MemberExpr")
        self.object = obj
        self.member = member

    def preorder(self, visitor):
        visitor.MemberExpr(self)
        visitor.visit(self.object)
        return self

    def postorder(self, visitor):
        visitor.visit(self.object)
        return visitor.MemberExpr(self)

    def visit(self, visitor):
        return visitor.MemberExpr(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["object"] = self.object.toJSON(dump_location)
        d["member"] = self.member.toJSON(dump_location)
        return d
