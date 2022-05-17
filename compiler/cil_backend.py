from cmath import log
from .astnodes import *
from .types import *
from .builder import Builder
from .typesystem import TypeSystem
from .visitor import Visitor
from collections import defaultdict
import json

class CilStackLoc:
    def __init__(self, name, loc, t, isArg):
        self.name = name
        self.loc = loc
        self.isArg = isArg
        self.t = t

    def decl(self):
        return f"[{self.loc}] {self.t} {self.name}"

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

    def store(self, name: str):
        n = self.locals[-1][name]
        if n is None:
            raise Exception(
                f"Internal compiler error: unknown name {name} for store")
        if n.isArg:
            self.instr(f"starg {n.loc}")
        else:
            self.instr(f"stloc {n.loc}")

    def load(self, name: str):
        n = self.locals[-1][name]
        if n is None:
            raise Exception(
                f"Internal compiler error: unknown name {name} for load")
        if n.isArg:
            self.instr(f"ldarg {n.loc}")
        else:
            self.instr(f"ldloc {n.loc}")

    def arrayStore(self, elementType:ValueType):
        self.instr(f"stelem {elementType.getCILName()}")

    def arrayLoad(self, elementType:ValueType):
        self.instr(f"ldelem {elementType.getCILName()}")

    def newLocalEntry(self, name: str, t: ValueType, isArg: bool = False) -> int:
        # add a new entry to locals table w/o storing anything
        n = len([k for k in self.locals[-1] if self.locals[-1][k].isArg == isArg])
        self.locals[-1][name] = CilStackLoc(name, n, t.getCILName(), isArg)
        return n

    def genLocalName(self, offset: int) -> str:
        return f"__local__{offset}"

    def newLocal(self, name: str, t: ValueType):
        # store the top of stack as a new local
        n = len([k for k in self.locals[-1] if not self.locals[-1][k].isArg])
        self.instr(f"stloc {n}")
        if name is None:
            name = self.genLocalName(n)
        self.locals[-1][name] = CilStackLoc(name, n, t.getCILName(), False)
        return name

    def visitStmtList(self, stmts:[Stmt]):
        if len(stmts) == 0:
            self.instr("nop")
        else:
            for s in stmts:
                self.visit(s)

    def Program(self, node: Program):
        func_decls = [d for d in node.declarations if isinstance(d, FuncDef)]
        cls_decls = [d for d in node.declarations if isinstance(d, ClassDef)]
        var_decls = [d for d in node.declarations if isinstance(d, VarDef)]

        self.instr(f".assembly '{self.main}'")
        self.instr("{")
        self.instr("}")
        self.instr(f".module {self.main}.exe")
        self.instr(f".class public auto ansi beforefieldinit {self.main} extends [mscorlib]System.Object")
        self.indent()

        # global vars (static members)
        for v in var_decls:
            self.instr(f".field public static {v.var.t.getCILName()} {v.var.identifier.getCILName()}")

        # main method, top level statements
        self.instr(".method public static hidebysig default void Main (string[] args)  cil managed")
        self.indent()
        self.instr(".entrypoint")
        self.instr(f".maxstack {self.localLimit}")
        locals = self.currentBuilder().newBlock()
        self.defaultToGlobals = True
        for v in var_decls:
            self.visit(v.value)
            self.instr(f"stsfld {v.var.t.getCILName()} {self.main}::{v.var.identifier.getCILName()}")
        self.visitStmtList(node.statements)
        self.defaultToGlobals = False
        self.generateLocalsDirective(locals)
        self.instr("ret")
        self.unindent()

        # global functions (static funcs)
        for d in func_decls:
            self.visit(d)
        self.unindent()

    def ClassDef(self, node: ClassDef):
        raise Exception("unimplemented")

    def generateLocalsDirective(self, locals):
        # defer local declarations until we know what we need
        locals.newLine(".locals init (").indent()
        mapping = self.locals[-1]
        localDecls = [mapping[k] for k in mapping if not mapping[k].isArg]
        sortedDecls = sorted(localDecls, key=lambda x: x.loc)
        for i in range(len(sortedDecls)):
            comma = "," if i < len(sortedDecls) - 1 else ""
            locals.newLine(sortedDecls[i].decl() + comma)
        locals.unindent().newLine(")")

    def FuncDef(self, node: FuncDef):
        self.instr(".method public hidebysig static")
        self.instr(f"{node.type.getCILSignature(node.name.getCILName())} cil managed")
        self.indent()
        self.instr(f".maxstack {self.localLimit}")
        self.enterScope()

        # initialize locals
        locals = self.currentBuilder().newBlock()

        for i in range(len(node.params)):
            self.newLocalEntry(node.params[i].identifier.getCILName(), node.type.parameters[i], True)
        for d in node.declarations:
            self.visit(d)
        self.returnType = node.type.returnType

        # handle last return
        self.visitStmtList(node.statements)
        hasReturn = False
        for s in node.statements:
            if s.isReturn:
                hasReturn = True
        if not hasReturn:
            self.buildReturn(None)
        self.generateLocalsDirective(locals)
        self.exitScope()
        self.unindent()

    def VarDef(self, node: VarDef):
        varName = node.var.identifier.getCILName()
        if node.isAttr:
            raise Exception("unimplemented")
        elif node.var.varInstance.isNonlocal:
            raise Exception("unimplemented")
        else:
            self.visit(node.value)
            self.newLocal(varName, node.var.t)

    # STATEMENTS

    def processAssignmentTarget(self, target: Expr):
        if isinstance(target, Identifier):
            if self.defaultToGlobals or target.varInstance.isGlobal:
                self.instr(
                    f"stsfld {target.inferredType.getCILName()} {self.main}::{target.getCILName()}")
            elif target.varInstance.isNonlocal:
                raise Exception("unimplemented")
            else:
                self.store(target.getCILName())
        elif isinstance(target, IndexExpr):
            temp = self.newLocal(None, target.inferredType)
            self.visit(target.list)
            self.visit(target.index)
            self.load(temp)
            self.arrayStore(target.inferredType)
        elif isinstance(target, MemberExpr):
            raise Exception("unimplemented")
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
            self.instr(f"brfalse {endLabel}")
            self.visitStmtList(node.thenBody)
            self.label(endLabel)
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
        self.visit(node.left)
        self.visit(node.right)
        if operator == "+":
            if self.isListConcat(operator, leftType, rightType):
                """
                var x = new int[];
                var y = new int[];
                var z = new int[x.Length + y.Length];
                x.CopyTo(z, 0);
                y.CopyTo(z, x.Length);
                """
                r = self.newLocal(None, rightType)
                l = self.newLocal(None, leftType)
                self.load(l)
                self.instr("ldlen")
                self.load(r)
                self.instr("ldlen")
                self.instr("add")
                self.instr("conv.i4")
                merged_t = self.ts.join(leftType, rightType).elementType
                self.instr(f"newarr {merged_t.getCILName()}")
                merged = self.newLocal(None, ListValueType(merged_t))
                self.load(l)
                self.load(merged)
                self.instr("ldc.i4 0")
                self.instr("callvirt instance void [mscorlib]System.Array::CopyTo(class [mscorlib]System.Array, int32)")
                self.load(r)
                self.load(merged)
                self.load(l)
                self.instr("ldlen")
                self.instr("conv.i4")
                self.instr("callvirt instance void [mscorlib]System.Array::CopyTo(class [mscorlib]System.Array, int32)")
                self.load(merged)
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
            self.arrayLoad(node.list.inferredType.elementType)
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
        name = node.function.getCILName()
        if node.isConstructor:
            self.instr(f"newobj instance void [mscorlib]System.Object::.ctor()")
        elif name == "print":
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
            signature = node.function.inferredType.getCILSignature(f"{self.main}::{name}")
            self.instr(f"call {signature}")
            if node.function.inferredType.returnType.isNone():
                self.NoneLiteral(None)  # push null for void return

    def ForStmt(self, node: ForStmt):
        # itr = {expr}, idx = 0
        self.visit(node.iterable)
        itr = self.newLocal(None, node.iterable.inferredType)
        self.instr("ldc.i8 0")
        idx = self.newLocal(None, IntType())
        startLabel = self.newLabelName()
        endLabel = self.newLabelName()
        self.label(startLabel)
        # while idx < len(itr)
        self.load(idx)
        self.instr("conv.i4")
        self.load(itr)
        if node.iterable.inferredType.isListType():
            self.instr("ldlen")
        else:
            self.instr("callvirt instance int32 [mscorlib]System.String::get_Length()")
        self.instr("conv.i4")
        self.instr("clt")
        self.instr(f"brfalse {endLabel}")
        # x = itr[idx]
        self.load(itr)
        self.load(idx)
        self.instr("conv.i4")
        if node.iterable.inferredType.isListType():
            self.arrayLoad(node.iterable.inferredType.elementType)
        else:
            self.instr("call instance char [mscorlib]System.String::get_Chars(int32)")
            self.instr("ldc.i4.1")
            self.instr("newobj instance void [mscorlib]System.String::.ctor(char, int32)")
        if self.defaultToGlobals or node.identifier.varInstance.isGlobal:
            self.instr(
                f"stsfld {node.identifier.inferredType.getCILName()} {self.main}::{node.identifier.getCILName()}")
        else:
            self.store(node.identifier.getCILName())
        # body
        self.visitStmtList(node.body)
        # idx = idx + 1
        self.load(idx)
        self.instr("ldc.i8 1")
        self.instr("add")
        self.store(idx)
        self.instr(f"br {startLabel}")
        self.label(endLabel)


        

    def ListExpr(self, node: ListExpr):
        t = node.inferredType
        length = len(node.elements)
        self.instr(f"ldc.i4 {length}")
        elementType = None
        if isinstance(t, ClassValueType):
            if node.emptyListType:
                elementType = node.emptyListType
            else:
                elementType = ClassValueType("object")
        else:
            elementType = t.elementType
        self.instr(f"newarr {elementType.getCILName()}")
        for i in range(len(node.elements)):
            self.instr("dup")
            self.instr(f"ldc.i4 {i}")
            self.visit(node.elements[i])
            self.arrayStore(elementType)

    def WhileStmt(self, node: WhileStmt):
        startLabel = self.newLabelName()
        endLabel = self.newLabelName()
        self.label(startLabel)
        self.visit(node.condition)
        self.instr(f"brfalse {endLabel}")
        self.visitStmtList(node.body)
        self.instr(f"br {startLabel}")
        self.label(endLabel)

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
            self.instr(f"ldsfld {node.inferredType.getCILName()} {self.main}::{node.getCILName()}")
        elif node.varInstance.isNonlocal:
            raise Exception("unimplemented")
        else:
            self.load(node.getCILName())

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
        self.instr("call string [mscorlib]System.Console::ReadLine()")

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
        self.instr(f"call void class [mscorlib]System.Console::WriteLine({arg.inferredType.getCILName()})")
        self.NoneLiteral(None)

    def visitArg(self, funcType, paramIdx: int, arg: Expr):
        self.visit(arg)
        # TODO
