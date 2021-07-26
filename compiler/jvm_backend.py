from .astnodes import *
from .types import *
from .builder import Builder
from .visitor import Visitor
from collections import defaultdict
import json

class JvmBackend(Visitor):
    # record all free vars from nested functions

    def __init__(self, main: str):
        self.builder = Builder()
        self.main = main # name of main class
        self.locals = [defaultdict(lambda: None)]
    
    def visit(self, node: Node):
        if isinstance(node, Expr):
            node.visitChildrenForTypecheck(self)
        node.visit(self)

    def enterScope(self):
        self.locals.append(defaultdict(lambda: None))

    def exitScope(self):
        self.locals.pop()

    def exprTypeIsRef(self, expr: Expr)->bool:
        t = expr.inferredType
        if isinstance(t, ClassValueType):
            return t.className not in {"int", "bool"}
        return False

    def store(self, name):
        n, isRef = self.locals[-1][name]
        if isRef:
            self.builder.newLine("astore {}".format(n))
        else:
            self.builder.newLine("istore {}".format(n))

    def load(self, name):
        n, isRef = self.locals[-1][name]
        if isRef:
            self.builder.newLine("aload {}".format(n))
        else:
            self.builder.newLine("iload {}".format(n))

    def newLocal(self, name:str=None, isRef:bool=True)->int:
        # store the top of stack as a new local
        n = len(self.locals[-1])
        if isRef:
            self.builder.newLine("astore {}".format(n))
        else:
            self.builder.newLine("istore {}".format(n))
        if name is None:
            name = "__local__{}".format(n)
        self.locals[-1][name] = (n, isRef)
        return n

    def emit_input(self):
        self.builder.newLine("new java/util/Scanner")
        self.builder.newLine("dup")
        self.builder.newLine("getstatic Field java/lang/System in Ljava/io/InputStream;")
        self.builder.newLine("invokespecial Method java/util/Scanner <init> (Ljava/io/InputStream;)V") 
        l = self.newLocal()
        self.builder.newLine("aload {}".format(l))
        self.builder.addLine("invokevirtual Method java/util/Scanner nextLine ()Ljava/lang/String;")

    def emit_len(self):
        pass # TODO

    def emit_print(self, arg:Expr):
        t = ""
        if arg.inferredType.classname == "int":
            t = "I"
        elif arg.inferredType.classname == "str":
            t = "Ljava/lang/String;"
        elif arg.inferredType.classname == "bool":
            t = "Z"
        else:
            # TODO - runtime abort
            raise Exception("Printing is unsupported for values of type "+arg.inferredType.classname)
        self.builder.newLine("getstatic Field java/lang/System out Ljava/io/PrintStream;")
        self.builder.newLine("invokevirtual Method java/io/PrintStream println ({})V".format(t))

    def Program(self, node: Program):
        self.builder.newLine(".version 49 0")
        self.builder.newLine(".class super {}".format(self.main))
        self.builder.newLine(".super java/lang/Object")
        self.builder.newLine(".method public static main : ([Ljava/lang/String;)V")
        self.builder.indent()
        # TODO
        self.builder.newLine("return")
        self.builder.unindent()
        self.builder.newLine(".end method")
        self.builder.newLine(".end class")

    def ClassDef(self, node: ClassDef):
        pass

    def FuncDef(self, node: FuncDef):
        pass

    def VarDef(self, node: VarDef):
        if self.isAttr:
            pass # TODO
        else:
            self.visit(node.value)
            self.newLocal(node.var, self.exprTypeIsRef(node.value))

    # STATEMENTS

    def NonLocalDecl(self, node: NonLocalDecl):
        pass

    def GlobalDecl(self, node: GlobalDecl):
        pass

    def processAssignmentTarget(target:Expr):
        pass # TODO

    def AssignStmt(self, node: AssignStmt):
        self.visit(node.value)
        targets = node.targets[::-1]
        if len(targets) > 1:
            self.builder.newLine("dup")
            for t in targets:
                self.processAssignmentTarget(t)
        else:
            self.processAssignmentTarget(targets[0])

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
        self.load(node.name)

    def MemberExpr(self, node: MemberExpr):
        pass

    def IfExpr(self, node: IfExpr):
        pass

    def MethodCallExpr(self, node: MethodCallExpr):
        pass

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        if node.value:
            self.builder.newLine("iconst_1")
        else:
            self.builder.newLine("iconst_0")

    def IntegerLiteral(self, node: IntegerLiteral):
        self.builder.newLine("ldc {}".format(node.value))

    def NoneLiteral(self, node: NoneLiteral):
        self.builder.newLine("aconst_null")

    def StringLiteral(self, node: StringLiteral):
        self.builder.newLine("ldc "+json.dumps(node.value))

    # TYPES

    def TypedVar(self, node: TypedVar):
        pass

    def ListType(self, node: ListType):
        pass

    def ClassType(self, node: ClassType):
        pass

