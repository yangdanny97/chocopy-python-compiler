from Expr import Expr

class MemberExpr(Expr):

    def __init__(self, location:[int], obj:Expr, member:Expr):
        super().__init__(self, location, "MemberExpr")
        self.object = obj
        self.member = member

    def typecheck(self, typechecker):
        typechecker.typecheck(self.object)
        typechecker.typecheck(self.member)
        typechecker.MemberExpr(self)

    def toJSON(self):
        d = super().toJSON(self)
        return d
