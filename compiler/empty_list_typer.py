from .astnodes import *
from .types import *
from .visitor import Visitor

# A visitor to refine the types of empty list literals
class EmptyListTyper(Visitor):

    def __init__(self):
        self.expectedListType = None

    def visit(self, node: Node):
        return node.preOrder(self)

    def Program(self, node: Program):
        for d in node.declarations:
            self.visit(d)
        for s in node.statements:
            self.visit(s)

    def ClassDef(self, node: ClassDef):
        for d in node.declarations:
            self.visit(d)

    def FuncDef(self, node: FuncDef):
        for d in node.declarations:
            self.visit(d)
        for s in node.statements:
            self.visit(s)

    def CallExpr(self, node: CallExpr):
        pass
        # for i in range(len(node.args)):

    def AssignStmt(self, node: AssignStmt):
        pass

    def ListExpr(self, node: ListExpr):
        pass

    def MethodCallExpr(self, node: MethodCallExpr):
        pass

    def ReturnStmt(self, node: ReturnStmt):
        pass


