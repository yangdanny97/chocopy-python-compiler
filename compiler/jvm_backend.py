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
        self.counter = 0 # for labels
        self.returnType = None

    def visit(self, node: Node):
        node.visit(self)

    def instr(self, instr:str):
        self.builder.newLine(instr)

    def newLabelName(self)->str:
        self.counter += 1
        return "L"+str(self.counter)

    def label(self, name:str)->str:
        self.builder.unindent()
        self.builder.newLine(name+":")
        self.builder.indent()

    def enterScope(self):
        self.locals.append(defaultdict(lambda: None))

    def exitScope(self):
        self.locals.pop()

    def returnInstr(self, exprType: ValueType):
        if exprType.isJavaRef():
            self.instr("areturn")
        else:
            self.instr("ireturn")

    def store(self, name:str, t:ValueType):
        # TODO arrays
        n = self.locals[-1][name]
        if n is None:
            raise Exception("unexpected")
        if t.isJavaRef():
            self.instr("astore {}".format(n))
        else:
            self.instr("istore {}".format(n))

    def load(self, name:str, t:ValueType):
        # TODO arrays
        n = self.locals[-1][name]
        if n is None:
            raise Exception("unexpected")
        if t.isJavaRef():
            self.instr("aload {}".format(n))
        else:
            self.instr("iload {}".format(n))

    def newLocalEntry(self, name:str)->int:
        # add a new entry to locals
        n = len(self.locals[-1])
        self.locals[-1][name] = n
        return n

    def newLocal(self, name:str=None, isRef:bool=True)->int:
        # store the top of stack as a new local
        n = len(self.locals[-1])
        if isRef:
            self.instr("astore {}".format(n))
        else:
            self.instr("istore {}".format(n))
        if name is None:
            name = "__local__{}".format(n)
        self.locals[-1][name] = n
        return n

    def Program(self, node: Program):
        func_decls = [d for d in node.declarations if isinstance(d, FuncDef)]
        cls_decls = [d for d in node.declarations if isinstance(d, ClassDef)]
        var_decls = [d for d in node.declarations if isinstance(d, VarDef)]

        self.instr(".version 49 0")
        self.instr(".class public super {}".format(self.main))
        self.instr(".super java/lang/Object")
        self.instr(".method public static main : ([Ljava/lang/String;)V")
        self.builder.indent()
        self.instr(".limit stack 100") # TODO
        self.instr(".limit locals {}".format(len(node.declarations) + 100))
        for d in var_decls:
            self.visit(d)
        for s in node.statements:
            self.visit(s)
        self.instr("return")
        self.builder.unindent()
        self.instr(".end method")
        for d in func_decls:
            self.visit(d)
        self.instr(".end class")
        for d in cls_decls:
            self.visit(d)

    def ClassDef(self, node: ClassDef):
        pass # TODO

    def FuncDef(self, node: FuncDef):
        self.enterScope()
        self.instr(".method public static {} : {}".format(node.name.name, node.type.getJavaSignature()))
        self.builder.indent()
        self.instr(".limit stack 100") # TODO
        self.instr(".limit locals {}".format(len(node.declarations) + 100))
        for i in range(len(node.params)):
            self.newLocalEntry(node.params[i].identifier.name)
        for d in node.declarations:
            # TODO build nested funcs (probably by hoisting)
            self.visit(d)
        self.returnType = node.type.returnType
        # handle last return
        hasReturn = False
        for s in node.statements:
            self.visit(s)
            if s.isReturn:
                hasReturn = True
        if not hasReturn:
            self.buildReturn(None)
        self.exitScope()
        self.builder.unindent()
        self.instr(".end method")

    def VarDef(self, node: VarDef):
        if node.isAttr:
            pass # TODO field defs
        else:
            self.visit(node.value)
            self.newLocal(node.var.identifier.name, node.value.inferredType.isJavaRef())

    # STATEMENTS

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
            self.instr("dup")
            for t in targets:
                self.processAssignmentTarget(t)
        else:
            self.processAssignmentTarget(targets[0])

    def IfStmt(self, node: IfStmt):
        pass

    def ExprStmt(self, node: ExprStmt):
        self.visit(node.expr)

    def comparator(self, instr:str, firstBranchTrue:bool=False):
        l1 = self.newLabelName()
        l2 = self.newLabelName()
        self.instr("{} {}".format(instr, l1))
        if firstBranchTrue:
            self.instr("iconst_1")
        else:
            self.instr("iconst_0")
        self.instr("goto {}".format(l2))
        self.label(l1)
        if firstBranchTrue:
            self.instr("iconst_0")
        else:
            self.instr("iconst_1") 
        self.label(l2)

    def BinaryExpr(self, node: BinaryExpr):
        operator = node.operator
        leftType = node.left.inferredType
        rightType = node.right.inferredType
        self.visit(node.left)
        self.visit(node.right)

        # concatenation and addition
        if operator == "+":
            if isinstance(leftType, ListValueType) and isinstance(rightType, ListValueType):
                pass
            elif leftType.className == "str":
                pass
            elif leftType.className == "int":
                self.instr("iadd")
            else:
                raise Exception("unexpected")
        # other arithmetic operators
        elif operator == "-":
            self.instr("isub")
        elif operator == "*":
            self.instr("imul")
        elif operator == "//":
            self.instr("invokestatic Method java/lang/Math floorDiv (II)I")
        elif operator == "%":
            self.instr("irem")
        # relational operators
        elif operator == "<":
            self.comparator("if_icmplt")
        elif operator == "<=":
            self.comparator("if_icmple")
        elif operator == ">":
            self.comparator("if_icmpgt")
        elif operator == ">=":
            self.comparator("if_icmpge")
        elif operator == "==":
            if leftType.isJavaRef():
                self.instr("invokevirtual Method java/lang/String equals (Ljava/lang/Object;)Z")
            else:
                self.comparator("if_icmpeq")
        elif operator == "!=":
            if leftType.isJavaRef():
                self.instr("invokevirtual Method java/lang/String equals (Ljava/lang/Object;)Z")
                self.comparator("ifne", True)
            else:
                self.comparator("if_icmpne")
        elif operator == "is":
            self.comparator("if_acmpeq")
        # logical operators
        elif operator == "and":
            self.instr("iand")
        elif operator == "or":
            self.instr("ior")
        else:
            raise Exception("unexpected")

    def IndexExpr(self, node: IndexExpr):
        pass

    def UnaryExpr(self, node: UnaryExpr):
        self.visit(node.operand)
        if node.operator == "-":
            self.instr("ineg")
        elif node.operator == "not":
            self.comparator("ifne", True)

    def buildConstructor(self, node: CallExpr):
        className = node.function.name
        self.builder.newLine("new {}".format(className))
        self.builder.newLine("dup")
        self.builder.newLine("invokespecial Method {} <init> ()V".format(className))

    def CallExpr(self, node: CallExpr):
        signature = node.function.inferredType.getJavaSignature()
        name = node.function.name
        if node.isConstructor:
            self.buildConstructor(node)
            return
        # TODO build shadowing
        if name == "print":
            self.emit_print(node.args[0])
        elif name == "len":
            self.emit_len(node.args[0])
        elif name == "input":
            self.emit_input()
        elif name == "__assert__":
            self.emit_assert(node.args[0])
        else:
            for arg in node.args:
                self.visit(arg)
            self.instr("invokestatic Method {} {} {}".format(self.main, name, signature))
            if node.function.inferredType.returnType.isNone():
                self.NoneLiteral(None) # push null for void return

    def ForStmt(self, node: ForStmt):
        pass

    def ListExpr(self, node: ListExpr):
        pass

    def WhileStmt(self, node: WhileStmt):
        pass

    def buildReturn(self, value:Expr):
        if self.returnType.isNone():
            self.builder.newLine("return")
        else:
            if value is None:
                self.NoneLiteral(None)
            else:
                self.visit(value)
            self.returnInstr(self.returnType)

    def ReturnStmt(self, node: ReturnStmt):
        self.buildReturn(node.value)

    def Identifier(self, node: Identifier):
        self.load(node.name, node.inferredType)

    def MemberExpr(self, node: MemberExpr):
        pass

    def IfExpr(self, node: IfExpr):
        self.visit(node.condition)
        l1 = self.newLabelName()
        l2 = self.newLabelName()
        self.instr("{} {}".format("ifne", l1))
        self.visit(node.elseExpr)
        self.instr("goto {}".format(l2))
        self.label(l1)
        self.visit(node.thenExpr)
        self.label(l2)

    def MethodCallExpr(self, node: MethodCallExpr):
        # TODO special case for init
        pass

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        if node.value:
            self.instr("iconst_1")
        else:
            self.instr("iconst_0")

    def IntegerLiteral(self, node: IntegerLiteral):
        self.instr("ldc {}".format(node.value))

    def NoneLiteral(self, node: NoneLiteral):
        self.instr("aconst_null")

    def StringLiteral(self, node: StringLiteral):
        self.instr("ldc "+json.dumps(node.value))

    # TYPES

    def TypedVar(self, node: TypedVar):
        pass

    def ListType(self, node: ListType):
        pass

    def ClassType(self, node: ClassType):
        pass

    def emit(self)->str:
        return self.builder.emit()

    # SUGAR

    def NonLocalDecl(self, node: NonLocalDecl):
        pass

    def GlobalDecl(self, node: GlobalDecl):
        pass

    # BUILT-INS
    def emit_assert(self, arg:Expr):
        label = self.newLabelName()
        self.visit(arg)
        self.instr("ifne {}".format(label))
        msg = "failed assertion on line {}".format(arg.location[0])
        self.instr("new java/lang/Exception")
        self.instr("dup")
        self.instr("ldc {}".format(json.dumps(msg)))
        self.instr("invokespecial Method java/lang/Exception <init> (Ljava/lang/String;)V")
        self.instr("athrow")
        self.label(label)

    def emit_input(self):
        self.instr("new java/util/Scanner")
        self.instr("dup")
        self.instr("getstatic Field java/lang/System in Ljava/io/InputStream;")
        self.instr("invokespecial Method java/util/Scanner <init> (Ljava/io/InputStream;)V") 
        l = self.newLocal()
        self.instr("aload {}".format(l))
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
        self.instr("getstatic Field java/lang/System out Ljava/io/PrintStream;")
        self.visit(arg)
        self.instr("invokevirtual Method java/io/PrintStream println ({})V".format(t))
        self.NoneLiteral(None) # push None for void return
