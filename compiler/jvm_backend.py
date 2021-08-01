from .astnodes import *
from .types import *
from .builder import Builder
from .typesystem import TypeSystem
from .visitor import Visitor
from collections import defaultdict
import json


class JvmBackend(Visitor):
    # record all free vars from nested functions

    def __init__(self, main: str, ts: TypeSystem):
        self.classes = dict()
        self.classes[main] = Builder(main)
        self.currentClass = main
        self.main = main  # name of main class
        self.locals = [defaultdict(lambda: None)]
        self.counter = 0  # for labels
        self.returnType = None
        self.stackLimit = 50
        self.localLimit = 50
        self.ts = ts
        self.defaultToGlobals = False # treat all vars as global if this is true

    def currentBuilder(self):
        return self.classes[self.currentClass]

    def visit(self, node: Node):
        node.visit(self)

    def instr(self, instr: str):
        self.currentBuilder().newLine(instr)

    def newLabelName(self) -> str:
        self.counter += 1
        return "L"+str(self.counter)

    def label(self, name: str) -> str:
        self.currentBuilder().unindent()
        self.instr(name+":")
        self.currentBuilder().indent()

    def enterScope(self):
        self.locals.append(defaultdict(lambda: None))

    def exitScope(self):
        self.locals.pop()

    def returnInstr(self, exprType: ValueType):
        if exprType.isJavaRef():
            self.instr("areturn")
        else:
            self.instr("ireturn")

    def store(self, name: str, t: ValueType):
        n = self.locals[-1][name]
        if n is None:
            raise Exception(
                f"Internal compiler error: unknown name {name} for store")
        if t.isJavaRef():
            self.instr(f"astore {n}")
        else:
            self.instr(f"istore {n}")

    def load(self, name: str, t: ValueType):
        n = self.locals[-1][name]
        if n is None:
            raise Exception(
                f"Internal compiler error: unknown name {name} for load")
        if t.isJavaRef():
            self.instr(f"aload {n}")
        else:
            self.instr(f"iload {n}")

    def arrayStore(self, t: ValueType):
        # expect the stack to be array, idx, value
        if t.isJavaRef():
            self.instr("aastore")
        else:
            self.instr("iastore")

    def arrayLoad(self, t: ValueType):
        # expect the stack to be array, idx
        if t.isJavaRef():
            self.instr("aaload")
        else:
            self.instr("iaload")

    def newLocalEntry(self, name: str) -> int:
        # add a new entry to locals table w/o storing anything
        n = len(self.locals[-1])
        self.locals[-1][name] = n
        return n

    def genLocalName(self, offset: int) -> str:
        return f"__local__{offset}"

    def newLocal(self, name: str = None, isRef: bool = True) -> int:
        # store the top of stack as a new local
        n = len(self.locals[-1])
        if isRef:
            self.instr(f"astore {n}")
        else:
            self.instr(f"istore {n}")
        if name is None:
            name = self.genLocalName(n)
        self.locals[-1][name] = n
        return n

    def Program(self, node: Program):
        func_decls = [d for d in node.declarations if isinstance(d, FuncDef)]
        cls_decls = [d for d in node.declarations if isinstance(d, ClassDef)]
        var_decls = [d for d in node.declarations if isinstance(d, VarDef)]

        self.instr(".version 49 0")
        self.instr(f".class public super {self.main}")
        self.instr(".super java/lang/Object")
        # global decls
        for v in var_decls:
            self.instr(f".field static {v.var.identifier.name} {v.var.t.getJavaSignature()}")

        # main
        self.instr(".method public static main : ([Ljava/lang/String;)V")
        self.currentBuilder().indent()
        self.instr(f".limit stack {self.stackLimit}")
        self.instr(f".limit locals {len(node.declarations) + self.localLimit}")
        for d in var_decls:
            self.visit(d)
        self.defaultToGlobals = True
        for s in node.statements:
            self.visit(s)
        self.defaultToGlobals = False
        self.instr("return")
        self.currentBuilder().unindent()
        self.instr(".end method")

        # global inits
        self.instr(".method static <clinit> : ()V")
        self.currentBuilder().indent()
        self.instr(".code stack 1 locals 0")
        for v in var_decls:
            self.visit(v.value)
            self.instr(f"putstatic Field {self.main} {v.var.identifier.name} {v.var.t.getJavaSignature()}")
        self.instr("return")
        self.instr(".end code")
        self.instr(".end method")

        # global functions (static funcs)
        for d in func_decls:
            self.visit(d)
        self.instr(".end class")

        # other classes
        for d in cls_decls:
            self.visit(d)

    def ClassDef(self, node: ClassDef):
        self.currentClass = node.name.name
        self.classes[self.currentClass] = Builder(self.currentClass)

        func_decls = [d for d in node.declarations if isinstance(d, FuncDef)]
        var_decls = [d for d in node.declarations if isinstance(d, VarDef)]

        self.instr(".version 49 0")
        self.instr(f".class public super {self.currentClass}")
        self.instr(f".super {node.superclass.name}")
        # TODO
        for d in var_decls:
            self.visit(d)
        for d in func_decls:
            self.visit(d)
        self.instr(".end class")

    def FuncDef(self, node: FuncDef):
        self.enterScope()
        self.instr(
            f".method public static {node.name.name} : {node.type.getJavaSignature()}")
        self.currentBuilder().indent()
        self.instr(f".limit stack {self.stackLimit}")
        self.instr(f".limit locals {len(node.declarations) + self.localLimit}")
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
        self.currentBuilder().unindent()
        self.instr(".end method")

    def VarDef(self, node: VarDef):
        if node.isAttr:
            pass  # TODO field defs
        else:
            self.visit(node.value)
            self.newLocal(node.var.identifier.name,
                          node.value.inferredType.isJavaRef())

    # STATEMENTS

    def processAssignmentTarget(self, target: Expr):
        if isinstance(target, Identifier):
            if self.defaultToGlobals or target.isGlobal:
                self.instr(f"putstatic Field {self.main} {target.name} {target.inferredType.getJavaSignature()}")
            else:
                self.store(target.name, target.inferredType)
        elif isinstance(target, IndexExpr):
            # stack should be array, idx, value
            self.visit(target.list)
            self.instr("swap")
            self.visit(target.index)
            self.instr("swap")
            self.arrayStore(target.inferredType)
        elif isinstance(target, MemberExpr):
            pass  # TODO
        else:
            raise Exception(
                "Internal compiler error: unsupported assignment target")

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
        startLabel = self.newLabelName()
        elseLabel = self.newLabelName()
        endLabel = self.newLabelName()
        self.label(startLabel)
        self.visit(node.condition)
        self.instr(f"ifeq {elseLabel}")
        for s in node.thenBody:
            self.visit(s)
        self.instr(f"goto {endLabel}")
        self.label(elseLabel)
        for s in node.elseBody:
            self.visit(s)
        self.label(endLabel)

    def ExprStmt(self, node: ExprStmt):
        self.visit(node.expr)

    def comparator(self, instr: str, firstBranchTrue: bool = False):
        l1 = self.newLabelName()
        l2 = self.newLabelName()
        self.instr(f"{instr} {l1}")
        if firstBranchTrue:
            self.instr("iconst_1")
        else:
            self.instr("iconst_0")
        self.instr(f"goto {l2}")
        self.label(l1)
        if firstBranchTrue:
            self.instr("iconst_0")
        else:
            self.instr("iconst_1")
        self.label(l2)

    def isListConcat(self, operator: str, leftType: ValueType, rightType: ValueType) -> bool:
        return leftType.isListType() and rightType.isListType() and operator == "+"

    def BinaryExpr(self, node: BinaryExpr):
        operator = node.operator
        leftType = node.left.inferredType
        rightType = node.right.inferredType
        if not self.isListConcat(operator, leftType, rightType):
            self.visit(node.left)
            self.visit(node.right)
        # concatenation and addition
        if operator == "+":
            if self.isListConcat(operator, leftType, rightType):
                self.visit(node.left)
                self.visit(node.right)
                self.instr("dup2")
                arrR = self.newLocal(None, True)
                # stack is L, R, L
                self.instr("arraylength")
                lenL = self.newLocal(None, False)
                self.instr("arraylength")
                lenR = self.newLocal(None, False)
                self.instr(f"iload {lenL}")
                self.instr(f"iload {lenR}")
                self.instr("iadd")
                # stack is L, total_length
                t = node.inferredType
                if ((isinstance(t, ListValueType) and t.elementType.isJavaRef())
                        or t == EmptyType()):
                    # refs
                    self.instr(
                        "invokestatic Method java/util/Arrays copyOf ([Ljava/lang/Object;I)[Ljava/lang/Object;")
                    self.instr(f"checkcast {t.getJavaName()}")
                else:
                    # primitives
                    self.instr("invokestatic Method java/util/Arrays copyOf (" +
                               f"{self.ts.join(leftType, rightType).getJavaSignature()}I){t.getJavaSignature()}")
                # stack is new_array
                newArr = self.newLocal(None, True)
                self.instr(f"aload {arrR}")
                self.instr("iconst_0")
                self.instr(f"aload {newArr}")
                self.instr(f"iload {lenL}")
                self.instr(f"iload {lenR}")
                # stack is R, 0, new_array, len(L), len(R)
                self.instr(
                    "invokestatic Method java/lang/System arraycopy (Ljava/lang/Object;ILjava/lang/Object;II)V")
                self.instr(f"aload {newArr}")
            elif leftType == StrType():
                self.instr(
                    "invokevirtual Method java/lang/String concat (Ljava/lang/String;)Ljava/lang/String;")
            elif leftType == IntType():
                self.instr("iadd")
            else:
                raise Exception(
                    "Internal compiler error: unexpected operand types for +")
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
                self.instr(
                    "invokevirtual Method java/lang/String equals (Ljava/lang/Object;)Z")
            else:
                self.comparator("if_icmpeq")
        elif operator == "!=":
            if leftType.isJavaRef():
                self.instr(
                    "invokevirtual Method java/lang/String equals (Ljava/lang/Object;)Z")
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
            raise Exception(
                f"Internal compiler error: unexpected operator {operator}")

    def IndexExpr(self, node: IndexExpr):
        self.visit(node.list)
        self.visit(node.index)
        if node.list.inferredType.isListType():
            self.arrayLoad(node.inferredType)
        else:
            self.instr("dup")
            self.instr("iconst_1")
            self.instr("iadd")
            self.instr(
                "invokevirtual Method java/lang/String substring (II)Ljava/lang/String;")

    def UnaryExpr(self, node: UnaryExpr):
        self.visit(node.operand)
        if node.operator == "-":
            self.instr("ineg")
        elif node.operator == "not":
            self.comparator("ifne", True)

    def buildConstructor(self, node: CallExpr):
        className = node.function.name
        classType = ClassValueType(className)
        javaName = classType.getJavaName()
        self.instr(f"new {javaName}")
        self.instr("dup")
        self.instr(f"invokespecial Method {javaName} <init> ()V")

    def CallExpr(self, node: CallExpr):
        signature = node.function.inferredType.getJavaSignature()
        name = node.function.name
        if node.isConstructor:
            self.buildConstructor(node)
            return
        # TODO shadowing
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
            self.instr(f"invokestatic Method {self.main} {name} {signature}")
            if node.function.inferredType.returnType.isNone():
                self.NoneLiteral(None)  # push null for void return

    def ForStmt(self, node: ForStmt):
        # itr = {expr}
        self.visit(node.iterable)
        itr = self.newLocal(None, True)
        # idx = 0
        self.instr("iconst_0")
        idx = self.newLocal(None, False)
        startLabel = self.newLabelName()
        endLabel = self.newLabelName()
        self.label(startLabel)
        # while idx < len(itr)
        self.load(self.genLocalName(idx), IntType())
        self.load(self.genLocalName(itr), node.iterable.inferredType)
        if node.iterable.inferredType.isListType():
            self.instr("arraylength")
        else:
            self.instr("invokevirtual Method java/lang/String length ()I")
        self.instr("isub")
        self.instr(f"ifge {endLabel}")
        # x = itr[idx]
        self.load(self.genLocalName(itr), node.iterable.inferredType)
        self.load(self.genLocalName(idx), IntType())
        if node.iterable.inferredType.isListType():
            self.arrayLoad(node.iterable.inferredType)
        else:
            self.instr("dup")
            self.instr("iconst_1")
            self.instr("iadd")
            self.instr(
                "invokevirtual Method java/lang/String substring (II)Ljava/lang/String;")
        self.store(node.identifier.name, node.identifier.inferredType)
        # body
        for s in node.body:
            self.visit(s)
        # idx = idx + 1
        self.load(self.genLocalName(idx), IntType())
        self.instr("iconst_1")
        self.instr("iadd")
        self.store(self.genLocalName(idx), IntType())
        self.instr(f"goto {startLabel}")
        self.label(endLabel)

    def ListExpr(self, node: ListExpr):
        t = node.inferredType
        length = len(node.elements)
        self.instr(f"ldc {length}")
        elementType = None
        if isinstance(t, ClassValueType):
            elementType = ClassValueType("object")
        else:
            elementType = t.elementType
        if isinstance(t, ClassValueType) or elementType.isJavaRef():
            self.instr(f"anewarray {elementType.getJavaName()}")
        else:
            self.instr(f"newarray {elementType.getJavaName()}")
        for i in range(len(node.elements)):
            self.instr("dup")
            self.instr(f"ldc {i}")
            self.visit(node.elements[i])
            self.arrayStore(elementType)

    def WhileStmt(self, node: WhileStmt):
        startLabel = self.newLabelName()
        endLabel = self.newLabelName()
        self.label(startLabel)
        self.visit(node.condition)
        self.instr(f"ifeq {endLabel}")
        for s in node.body:
            self.visit(s)
        self.instr(f"goto {startLabel}")
        self.label(endLabel)

    def buildReturn(self, value: Expr):
        if self.returnType.isNone():
            self.instr("return")
        else:
            if value is None:
                self.NoneLiteral(None)
            else:
                self.visit(value)
            self.returnInstr(self.returnType)

    def ReturnStmt(self, node: ReturnStmt):
        self.buildReturn(node.value)

    def Identifier(self, node: Identifier):
        if self.defaultToGlobals or node.isGlobal:
            self.instr(f"getstatic Field {self.main} {node.name} {node.inferredType.getJavaSignature()}")
        else:
            self.load(node.name, node.inferredType)

    def MemberExpr(self, node: MemberExpr):
        pass

    def IfExpr(self, node: IfExpr):
        self.visit(node.condition)
        l1 = self.newLabelName()
        l2 = self.newLabelName()
        self.instr(f"ifne {l1}")
        self.visit(node.elseExpr)
        self.instr(f"goto {l2}")
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
        self.instr(f"ldc {node.value}")

    def NoneLiteral(self, node: NoneLiteral):
        self.instr("aconst_null")

    def StringLiteral(self, node: StringLiteral):
        self.instr(f"ldc {json.dumps(node.value)}")

    # TYPES

    def TypedVar(self, node: TypedVar):
        pass

    def ListType(self, node: ListType):
        pass

    def ClassType(self, node: ClassType):
        pass

    def emit(self) -> str:
        return self.currentBuilder().emit()

    # SUGAR

    def NonLocalDecl(self, node: NonLocalDecl):
        pass

    def GlobalDecl(self, node: GlobalDecl):
        pass

    # BUILT-INS - note: these are in-lined
    def emit_assert(self, arg: Expr):
        label = self.newLabelName()
        self.visit(arg)
        self.instr(f"ifne {label}")
        msg = f"failed assertion on line {arg.location[0]}"
        self.emit_exn(msg)
        self.label(label)

    def emit_exn(self, msg: str):
        self.instr("new java/lang/Exception")
        self.instr("dup")
        self.instr(f"ldc {json.dumps(msg)}")
        self.instr(
            "invokespecial Method java/lang/Exception <init> (Ljava/lang/String;)V")
        self.instr("athrow")

    def emit_input(self):
        self.instr("new java/util/Scanner")
        self.instr("dup")
        self.instr("getstatic Field java/lang/System in Ljava/io/InputStream;")
        self.instr(
            "invokespecial Method java/util/Scanner <init> (Ljava/io/InputStream;)V")
        l = self.newLocal()
        self.instr(f"aload {l}")
        self.currentBuilder().addLine(
            "invokevirtual Method java/util/Scanner nextLine ()Ljava/lang/String;")

    def emit_len(self, arg: Expr):
        t = arg.inferredType
        is_list = False
        if t.isListType():
            is_list = True
        else:
            if t == NoneType():
                is_list = True
            elif t == EmptyType():
                is_list = True
            elif t == StrType():
                is_list = False
            else:
                self.emit_exn(
                    f"Built-in function len is unsupported for values of type {arg.inferredType.classname}")
        self.visit(arg)
        if is_list:
            self.instr("arraylength")
        else:
            self.instr("invokevirtual Method java/lang/String length ()I")

    def emit_print(self, arg: Expr):
        if isinstance(arg.inferredType, ListValueType) or arg.inferredType.className not in {"bool", "int", "str"}:
            self.emit_exn(
                f"Built-in function print is unsupported for values of type {arg.inferredType.classname}")
        t = arg.inferredType.getJavaSignature()
        self.instr("getstatic Field java/lang/System out Ljava/io/PrintStream;")
        self.visit(arg)
        self.instr(
            f"invokevirtual Method java/io/PrintStream println ({t})V")
        self.NoneLiteral(None)  # push None for void return
