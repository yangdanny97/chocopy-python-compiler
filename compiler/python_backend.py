from .astnodes import *
from .types import *
from .builder import Builder
from .visitor import Visitor
import json

class PythonBackend(Visitor):
    def __init__(self):
        self.builder = Builder(None)

    def visit(self, node: Node):
        return node.visit(self)

    # TOP LEVEL & DECLARATIONS

    def Program(self, node: Program):
        for d in node.declarations:
            self.visit(d)
        for s in node.statements:
            self.visit(s)

    def VarDef(self, node: VarDef):
        self.builder.newLine()
        self.visit(node.var)
        self.builder.addText(" = ")
        if node.var.capturedNonlocal:
            self.builder.addText("[")
            self.visit(node.value)
            self.builder.addText("]")
        else:
            self.visit(node.value)

    def ClassDef(self, node: ClassDef):
        self.builder.newLine("class ")
        self.visit(node.name)
        self.builder.addText("(")
        self.visit(node.superclass)
        self.builder.addText("):")
        self.builder.indent()
        for d in node.declarations:
            self.visit(d)
        self.builder.unindent()
        self.builder.newLine()

    def FuncDef(self, node: FuncDef):
        self.builder.newLine("def ")
        self.visit(node.name)
        self.builder.addText("(")
        for i in range(len(node.params)):
            self.visit(node.params[i])
            if i != len(node.params) - 1:
                self.builder.addText(", ")
        self.builder.addText("):")
        self.builder.indent()
        for d in node.declarations:
            self.visit(d)
        for s in node.statements:
            self.visit(s)
        if len(node.declarations) == 0 and len(node.statements) == 0:
            self.builder.addText("pass")
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
        self.builder.newLine("__x = ")
        self.visit(node.value)
        for t in node.targets:
            self.builder.newLine()
            self.visit(t)
            self.builder.addText(" = __x")

    def IfStmt(self, node: IfStmt):
        self.builder.newLine("if ")
        self.visit(node.condition)
        self.builder.addText(":")
        self.builder.indent()
        for s in node.thenBody:
            self.visit(s)
        if len(node.thenBody) == 0:
            self.builder.addText("pass")
        self.builder.unindent()
        self.builder.newLine("else:")
        self.builder.indent()
        for s in node.elseBody:
            self.visit(s)
        if len(node.elseBody) == 0:
            self.builder.addText("pass")
        self.builder.unindent()

    def ExprStmt(self, node: ExprStmt):
        self.builder.newLine()
        self.visit(node.expr)

    def BinaryExpr(self, node: BinaryExpr):
        self.builder.addText("(")
        self.visit(node.left)
        self.builder.addText(" " + node.operator + " ")
        self.visit(node.right)
        self.builder.addText(")")

    def IndexExpr(self, node: IndexExpr):
        self.visit(node.list)
        self.builder.addText("[")
        self.visit(node.index)
        self.builder.addText("]")

    def UnaryExpr(self, node: UnaryExpr):
        self.builder.addText("(")
        self.builder.addText(node.operator + " ")
        self.visit(node.operand)
        self.builder.addText(")")

    def argIsRef(self, node:Expr, idx:int)->bool:
        if node.isConstructor:
            return node.function.inferredType.parameters[idx+1].isRef
        else:
            return node.function.inferredType.parameters[idx].isRef

    def CallExpr(self, node: CallExpr):
        # TODO: wrap arg refs
        # special case for assertions
        if node.function.name == "__assert__":
            self.builder.addText("assert ")
            self.visit(node.args[0])
            return
        self.visit(node.function)
        self.builder.addText("(")
        for i in range(len(node.args)):
            isRef = False # self.argIsRef(node, i)
            if isRef:
                node.builder.addText("[")
            self.visit(node.args[i])
            if isRef:
                self.builder.addText("]")
            if i != len(node.args) - 1:
                self.builder.addText(", ")
        self.builder.addText(")")

    def ForStmt(self, node: ForStmt):
        self.builder.newLine("for ")
        self.visit(node.identifier)
        self.builder.addText(" in ")
        self.visit(node.iterable)
        self.builder.addText(":")
        self.builder.indent()
        for b in node.body:
            self.visit(b)
        if len(node.body) == 0:
            self.builder.addText("pass")
        self.builder.unindent()

    def ListExpr(self, node: ListExpr):
        self.builder.addText("[")
        for i in range(len(node.elements)):
            self.visit(node.elements[i])
            if i != len(node.elements) - 1:
                self.builder.addText(", ")
        self.builder.addText("]")

    def WhileStmt(self, node: WhileStmt):
        self.builder.newLine("while ")
        self.visit(node.condition)
        self.builder.addText(":")
        self.builder.indent()
        for b in node.body:
            self.visit(b)
        if len(node.body) == 0:
            self.builder.addText("pass")
        self.builder.unindent()

    def ReturnStmt(self, node: ReturnStmt):
        self.builder.newLine("return ")
        if node.value is not None:
            self.visit(node.value)

    def Identifier(self, node: Identifier):
        if node.isRef:
            self.builder.addText(node.name + "[0]")
        else:
            self.builder.addText(node.name)

    def MemberExpr(self, node: MemberExpr):
        self.visit(node.object)
        self.builder.addText(".")
        self.visit(node.member)

    def IfExpr(self, node: IfExpr):
        self.builder.addText("(")
        self.visit(node.thenExpr)
        self.builder.addText(" if ")
        self.visit(node.condition)
        self.builder.addText(" else ")
        self.visit(node.elseExpr)
        self.builder.addText(")")

    def MethodCallExpr(self, node: MethodCallExpr):
        # TODO wrap arg refs
        self.visit(node.method)
        self.builder.addText("(")
        for i in range(len(node.args)):
            self.visit(node.args[i])
            if i != len(node.args) - 1:
                self.builder.addText(", ")
        self.builder.addText(")")

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        self.builder.addText(str(node.value))

    def IntegerLiteral(self, node: IntegerLiteral):
        self.builder.addText(str(node.value))

    def NoneLiteral(self, node: NoneLiteral):
        self.builder.addText(str(node.value))

    def StringLiteral(self, node: StringLiteral):
        self.builder.addText(json.dumps(node.value))

    # TYPES

    def TypedVar(self, node: TypedVar):
        self.visit(node.identifier)

    def ListType(self, node: ListType):
        pass

    def ClassType(self, node: ClassType):
        self.builder.addText(node.className)
