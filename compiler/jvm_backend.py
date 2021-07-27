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
        node.visit(self)

    def enterScope(self):
        self.locals.append(defaultdict(lambda: None))

    def exitScope(self):
        self.locals.pop()

    def typeIsRef(self, t: ValueType)->bool:
        if isinstance(t, ClassValueType):
            return t.className not in {"int", "bool"}
        return False

    def returnInstr(self, exprType: ValueType):
        if self.typeIsRef(exprType):
            self.builder.newLine("areturn")
        else:
            self.builder.newLine("ireturn")

    def store(self, name:str, t:ValueType):
        # TODO arrays
        n = self.locals[-1][name]
        if n is None:
            raise Exception("unexpected")
        if self.typeIsRef(t):
            self.builder.newLine("astore {}".format(n))
        else:
            self.builder.newLine("istore {}".format(n))

    def load(self, name:str, t:ValueType):
        # TODO arrays
        n = self.locals[-1][name]
        if n is None:
            raise Exception("unexpected")
        if self.typeIsRef(t):
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
        self.locals[-1][name] = n
        return n

    def emit_input(self):
        self.builder.newLine("new java/util/Scanner")
        self.builder.newLine("dup")
        self.builder.newLine("getstatic Field java/lang/System in Ljava/io/InputStream;")
        self.builder.newLine("invokespecial Method java/util/Scanner <init> (Ljava/io/InputStream;)V") 
        l = self.newLocal()
        self.builder.newLine("aload {}".format(l))
        self.builder.addLine("invokevirtual Method java/util/Scanner nextLine ()Ljava/lang/String;")

    def emit_len(self, arg:Expr):
        t = arg.inferredType
        is_list = False
        if isinstance(t, ListValueType):
            is_list = True
        else:
            if t.className == "<None>":
                pass
            elif t.className == "<Empty>":
                is_list = True
            elif t.className == "str":
                pass
            else:
                # TODO - runtime abort
                raise Exception("Built-in function len is unsupported for values of type "+arg.inferredType.classname)
        if is_list:
            pass # TODO
        else:
            pass

    def emit_print(self, arg:Expr):
        if isinstance(arg.inferredType, ListValueType):
            raise Exception("Built-in function print is unsupported for lists")
        t = arg.inferredType.getJavaSignature()
        self.builder.newLine("getstatic Field java/lang/System out Ljava/io/PrintStream;")
        self.visit(arg)
        self.builder.newLine("invokevirtual Method java/io/PrintStream println ({})V".format(t))

    def Program(self, node: Program):
        self.builder.newLine(".version 49 0")
        self.builder.newLine(".class public super {}".format(self.main))
        self.builder.newLine(".super java/lang/Object")
        self.builder.newLine(".method public static main : ([Ljava/lang/String;)V")
        self.builder.indent()
        self.builder.newLine(".limit stack 100") # TODO
        self.builder.newLine(".limit locals {}".format(len(node.declarations) + 100))
        for d in node.declarations:
            self.visit(d)
        for s in node.statements:
            self.visit(s)
        self.builder.newLine("return")
        self.builder.unindent()
        self.builder.newLine(".end method")
        self.builder.newLine(".end class")

    def ClassDef(self, node: ClassDef):
        pass # TODO

    def FuncDef(self, node: FuncDef):
        self.enterScope()
        # TODO
        self.exitScope()

    def VarDef(self, node: VarDef):
        if node.isAttr:
            pass # TODO field defs
        else:
            self.visit(node.value)
            self.newLocal(node.var.identifier.name, self.typeIsRef(node.value.inferredType))

    # STATEMENTS

    def NonLocalDecl(self, node: NonLocalDecl):
        pass

    def GlobalDecl(self, node: GlobalDecl):
        pass

    def processAssignmentTarget(self, target:Expr):
        if isinstance(target, Identifier):
            self.store(target.name, target.inferredType)
        elif isinstance(target, IndexExpr):
            pass # TODO
        elif isinstance(target, MemberExpr):
            pass # TODO
        else:
            raise Exception("unsupported")

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
        self.visit(node.expr)

    def BinaryExpr(self, node: BinaryExpr):
        pass

    def IndexExpr(self, node: IndexExpr):
        pass

    def UnaryExpr(self, node: UnaryExpr):
        pass

    def CallExpr(self, node: CallExpr):
        signature = node.function.inferredType.getJavaSignature()
        name = node.function.name
        if name == "print":
            self.emit_print(node.args[0])
        elif name == "len":
            self.emit_len(node.args[0])
        elif name == "input":
            self.emit_input()
        else:
            for arg in node.args:
                self.visit(arg)
            self.builder.newLine("invokestatic Method {} {} {};".format(self.main, name, signature))

    def ForStmt(self, node: ForStmt):
        pass

    def ListExpr(self, node: ListExpr):
        pass

    def WhileStmt(self, node: WhileStmt):
        pass

    def ReturnStmt(self, node: ReturnStmt):
        if node.expType.isNone():
            pass # TODO handle void
        else:
            if node.value is None:
                self.NoneLiteral(None)
            else:
                self.visit(node.value)
            self.returnInstr(node.expType)

    def Identifier(self, node: Identifier):
        self.load(node.name, node.inferredType)

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

    def emit(self)->str:
        return self.builder.emit()
