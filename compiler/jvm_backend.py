from .astnodes import *
from .types import *
from .builder import Builder
from .typesystem import TypeSystem
from .visitor import CommonVisitor
from typing import List, Dict, Optional, cast, Callable
import json


class JvmBackend(CommonVisitor):
    localLimit = 50
    stackLimit = 500
    defaultToGlobals = False  # treat all vars as global if this is true
    classes: Dict[str, Builder]

    def __init__(self, main: str, ts: TypeSystem):
        self.classes = {}
        self.classes[main] = Builder(main)
        self.currentClass = main
        self.main = main  # name of main class
        self.ts = ts
        self.locals = []
        self.enterScope()

    def currentBuilder(self) -> Builder:
        return self.classes[self.currentClass]

    def newLabelName(self) -> str:
        self.counter += 1
        return "L" + str(self.counter)

    def label(self, name: str):
        self.currentBuilder().unindent()
        self.instr(name + ":")
        self.currentBuilder().indent()

    def returnInstr(self, exprType: ValueType):
        if exprType.isJavaRef():
            self.instr("areturn")
        else:
            self.instr("ireturn")

    def wrap(self, val: Expr, elementType: ValueType):
        self.loadInt(1)
        self.instr(f"anewarray {elementType.getJavaName(True)}")
        self.instr("dup")
        self.loadInt(0)
        self.visit(val)
        self.arrayStore(elementType)

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

    def arrayStore(self, elementType: ValueType):
        # expect the stack to be array, idx, value
        if elementType == IntType():
            self.instr(
                "invokestatic Method java/lang/Integer valueOf (I)Ljava/lang/Integer;")
        elif elementType == BoolType():
            self.instr(
                "invokestatic Method java/lang/Boolean valueOf (Z)Ljava/lang/Boolean;")
        self.instr("aastore")

    def arrayLoad(self, elementType: ValueType):
        # expect the stack to be array, idx
        self.instr("aaload")
        if elementType == IntType():
            self.instr("invokevirtual Method java/lang/Integer intValue ()I")
        elif elementType == BoolType():
            self.instr(
                "invokevirtual Method java/lang/Boolean booleanValue ()Z")

    def newLocalEntry(self, name: str) -> int:
        # add a new entry to locals table w/o storing anything
        n = len(self.locals[-1])
        self.locals[-1][name] = n
        return n

    def genLocalName(self, offset: int) -> str:
        return f"__local__{offset}"

    def newLocal(self, name: Optional[str] = None, isRef: bool = True) -> int:
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

    def visitStmtList(self, stmts: List[Stmt]):
        if len(stmts) == 0:
            self.instr("nop")
        else:
            for s in stmts:
                self.visit(s)

    def Program(self, node: Program):
        func_decls = [d for d in node.declarations if isinstance(d, FuncDef)]
        cls_decls = [d for d in node.declarations if isinstance(d, ClassDef)]
        var_decls = [d for d in node.declarations if isinstance(d, VarDef)]

        self.instr(".version 49 0")
        self.instr(f".class public super {self.main}")
        self.instr(".super java/lang/Object")
        # global decls
        for v in var_decls:
            self.instr(
                f".field static {v.var.identifier.name} {v.var.getTypeX().getJavaSignature()}")

        # main
        self.instr(".method public static main : ([Ljava/lang/String;)V")
        self.currentBuilder().indent()
        self.instr(
            f".code stack {self.stackLimit} locals {len(node.declarations) + self.localLimit}")
        self.defaultToGlobals = True
        self.visitStmtList(node.statements)
        self.defaultToGlobals = False
        self.instr("return")
        self.instr(".end code")
        self.currentBuilder().unindent()
        self.instr(".end method")

        # global inits
        self.instr(".method static <clinit> : ()V")
        self.currentBuilder().indent()
        self.instr(".code stack 1 locals 0")
        for v in var_decls:
            self.visit(v.value)
            self.instr(
                f"putstatic Field {self.main} {v.var.identifier.name} {v.var.getTypeX().getJavaSignature()}")
        self.instr("return")
        self.instr(".end code")
        self.currentBuilder().unindent()
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

        superclass = ClassValueType(node.superclass.name).getJavaName()

        self.instr(".version 49 0")
        self.instr(f".class public super {self.currentClass}")
        self.instr(f".super {superclass}")

        constructor_def = None
        # field decls
        for v in var_decls:
            self.instr(
                f".field {v.var.identifier.name} {v.var.getTypeX().getJavaSignature()}")
        for d in func_decls:
            if d.name.name == "__init__":
                constructor_def = d
                d.declarations = var_decls + d.declarations
                self.constructor(superclass, d)
            else:
                self.method(d)
        if constructor_def is None:
            funcDef = node.getDefaultConstructor()
            self.constructor(superclass, funcDef)
        self.instr(".end class")

    def funcDefHelper(self, node: FuncDef):
        for i in range(len(node.params)):
            self.newLocalEntry(node.params[i].identifier.name)
        for d in node.declarations:
            self.visit(d)
        # pyrefly: ignore [bad-assignment]
        self.returnType = node.getTypeX().returnType
        # handle last return
        self.visitStmtList(node.statements)
        hasReturn = False
        for s in node.statements:
            if s.isReturn:
                hasReturn = True
        if not hasReturn:
            self.buildReturn(None)
        self.exitScope()

    def constructor(self, superclass: str, node: FuncDef):
        self.enterScope()
        constructorSig = node.getTypeX().dropFirstParam()
        self.instr(
            f".method public <init> : {constructorSig.getJavaSignature()}")
        self.currentBuilder().indent()
        self.instr(
            f".code stack {self.stackLimit} locals {len(node.declarations) + self.localLimit}")
        # call superclass constructor
        self.instr("aload 0")
        self.instr(f"invokespecial Method {superclass} <init> ()V ")
        self.funcDefHelper(node)
        self.instr(".end code")
        self.currentBuilder().unindent()
        self.instr(".end method")

    def method(self, node: FuncDef):
        self.enterScope()
        methodSig = node.getTypeX().dropFirstParam()
        self.instr(
            f".method public {node.name.name} : {methodSig.getJavaSignature()}")
        self.currentBuilder().indent()
        self.instr(
            f".code stack {self.stackLimit} locals {len(node.declarations) + self.localLimit}")
        self.funcDefHelper(node)
        self.instr(".end code")
        self.currentBuilder().unindent()
        self.instr(".end method")

    def FuncDef(self, node: FuncDef):
        self.enterScope()
        self.instr(
            f".method public static {node.name.name} : {node.getTypeX().getJavaSignature()}")
        self.currentBuilder().indent()
        self.instr(
            f".code stack {self.stackLimit} locals {len(node.declarations) + self.localLimit}")
        self.funcDefHelper(node)
        self.instr(".end code")
        self.currentBuilder().unindent()
        self.instr(".end method")

    def VarDef(self, node: VarDef):
        varName = node.var.identifier.name
        if node.isAttr:
            className = ClassValueType(self.currentClass)
            self.instr("aload 0")
            self.visit(node.value)
            self.instr(
                f"putfield Field {className.getJavaName()} {varName} {node.var.getTypeX().getJavaSignature()}")
        elif node.var.varInstanceX().isNonlocal:
            self.wrap(node.value, node.var.getTypeX())
            self.newLocal(varName, True)
        else:
            self.visit(node.value)
            self.newLocal(varName, node.value.inferredValueType().isJavaRef())

    # STATEMENTS

    def processAssignmentTarget(self, target: Expr):
        if isinstance(target, Identifier):
            if self.defaultToGlobals or target.varInstanceX().isGlobal:
                self.instr(
                    f"putstatic Field {self.main} {target.name} {target.inferredValueType().getJavaSignature()}")
            elif target.varInstanceX().isNonlocal:
                self.load(target.name, ListValueType(
                    target.inferredValueType()))
                self.instr("swap")
                self.loadInt(0)
                self.instr("swap")
                self.arrayStore(target.inferredValueType())
            else:
                self.store(target.name, target.inferredValueType())
        elif isinstance(target, IndexExpr):
            # stack should be array, idx, value
            self.visit(target.list)
            self.instr("swap")
            self.visit(target.index)
            self.instr("swap")
            self.arrayStore(target.inferredValueType())
        elif isinstance(target, MemberExpr):
            self.visit(target.object)
            self.instr("swap")
            self.instr(
                f"putfield Field {cast(ClassValueType, target.object.inferredValueType()).className} {target.member.name} {target.inferredValueType().getJavaSignature()}")
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
        if len(node.elseBody) == 0:
            startLabel = self.newLabelName()
            endLabel = self.newLabelName()
            self.label(startLabel)
            self.visit(node.condition)
            self.instr(f"ifeq {endLabel}")
            self.visitStmtList(node.thenBody)
            self.label(endLabel)
            self.instr("nop")
        else:
            startLabel = self.newLabelName()
            elseLabel = self.newLabelName()
            endLabel = self.newLabelName()
            self.label(startLabel)
            self.visit(node.condition)
            self.instr(f"ifeq {elseLabel}")
            self.visitStmtList(node.thenBody)
            self.instr(f"goto {endLabel}")
            self.label(elseLabel)
            self.visitStmtList(node.elseBody)
            self.label(endLabel)
            self.instr("nop")

    def ExprStmt(self, node: ExprStmt):
        self.visit(node.expr)
        if isinstance(node.expr, CallExpr) or isinstance(node.expr, MethodCallExpr):
            self.instr("pop")

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
        self.instr("nop")

    def isListConcat(self, operator: str, leftType: ValueType, rightType: ValueType) -> bool:
        return leftType.isListType() and rightType.isListType() and operator == "+"

    def BinaryExpr(self, node: BinaryExpr):
        operator = node.operator
        leftType = node.left.inferredValueType()
        rightType = node.right.inferredValueType()
        shortCircuitOps = {"and", "or"}
        if operator not in shortCircuitOps:
            self.visit(node.left)
            self.visit(node.right)
        # concatenation and addition
        if operator == "+":
            if self.isListConcat(operator, leftType, rightType):
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
                list_t = cast(ListValueType, self.ts.join(leftType, rightType))
                self.instr(
                    f"anewarray {list_t.elementType.getJavaName(True)}")
                newArr = self.newLocal(None, True)
                self.instr("iconst_0")
                self.instr(f"aload {newArr}")
                self.instr("iconst_0")
                self.instr(f"iload {lenL}")
                # stack is L, 0, new_array, 0, len(L)
                self.instr(
                    "invokestatic Method java/lang/System arraycopy (Ljava/lang/Object;ILjava/lang/Object;II)V")
                # stack is new_array
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
            self.instr("invokestatic Method java/lang/Math floorMod (II)I")
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
            c = lambda: self.visit(node.left)
            t = lambda: self.visit(node.right)
            e = lambda: self.instr("iconst_0")
            self.ternary(c, t, e)
        elif operator == "or":
            c = lambda: self.visit(node.left)
            t = lambda: self.instr("iconst_1")
            e = lambda: self.visit(node.right)
            self.ternary(c, t, e)
        else:
            raise Exception(
                f"Internal compiler error: unexpected operator {operator}")

    def IndexExpr(self, node: IndexExpr):
        self.visit(node.list)
        self.visit(node.index)
        if node.list.inferredValueType().isListType():
            self.arrayLoad(
                cast(ListValueType, node.list.inferredType).elementType)
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
        assert isinstance(node.function.inferredType, FuncType)
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
            for i in range(len(node.args)):
                self.visitArg(node.function.inferredType, i, node.args[i])
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
        self.load(self.genLocalName(itr), node.iterable.inferredValueType())
        if node.iterable.inferredValueType().isListType():
            self.instr("arraylength")
        else:
            self.instr("invokevirtual Method java/lang/String length ()I")
        self.instr("isub")
        self.instr(f"ifge {endLabel}")
        # x = itr[idx]
        self.load(self.genLocalName(itr), node.iterable.inferredValueType())
        self.load(self.genLocalName(idx), IntType())
        if node.iterable.inferredValueType().isListType():
            self.arrayLoad(
                cast(ListValueType, node.iterable.inferredValueType()).elementType)
        else:
            self.instr("dup")
            self.instr("iconst_1")
            self.instr("iadd")
            self.instr(
                "invokevirtual Method java/lang/String substring (II)Ljava/lang/String;")
        self.processAssignmentTarget(node.identifier)
        # body
        self.visitStmtList(node.body)
        # idx = idx + 1
        self.load(self.genLocalName(idx), IntType())
        self.instr("iconst_1")
        self.instr("iadd")
        self.store(self.genLocalName(idx), IntType())
        self.instr(f"goto {startLabel}")
        self.label(endLabel)
        self.instr("nop")

    def ListExpr(self, node: ListExpr):
        t = node.inferredType
        length = len(node.elements)
        self.loadInt(length)
        elementType = None
        if isinstance(t, ClassValueType):
            if node.emptyListType:
                elementType = node.emptyListType
            else:
                elementType = ClassValueType("object")
        else:
            elementType = cast(ListValueType, t).elementType
        self.instr(f"anewarray {elementType.getJavaName(True)}")
        for i in range(len(node.elements)):
            self.instr("dup")
            self.loadInt(i)
            self.visit(node.elements[i])
            self.arrayStore(elementType)

    def WhileStmt(self, node: WhileStmt):
        startLabel = self.newLabelName()
        endLabel = self.newLabelName()
        self.label(startLabel)
        self.visit(node.condition)
        self.instr(f"ifeq {endLabel}")
        self.visitStmtList(node.body)
        self.instr(f"goto {startLabel}")
        self.label(endLabel)
        self.instr("nop")

    def buildReturn(self, value: Optional[Expr]):
        # pyrefly: ignore [missing-attribute]
        if self.returnType.isNone():
            self.instr("return")
        else:
            if value is None:
                self.NoneLiteral(None)
            else:
                self.visit(value)
            # pyrefly: ignore [bad-argument-type]
            self.returnInstr(self.returnType)

    def ReturnStmt(self, node: ReturnStmt):
        self.buildReturn(node.value)

    def Identifier(self, node: Identifier):
        if self.defaultToGlobals or node.varInstanceX().isGlobal:
            self.instr(
                f"getstatic Field {self.main} {node.name} {node.inferredValueType().getJavaSignature()}")
        elif node.varInstanceX().isNonlocal:
            self.load(node.name, ListValueType(node.inferredValueType()))
            self.loadInt(0)
            self.arrayLoad(node.inferredValueType())
        else:
            self.load(node.name, node.inferredValueType())

    def MemberExpr(self, node: MemberExpr):
        self.visit(node.object)
        self.instr(
            f"getfield Field {cast(ClassValueType, node.object.inferredValueType()).className} {node.member.name} {node.inferredValueType().getJavaSignature()}")

    def IfExpr(self, node: IfExpr):
        c = lambda: self.visit(node.condition)
        t = lambda: self.visit(node.thenExpr)
        e = lambda: self.visit(node.elseExpr)
        self.ternary(c, t, e)

    def ternary(self, condFn: Callable, thenFn: Callable, elseFn: Callable):
        condFn()
        l1 = self.newLabelName()
        l2 = self.newLabelName()
        self.instr(f"ifne {l1}")
        elseFn()
        self.instr(f"goto {l2}")
        self.label(l1)
        thenFn()
        self.label(l2)
        self.instr("nop")

    def MethodCallExpr(self, node: MethodCallExpr):
        className = cast(
            ClassValueType, node.method.object.inferredType).className
        methodName = node.method.member.name
        if methodName == "__init__" and className in {"int", "bool"}:
            return
        self.visit(node.method.object)
        methodType = node.method.inferredType
        assert isinstance(methodType, FuncType)
        for i in range(len(node.args)):
            self.visitArg(methodType, i + 1, node.args[i])
        javaMethodType = methodType.dropFirstParam()
        self.instr(
            f"invokevirtual Method {className} {methodName} {javaMethodType.getJavaSignature()}")
        if methodType.returnType.isNone():
            self.NoneLiteral(None)  # push null for void return

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        if node.value:
            self.instr("iconst_1")
        else:
            self.instr("iconst_0")

    def loadInt(self, value: int):
        if value >= 0 and value <= 5:
            self.instr(f"iconst_{value}")
        else:
            self.instr(f"ldc {value}")

    def IntegerLiteral(self, node: IntegerLiteral):
        # pyrefly: ignore [bad-argument-type]
        self.loadInt(node.value)

    def NoneLiteral(self, node: Optional[NoneLiteral]):
        self.instr("aconst_null")

    def StringLiteral(self, node: StringLiteral):
        self.instr(f"ldc {json.dumps(node.value)}")

    # BUILT-INS - note: these are in-lined
    def emit_assert(self, arg: Expr):
        label = self.newLabelName()
        self.visit(arg)
        self.instr(f"ifne {label}")
        msg = f"failed assertion on line {arg.location[0]}"
        self.emit_exn(msg)
        self.label(label)
        self.NoneLiteral(None)

    def emit_exn(self, msg: str):
        self.instr("new java/lang/Exception")
        self.instr("dup")
        self.instr(f"ldc {json.dumps(msg)}")
        self.instr(
            "invokespecial Method java/lang/Exception <init> (Ljava/lang/String;)V")
        self.instr("athrow")
        self.NoneLiteral(None)

    def emit_input(self):
        self.instr("new java/util/Scanner")
        self.instr("dup")
        self.instr("getstatic Field java/lang/System in Ljava/io/InputStream;")
        self.instr(
            "invokespecial Method java/util/Scanner <init> (Ljava/io/InputStream;)V")
        l = self.newLocal()
        self.instr(f"aload {l}")
        self.instr(
            "invokevirtual Method java/util/Scanner nextLine ()Ljava/lang/String;")

    def emit_len(self, arg: Expr):
        t = arg.inferredValueType()
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
                    "Built-in function len is unsupported for values of this type")
                return
        self.visit(arg)
        if is_list:
            self.instr("arraylength")
        else:
            self.instr("invokevirtual Method java/lang/String length ()I")

    def emit_print(self, arg: Expr):
        if isinstance(arg.inferredType, ListValueType) or cast(ClassValueType, arg.inferredType).className not in {"bool", "int", "str"}:
            self.emit_exn(
                "Built-in function print is unsupported for values of this type")
        t = arg.inferredValueType().getJavaSignature()
        self.instr("getstatic Field java/lang/System out Ljava/io/PrintStream;")
        self.visit(arg)
        self.instr(
            f"invokevirtual Method java/io/PrintStream println ({t})V")
        self.NoneLiteral(None)  # push None for void return

    def visitArg(self, funcType: FuncType, paramIdx: int, arg: Expr):
        argIsRef = isinstance(
            arg, Identifier) and arg.varInstanceX().isNonlocal
        paramIsRef = paramIdx in funcType.refParams
        if argIsRef and paramIsRef and cast(Identifier, arg).varInstance == funcType.refParams[paramIdx]:
            # ref arg and ref param, pass ref arg
            self.load(cast(Identifier, arg).name,
                      ListValueType(arg.inferredValueType()))
        elif paramIsRef:
            # non-ref arg and ref param, or do not pass ref arg
            # unwrap if necessary, re-wrap
            self.wrap(arg, arg.inferredValueType())
        else:  # non-ref param, maybe unwrap
            self.visit(arg)
