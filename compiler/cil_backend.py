from .astnodes import *
from .types import *
from .builder import Builder
from .typesystem import TypeSystem
from .visitor import Visitor
from collections import defaultdict
import json


class CilBackend(Visitor):

    def __init__(self, main: str, ts: TypeSystem):
        self.classes = dict()
        self.classes[main] = Builder(main)
        self.currentClass = main
        self.main = main  # name of main class
        self.locals = [defaultdict(lambda: None)]
        self.counter = 0  # for labels
        self.returnType = None
        self.localLimit = 50
        self.stackLimit = 500
        self.ts = ts
        self.defaultToGlobals = False  # treat all vars as global if this is true

    def indent(self):
        self.instr("{")
        self.currentBuilder().indent()

    def unindent(self):
        self.currentBuilder().unindent()
        self.instr("}")

    def currentBuilder(self):
        return self.classes[self.currentClass]

    def visit(self, node: Node):
        node.visit(self)

    def instr(self, instr: str):
        self.currentBuilder().newLine(instr)

    def newLabelName(self) -> str:
        self.counter += 1
        return "IL_"+str(self.counter)

    def label(self, name: str) -> str:
        self.currentBuilder().unindent()
        self.instr(name+": nop")
        self.currentBuilder().indent()

    def enterScope(self):
        self.locals.append(defaultdict(lambda: None))

    def exitScope(self):
        self.locals.pop()

    def wrap(self, val:Expr, elementType:ValueType):
        raise Exception("unimplemented")

    def store(self, name: str, t: ValueType):
        n = self.locals[-1][name]
        if n is None:
            raise Exception(
                f"Internal compiler error: unknown name {name} for store")
        self.instr(f"stloc {n}")

    def load(self, name: str, t: ValueType):
        n = self.locals[-1][name]
        if n is None:
            raise Exception(
                f"Internal compiler error: unknown name {name} for load")
        self.instr(f"ldloc {n}")

    def arrayStore(self, elementType:ValueType):
        raise Exception("unimplemented")

    def arrayLoad(self, elementType:ValueType):
        raise Exception("unimplemented")

    def newLocalEntry(self, name: str) -> int:
        raise Exception("unimplemented")

    def genLocalName(self, offset: int) -> str:
        return f"__local__{offset}"

    def newLocal(self, name: str = None) -> int:
        # store the top of stack as a new local
        n = len(self.locals[-1])
        self.instr(f"stloc {n}")
        if name is None:
            name = self.genLocalName(n)
        self.locals[-1][name] = n
        return n

    def visitStmtList(self, stmts:[Stmt]):
        if len(stmts) == 0:
            self.instr("nop")
        else:
            for s in stmts:
                self.visit(s)

    def Program(self, node: Program):
        # TODO
        self.instr(f".assembly '{self.main}'")
        self.instr("{")
        self.instr("}")
        self.instr(f".module {self.main}.exe")
        self.instr(f".class public auto ansi beforefieldinit {self.main} extends [mscorlib]System.Object")
        self.indent()

        var_decls = [d for d in node.declarations if isinstance(d, VarDef)]
        for v in var_decls:
            self.instr(f".field public static {v.var.t.getCILName()} {v.var.identifier.name}")

        self.instr(".method public static hidebysig default void Main (string[] args)  cil managed")
        self.indent()
        self.instr(".entrypoint")
        self.instr(f".maxstack {self.localLimit}")
        self.defaultToGlobals = True
        for v in var_decls:
            self.visit(v.value)
            self.instr(f"stsfld {v.var.t.getCILName()} {self.main}::{v.var.identifier.name}")
        self.visitStmtList(node.statements)
        self.defaultToGlobals = False
        self.instr("ret")
        self.unindent()
        self.unindent()

    def ClassDef(self, node: ClassDef):
        raise Exception("unimplemented")

    def FuncDef(self, node: FuncDef):
        raise Exception("unimplemented")

    def VarDef(self, node: VarDef):
        raise Exception("unimplemented")

    # STATEMENTS

    def processAssignmentTarget(self, target: Expr):
        if isinstance(target, Identifier):
            if self.defaultToGlobals or target.varInstance.isGlobal:
                self.instr(
                    f"stsfld {target.inferredType.getCILName()} {self.main}::{target.name}")
            elif target.varInstance.isNonlocal:
                raise Exception("unimplemented")
            else:
                self.store(target.name, target.inferredType)

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
            self.instr(f"brfalse {endLabel}")
            self.visitStmtList(node.thenBody)
            self.label(endLabel)
            self.instr("nop")
        else:
            startLabel = self.newLabelName()
            elseLabel = self.newLabelName()
            endLabel = self.newLabelName()
            self.label(startLabel)
            self.visit(node.condition)
            self.instr(f"brfalse {elseLabel}")
            self.visitStmtList(node.thenBody)
            self.instr(f"br {endLabel}")
            self.label(elseLabel)
            self.visitStmtList(node.elseBody)
            self.label(endLabel)
            self.instr("nop")

    def ExprStmt(self, node: ExprStmt):
        self.visit(node.expr)
        if isinstance(node.expr, CallExpr) or isinstance(node.expr, MethodCallExpr):
            self.instr("pop")

    def isListConcat(self, operator: str, leftType: ValueType, rightType: ValueType) -> bool:
        return leftType.isListType() and rightType.isListType() and operator == "+"

    def BinaryExpr(self, node: BinaryExpr):
        operator = node.operator
        leftType = node.left.inferredType
        rightType = node.right.inferredType
        if not self.isListConcat(operator, leftType, rightType):
            self.visit(node.left)
            self.visit(node.right)
        if operator == "+":
            if self.isListConcat(operator, leftType, rightType):
        # var z = new int[x.Length + y.Length];
        # x.CopyTo(z, 0);
        # y.CopyTo(z, x.Length);
        # IL_000f: ldloc.0
        # IL_0010: ldlen
        # IL_0011: conv.i4
        # IL_0012: ldloc.1
        # IL_0013: ldlen
        # IL_0014: conv.i4
        # IL_0015: add
        # IL_0016: newarr [mscorlib]System.Int32
        # IL_001b: stloc.2
        # IL_001c: ldloc.0
        # IL_001d: ldloc.2
        # IL_001e: ldc.i4.0
        # IL_001f: callvirt instance void [mscorlib]System.Array::CopyTo(class [mscorlib]System.Array, int32)
        # IL_0024: nop
        # IL_0025: ldloc.1
        # IL_0026: ldloc.2
        # IL_0027: ldloc.0
        # IL_0028: ldlen
        # IL_0029: conv.i4
        # IL_002a: callvirt instance void [mscorlib]System.Array::CopyTo(class [mscorlib]System.Array, int32)
                # TODO
                pass
            elif leftType == StrType():
                self.instr("call string [mscorlib]System.String::Concat(string, string)")
            elif leftType == IntType():
                self.instr("add.ovf")
            else:
                raise Exception(
                    "Internal compiler error: unexpected operand types for +")
        # other arithmetic operators
        elif operator == "-":
            self.instr("sub.ovf")
        elif operator == "*":
            self.instr("mul.ovf")
        elif operator == "//":
            self.instr("div")
        elif operator == "%":
            self.instr("rem")
        # relational operators
        elif operator == "<":
            self.instr("clt")
        elif operator == "<=":
            self.instr("cgt")
            self.instr("ldc.i4.0")
            self.instr("ceq")
        elif operator == ">":
            self.instr("cgt")
        elif operator == ">=":
            self.instr("clt")
            self.instr("ldc.i4.0")
            self.instr("ceq")
        elif operator == "==":
            if leftType == StrType():
                self.instr("call instance bool [mscorlib]System.String::Equals(string)")
            else:
                self.instr("ceq")
        elif operator == "!=":
            self.instr("ceq")
            self.instr("ldc.i4.0")
            self.instr("ceq")
        elif operator == "is":
            self.instr("ceq")
        # logical operators
        elif operator == "and":
            self.instr("and")
        elif operator == "or":
            self.instr("or")
        else:
            raise Exception(
                f"Internal compiler error: unexpected operator {operator}")

    def IndexExpr(self, node: IndexExpr):
        self.visit(node.list)
        self.visit(node.index)
        self.instr("conv.i4")
        if node.list.inferredType.isListType():
            raise Exception("unimplemented")
        else:
            self.instr("call instance char [mscorlib]System.String::get_Chars(int32)")
            self.instr("ldc.i4.1")
            self.instr("newobj instance void [mscorlib]System.String::.ctor(char, int32)")

    def UnaryExpr(self, node: UnaryExpr):
        self.visit(node.operand)
        if node.operator == "-":
            self.instr("neg")
        elif node.operator == "not":
            self.instr("ldc.i4.0")
            self.instr("ceq")

    def CallExpr(self, node: CallExpr):
        name = node.function.name
        if node.isConstructor:
            raise Exception("unimplemented")
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
            raise Exception("unimplemented")

    def ForStmt(self, node: ForStmt):
        raise Exception("unimplemented")

    def ListExpr(self, node: ListExpr):
        raise Exception("unimplemented")

    def WhileStmt(self, node: WhileStmt):
        raise Exception("unimplemented")

    def buildReturn(self, value: Expr):
        if not self.returnType.isNone():
            if value is None:
                self.NoneLiteral(None)
            else:
                self.visit(value)
        self.instr("ret")

    def ReturnStmt(self, node: ReturnStmt):
        self.buildReturn(node.value)

    def Identifier(self, node: Identifier):
        if self.defaultToGlobals or node.varInstance.isGlobal:
            self.instr(f"ldsfld {node.inferredType.getCILName()} {self.main}::{node.name}")
        elif node.varInstance.isNonlocal:
            raise Exception("unimplemented")
        else:
            self.load(node.name, node.inferredType)

    def MemberExpr(self, node: MemberExpr):
        raise Exception("unimplemented")
    
    def IfExpr(self, node: IfExpr):
        self.visit(node.condition)
        l1 = self.newLabelName()
        l2 = self.newLabelName()
        self.instr(f"brtrue {l1}")
        self.visit(node.elseExpr)
        self.instr(f"br {l2}")
        self.label(l1)
        self.visit(node.thenExpr)
        self.label(l2)
        self.instr("nop")

    def MethodCallExpr(self, node: MethodCallExpr):
        raise Exception("unimplemented")

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        if node.value:
            self.instr("ldc.i4.1")
        else:
            self.instr("ldc.i4.0")

    def IntegerLiteral(self, node: IntegerLiteral):
        self.instr(f"ldc.i8 {node.value}")

    def NoneLiteral(self, node: NoneLiteral):
        self.instr("ldnull")

    def StringLiteral(self, node: StringLiteral):
        self.instr(f"ldstr {json.dumps(node.value)}")

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
        self.instr(f"brtrue {label}")
        msg = f"failed assertion on line {arg.location[0]}"
        self.emit_exn(msg)
        self.label(label)
        self.NoneLiteral(None)

    def emit_exn(self, msg: str):
        self.instr(f'ldstr "{msg}"')
        self.instr("newobj instance void [mscorlib]System.Exception::.ctor(string)")
        self.instr("throw")

    def emit_input(self):
        self.instr("call string [System.Console]System.Console::ReadLine()")

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
            self.instr("ldlen")
            self.instr("conv.i8")
        else:
            self.instr("callvirt instance int32 [mscorlib]System.String::get_Length()")
            self.instr("conv.i8")

    def emit_print(self, arg: Expr):
        self.visit(arg)
        self.instr("call void class [mscorlib]System.Console::WriteLine(string)")
        self.NoneLiteral(None)

    def visitArg(self, funcType, paramIdx: int, arg: Expr):
        self.visit(arg)
        # TODO
