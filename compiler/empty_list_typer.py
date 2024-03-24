from .astnodes import *
from .types import *
from .visitor import Visitor
from typing import List, Optional

# A visitor to refine the types of empty list literals []
# based on what they are being assigned to
# Prior to this pass, they have the special type <Empty>


class EmptyListTyper(Visitor):
    expectedType: Optional[ValueType] = None
    expReturnType: Optional[ValueType] = None

    def visit(self, node: Node):
        return node.preorder(self)

    def isEmptyListMultiAssign(self, node: Node) -> bool:
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
                assert isinstance(s, AssignStmt)
                statements = statements + self.transformMultiAssign(s)
            else:
                statements.append(s)
        node.statements = statements

    def FuncDef(self, node: FuncDef):
        assert node.type is not None
        self.expReturnType = node.type.returnType
        statements = []
        for s in node.statements:
            if self.isEmptyListMultiAssign(s):
                assert isinstance(s, AssignStmt)
                statements = statements + self.transformMultiAssign(s)
            else:
                statements.append(s)
        node.statements = statements

    def CallExpr(self, node: CallExpr):
        assert isinstance(node.function.inferredType, FuncType)
        for i in range(len(node.args)):
            self.expectedType = node.function.inferredType.parameters[i]
            self.visit(node.args[i])
        self.expectedType = None

    def AssignStmt(self, node: AssignStmt):
        target_type = node.targets[0].inferredType
        assert isinstance(target_type, ValueType)
        self.expectedType = target_type

    def ListExpr(self, node: ListExpr):
        if self.expectedType is None:
            return
        expType = self.expectedType
        if not isinstance(expType, ListValueType):
            expType = ListValueType(ObjectType())
        if len(node.elements) == 0:
            node.emptyListType = expType.elementType
        else:
            for i in node.elements:
                self.expectedType = expType.elementType
                self.visit(i)
            self.expectedType = None

    def MethodCallExpr(self, node: MethodCallExpr):
        for i in range(len(node.args)):
            assert node.method.inferredType is not None and isinstance(
                node.method.inferredType, FuncType)
            self.expectedType = node.method.inferredType.parameters[i]
            self.visit(node.args[i])
        self.expectedType = None

    def ReturnStmt(self, node: ReturnStmt):
        self.expectedType = self.expReturnType
