from .astnodes import *
from collections import defaultdict
from .builder import Builder
from typing import List, Any


class Visitor:

    def visit(self, node: Node) -> Any:
        return node.visit(self)

    # TOP LEVEL & DECLARATIONS

    def Program(self, node: Program) -> Any:
        pass

    def VarDef(self, node: VarDef) -> Any:
        pass

    def ClassDef(self, node: ClassDef) -> Any:
        pass

    def FuncDef(self, node: FuncDef) -> Any:
        pass

    # STATEMENTS

    def NonLocalDecl(self, node: NonLocalDecl) -> Any:
        pass

    def GlobalDecl(self, node: GlobalDecl) -> Any:
        pass

    def AssignStmt(self, node: AssignStmt) -> Any:
        pass

    def IfStmt(self, node: IfStmt) -> Any:
        pass

    def ExprStmt(self, node: ExprStmt) -> Any:
        pass

    def BinaryExpr(self, node: BinaryExpr) -> Any:
        pass

    def IndexExpr(self, node: IndexExpr) -> Any:
        pass

    def UnaryExpr(self, node: UnaryExpr) -> Any:
        pass

    def CallExpr(self, node: CallExpr) -> Any:
        pass

    def ForStmt(self, node: ForStmt) -> Any:
        pass

    def ListExpr(self, node: ListExpr) -> Any:
        pass

    def WhileStmt(self, node: WhileStmt) -> Any:
        pass

    def ReturnStmt(self, node: ReturnStmt) -> Any:
        pass

    def Identifier(self, node: Identifier) -> Any:
        pass

    def MemberExpr(self, node: MemberExpr) -> Any:
        pass

    def IfExpr(self, node: IfExpr) -> Any:
        pass

    def MethodCallExpr(self, node: MethodCallExpr) -> Any:
        pass

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral) -> Any:
        pass

    def IntegerLiteral(self, node: IntegerLiteral) -> Any:
        pass

    def NoneLiteral(self, node: NoneLiteral) -> Any:
        pass

    def StringLiteral(self, node: StringLiteral) -> Any:
        pass

    # TYPES

    def TypedVar(self, node: TypedVar) -> Any:
        pass

    def ListType(self, node: ListType) -> Any:
        pass

    def ClassType(self, node: ClassType) -> Any:
        pass


class CommonVisitor(Visitor):
    returnType = None  # for tracking return types in functions
    counter = 0  # for labels

    # helpers for handling locals
    locals: List[defaultdict] = []

    def enterScope(self):
        self.locals.append(defaultdict(lambda: None))

    def exitScope(self):
        self.locals.pop()

    # helpers for building code

    def instr(self, instr: str):
        self.currentBuilder().newLine(instr)

    def currentBuilder(self) -> Builder:
        raise Exception("unimplemented")

    def emit(self) -> str:
        return self.currentBuilder().emit()
