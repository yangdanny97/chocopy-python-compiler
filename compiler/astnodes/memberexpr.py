from .expr import Expr
from .identifier import Identifier

class MemberExpr(Expr):

    def __init__(self, location:[int], obj:Expr, member:Identifier):
        super().__init__(location, "MemberExpr")
        self.object = obj
        self.member = member

    def visitChildren(self, typechecker):
        typechecker.visit(self.object)
        return typechecker.MemberExpr(self)

    def visit(self, visitor):
        return visitor.MemberExpr(self)

    def toJSON(self):
        d = super().toJSON()
        d["object"] = self.object.toJSON()
        d["member"] = self.member.toJSON()
        return d
