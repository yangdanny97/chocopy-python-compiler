class Translator:

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
