from .astnodes import *
from .types import *
from .visitor import Visitor

class TypeEraser(Visitor):

    def BinaryExpr(self, node: BinaryExpr):
        pass

    def IndexExpr(self, node: IndexExpr):
        pass

    def UnaryExpr(self, node: UnaryExpr):
        pass

    def CallExpr(self, node: CallExpr):
        pass

    def ForStmt(self, node: ForStmt):
        pass

    def ListExpr(self, node: ListExpr):
        pass

    def WhileStmt(self, node: WhileStmt):
        pass

    def ReturnStmt(self, node: ReturnStmt):
        pass

    def Identifier(self, node: Identifier):
        pass

    def MemberExpr(self, node: MemberExpr):
        pass

    def IfExpr(self, node: IfExpr):
        pass

    def MethodCallExpr(self, node: MethodCallExpr):
        pass

