from .astnodes import *

class Translator:

    def visit(self, node: Node):
        return node.visit(self)

    # TOP LEVEL & DECLARATIONS

    def Program(self, node: Program):
        raise NotImplementedError

    def VarDef(self, node: VarDef):
        raise NotImplementedError

    def ClassDef(self, node: ClassDef):
        raise NotImplementedError

    def FuncDef(self, node: FuncDef):
        raise NotImplementedError

    # STATEMENTS

    def NonLocalDecl(self, node: NonLocalDecl):
        raise NotImplementedError

    def GlobalDecl(self, node: GlobalDecl):
        raise NotImplementedError

    def AssignStmt(self, node: AssignStmt):
        raise NotImplementedError

    def IfStmt(self, node: IfStmt):
        raise NotImplementedError

    def ExprStmt(self, node: ExprStmt):
        raise NotImplementedError

    def BinaryExpr(self, node: BinaryExpr):
        raise NotImplementedError

    def IndexExpr(self, node: IndexExpr):
        raise NotImplementedError

    def UnaryExpr(self, node: UnaryExpr):
        raise NotImplementedError

    def CallExpr(self, node: CallExpr):
        raise NotImplementedError

    def ForStmt(self, node: ForStmt):
        raise NotImplementedError

    def ListExpr(self, node: ListExpr):
        raise NotImplementedError

    def WhileStmt(self, node: WhileStmt):
        raise NotImplementedError

    def ReturnStmt(self, node: ReturnStmt):
        raise NotImplementedError

    def Identifier(self, node: Identifier):
        raise NotImplementedError

    def MemberExpr(self, node: MemberExpr):
        raise NotImplementedError

    def IfExpr(self, node: IfExpr):
        raise NotImplementedError

    def MethodCallExpr(self, node: MethodCallExpr):
        raise NotImplementedError

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        raise NotImplementedError

    def IntegerLiteral(self, node: IntegerLiteral):
        raise NotImplementedError

    def NoneLiteral(self, node: NoneLiteral):
        raise NotImplementedError

    def StringLiteral(self, node: StringLiteral):
        raise NotImplementedError

    # TYPES

    def TypedVar(self, node: TypedVar):
        raise NotImplementedError

    def ListType(self, node: ListType):
        raise NotImplementedError

    def ClassType(self, node: ClassType):
        raise NotImplementedError
