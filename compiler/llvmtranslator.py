from .astnodes import *
from .types import *
from collections import defaultdict
from .typechecker import TypeChecker


class LLVMTranslator:
    def __init__(self, tc:TypeChecker):
        self.tc = tc
        pass # TODO setup

    def visit(self, node: Node):
        return node.visit(self)

    # set up standard library functions

    def stdlibPrint(self):
        pass # TODO

    def stdlibLen(self):
        pass # TODO

    def stdlibInput(self):
        pass # TODO

    # TOP LEVEL & DECLARATIONS

    def Program(self, node: Program):
        pass # TODO

    def VarDef(self, node: VarDef):
        pass # TODO

    def ClassDef(self, node: ClassDef):
        pass # TODO

    def FuncDef(self, node: FuncDef):
        pass # TODO

    # STATEMENTS

    def NonLocalDecl(self, node: NonLocalDecl):
        pass # TODO

    def GlobalDecl(self, node: GlobalDecl):
        pass # TODO

    def AssignStmt(self, node: AssignStmt):
        pass # TODO

    def IfStmt(self, node: IfStmt):
        pass # TODO

    def BinaryExpr(self, node: BinaryExpr):
        pass # TODO

    def IndexExpr(self, node: IndexExpr):
        pass # TODO

    def UnaryExpr(self, node: UnaryExpr):
        pass # TODO

    def CallExpr(self, node: CallExpr):
        pass # TODO

    def ForStmt(self, node: ForStmt):
        pass # TODO

    def ListExpr(self, node: ListExpr):
        pass # TODO

    def WhileStmt(self, node: WhileStmt):
        pass # TODO

    def ReturnStmt(self, node: ReturnStmt):
        pass # TODO

    def Identifier(self, node: Identifier):
        pass # TODO

    def MemberExpr(self, node: MemberExpr):
        pass # TODO

    def IfExpr(self, node: IfExpr):
        pass # TODO

    def MethodCallExpr(self, node: MethodCallExpr):
        pass # TODO

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        pass # TODO

    def IntegerLiteral(self, node: IntegerLiteral):
        pass # TODO

    def NoneLiteral(self, node: NoneLiteral):
        pass # TODO

    def StringLiteral(self, node: StringLiteral):
        pass # TODO

    # TYPES

    def TypedVar(self, node: TypedVar):
        pass # TODO

    def ListType(self, node: ListType):
        pass # TODO

    def ClassType(self, node: ClassType):
        pass # TODO
