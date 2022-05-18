from .astnodes import *
from collections import defaultdict
from .builder import Builder


class Visitor:

    def visit(self, node: Node):
        return node.visit(self)

    # TOP LEVEL & DECLARATIONS

    def Program(self, node: Program):
        pass

    def VarDef(self, node: VarDef):
        pass

    def ClassDef(self, node: ClassDef):
        pass

    def FuncDef(self, node: FuncDef):
        pass

    # STATEMENTS

    def NonLocalDecl(self, node: NonLocalDecl):
        pass

    def GlobalDecl(self, node: GlobalDecl):
        pass

    def AssignStmt(self, node: AssignStmt):
        pass

    def IfStmt(self, node: IfStmt):
        pass

    def ExprStmt(self, node: ExprStmt):
        pass

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

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        pass

    def IntegerLiteral(self, node: IntegerLiteral):
        pass

    def NoneLiteral(self, node: NoneLiteral):
        pass

    def StringLiteral(self, node: StringLiteral):
        pass

    # TYPES

    def TypedVar(self, node: TypedVar):
        pass

    def ListType(self, node: ListType):
        pass

    def ClassType(self, node: ClassType):
        pass


class CommonVisitor(Visitor):
    returnType = None  # for tracking return types in functions
    counter = 0  # for labels

    # helpers for handling locals

    locals = []

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
