from .astnodes import *
from .types import *
from .visitor import Visitor

# A utility visitor to erase the inferred types of expressions


class TypeEraser(Visitor):

    def visit(self, node: Node):
        if isinstance(node, Expr):
            node.inferredType = None
        return node.postorder(self)

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
        self.visit(node.function)

    def MethodCallExpr(self, node: MethodCallExpr):
        self.visit(node.method)

    def NonLocalDecl(self, node: NonLocalDecl):
        self.visit(node.variable)

    def GlobalDecl(self, node: GlobalDecl):
        self.visit(node.variable)
