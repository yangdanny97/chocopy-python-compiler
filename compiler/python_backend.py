from .astnodes import *
from .types import *
from .builder import Builder
from .visitor import Visitor
import json


class PythonBackend(Visitor):
    def __init__(self):
        self.builder = Builder("")

    def visit(self, node: Node):
        return node.visit(self)

    def addText(self, text: str):
        self.builder.addText(text)

    # TOP LEVEL & DECLARATIONS

    def Program(self, node: Program):
        for d in node.declarations:
            self.visit(d)
        for s in node.statements:
            self.visit(s)

    def VarDef(self, node: VarDef):
        self.builder.newLine()
        self.visit(node.var)
        self.addText(" = ")
        if node.var.varInstance is None:
            self.visit(node.value)
        elif not node.isAttr and node.var.varInstance.isNonlocal:
            self.addText("[")
            self.visit(node.value)
            self.addText("]")
        else:
            self.visit(node.value)

    def ClassDef(self, node: ClassDef):
        self.builder.newLine("class ")
        self.visit(node.name)
        self.addText("(")
        self.visit(node.superclass)
        self.addText("):")
        self.builder.indent()
        for d in node.declarations:
            self.visit(d)
        self.builder.unindent()
        self.builder.newLine()

    def FuncDef(self, node: FuncDef):
        self.builder.newLine("def ")
        self.visit(node.name)
        self.addText("(")
        for i in range(len(node.params)):
            self.visit(node.params[i])
            if i != len(node.params) - 1:
                self.addText(", ")
        self.addText("):")
        self.builder.indent()
        # hack to wrap self if it's needed for nonlocal
        selfVarInstance = node.params[0].varInstance if node.isMethod else None
        if selfVarInstance is not None and selfVarInstance.isNonlocal:
            self.builder.newLine("self = [self]")
        for d in node.declarations:
            self.visit(d)
        for s in node.statements:
            self.visit(s)
        if len(node.declarations) == 0 and len(node.statements) == 0:
            self.addText("pass")
        self.builder.unindent()
        self.builder.newLine()

    # STATEMENTS

    def NonLocalDecl(self, node: NonLocalDecl):
        self.builder.newLine("nonlocal ")
        self.visit(node.variable)

    def GlobalDecl(self, node: GlobalDecl):
        self.builder.newLine("global ")
        self.visit(node.variable)

    def AssignStmt(self, node: AssignStmt):
        if len(node.targets) == 1:
            self.builder.newLine()
            self.visit(node.targets[0])
            self.addText(" = ")
            self.visit(node.value)
        else:
            self.builder.newLine("__x = ")
            self.visit(node.value)
            for t in node.targets:
                self.builder.newLine()
                self.visit(t)
                self.addText(" = __x")

    def IfStmt(self, node: IfStmt):
        self.builder.newLine("if ")
        self.visit(node.condition)
        self.addText(":")
        self.builder.indent()
        for s in node.thenBody:
            self.visit(s)
        if len(node.thenBody) == 0:
            self.addText("pass")
        self.builder.unindent()
        self.builder.newLine("else:")
        self.builder.indent()
        for s in node.elseBody:
            self.visit(s)
        if len(node.elseBody) == 0:
            self.addText("pass")
        self.builder.unindent()

    def ExprStmt(self, node: ExprStmt):
        self.builder.newLine()
        self.visit(node.expr)

    def BinaryExpr(self, node: BinaryExpr):
        self.addText("(")
        self.visit(node.left)
        self.addText(" " + node.operator + " ")
        self.visit(node.right)
        self.addText(")")

    def IndexExpr(self, node: IndexExpr):
        self.visit(node.list)
        self.addText("[")
        self.visit(node.index)
        self.addText("]")

    def UnaryExpr(self, node: UnaryExpr):
        self.addText("(")
        self.addText(node.operator + " ")
        self.visit(node.operand)
        self.addText(")")

    def visitArg(self, node, funcType, paramIdx: int, argIdx: int):
        arg = node.args[argIdx]
        if isinstance(arg, Identifier) and arg.varInstance is None:
            self.visit(arg)
            return
        argIsRef = isinstance(
            arg, Identifier) and arg.varInstance is not None and arg.varInstance.isNonlocal
        paramIsRef = paramIdx in funcType.refParams
        if argIsRef and paramIsRef and arg.varInstance == funcType.refParams[paramIdx]:
            # ref arg and ref param, pass ref arg
            self.addText(arg.name)
        elif paramIsRef:
            # non-ref arg and ref param, or do not pass ref arg
            self.addText("[")
            self.visit(arg)
            self.addText("]")
        else:  # non-ref param, maybe unwrap
            self.visit(arg)

    def CallExpr(self, node: CallExpr):
        # special case for builtins - always unwrap
        if node.function.name == "__assert__":
            self.addText("assert ")
            self.visit(node.args[0])
            return
        elif node.function.name in {"print", "len"}:
            self.visit(node.function)
            self.addText("(")
            self.visit(node.args[0])
            self.addText(")")
            return
        self.visit(node.function)
        self.addText("(")
        for i in range(len(node.args)):
            if node.isConstructor:
                self.visitArg(node, node.function.inferredType, i + 1, i)
            else:
                self.visitArg(node, node.function.inferredType, i, i)
            if i != len(node.args) - 1:
                self.addText(", ")
        self.addText(")")

    def ForStmt(self, node: ForStmt):
        self.builder.newLine("for ")
        self.visit(node.identifier)
        self.addText(" in ")
        self.visit(node.iterable)
        self.addText(":")
        self.builder.indent()
        for b in node.body:
            self.visit(b)
        if len(node.body) == 0:
            self.addText("pass")
        self.builder.unindent()

    def ListExpr(self, node: ListExpr):
        self.addText("[")
        for i in range(len(node.elements)):
            self.visit(node.elements[i])
            if i != len(node.elements) - 1:
                self.addText(", ")
        self.addText("]")

    def WhileStmt(self, node: WhileStmt):
        self.builder.newLine("while ")
        self.visit(node.condition)
        self.addText(":")
        self.builder.indent()
        for b in node.body:
            self.visit(b)
        if len(node.body) == 0:
            self.addText("pass")
        self.builder.unindent()

    def ReturnStmt(self, node: ReturnStmt):
        self.builder.newLine("return ")
        if node.value is not None:
            self.visit(node.value)

    def Identifier(self, node: Identifier):
        if node.varInstance is None:
            self.addText(node.name)
        elif node.varInstance.isNonlocal:
            self.addText(node.name + "[0]")
        else:
            self.addText(node.name)

    def MemberExpr(self, node: MemberExpr):
        self.visit(node.object)
        self.addText(".")
        self.visit(node.member)

    def IfExpr(self, node: IfExpr):
        self.addText("(")
        self.visit(node.thenExpr)
        self.addText(" if ")
        self.visit(node.condition)
        self.addText(" else ")
        self.visit(node.elseExpr)
        self.addText(")")

    def MethodCallExpr(self, node: MethodCallExpr):
        self.visit(node.method)
        self.addText("(")
        for i in range(len(node.args)):
            self.visitArg(node, node.method.inferredType, i + 1, i)
            if i != len(node.args) - 1:
                self.addText(", ")
        self.addText(")")

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        self.addText(str(node.value))

    def IntegerLiteral(self, node: IntegerLiteral):
        self.addText(str(node.value))

    def NoneLiteral(self, node: NoneLiteral):
        self.addText(str(node.value))

    def StringLiteral(self, node: StringLiteral):
        self.addText(json.dumps(node.value))

    # TYPES

    def TypedVar(self, node: TypedVar):
        self.addText(node.identifier.name)

    def ListType(self, node: ListType):
        pass

    def ClassType(self, node: ClassType):
        self.addText(node.className)
