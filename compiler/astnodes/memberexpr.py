from .expr import Expr

class MemberExpr(Expr):

    def __init__(self, location:[int], obj:Expr, member:Expr):
        super().__init__(location, "MemberExpr")
        self.object = obj
        self.member = member

    def visit(self, typechecker):
        typechecker.visit(self.object)
        return typechecker.MemberExpr(self)

    def toJSON(self):
        d = super().toJSON()
        d["object"] = self.object.toJSON()
        d["member"] = self.member.toJSON()
        return d
