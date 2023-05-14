from .astnodes import *
from .types import *
from .visitor import Visitor
from typing import List

# A visitor to refine the types of empty list literals


class EmptyListTyper(Visitor):

    def __init__(self):
        self.expectedType = None
        self.expReturnType = None

    def visit(self, node: Node):
        return node.preorder(self)

    def isEmptyListMultiAssign(self, node: Node):
        if not isinstance(node, AssignStmt):
            return False
        if len(node.targets) == 1 or not isinstance(node.value, ListExpr):
            return False
        if len(node.value.elements) > 0:
            return False
        return True

    def transformMultiAssign(self, node: AssignStmt) -> List[AssignStmt]:
        statements = []
        for t in node.targets:
            statements.append(AssignStmt(node.location, [t], node.value))
        return statements

    def Program(self, node: Program):
        statements = []
        for s in node.statements:
            if self.isEmptyListMultiAssign(s):
                statements = statements + self.transformMultiAssign(s)
            else:
                statements.append(s)
        node.statements = statements

    def FuncDef(self, node: FuncDef):
        self.expReturnType = node.type.returnType
        statements = []
        for s in node.statements:
            if self.isEmptyListMultiAssign(s):
                statements = statements + self.transformMultiAssign(s)
            else:
                statements.append(s)
        node.statements = statements

    def CallExpr(self, node: CallExpr):
        for i in range(len(node.args)):
            self.expectedType = node.function.inferredType.parameters[i]
            self.visit(node.args[i])
        self.expectedType = None

    def AssignStmt(self, node: AssignStmt):
        self.expectedType = node.targets[0].inferredType

    def ListExpr(self, node: ListExpr):
        if self.expectedType is None:
            return
        expType = self.expectedType
        if isinstance(self.expectedType, ListValueType) and len(node.elements) == 0:
            node.emptyListType = expType.elementType
        else:
            for i in node.elements:
                self.expectedType = expType.elementType
                self.visit(i)
            self.expectedType = None

    def MethodCallExpr(self, node: MethodCallExpr):
        for i in range(len(node.args)):
            self.expectedType = node.method.inferredType.parameters[i]
            self.visit(node.args[i])
        self.expectedType = None

    def ReturnStmt(self, node: ReturnStmt):
        self.expectedType = self.expReturnType
