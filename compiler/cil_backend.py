from .astnodes import *
from .types import *
from .builder import Builder
from .typesystem import TypeSystem
from .visitor import CommonVisitor
from typing import List, Optional, cast, Callable
import json


class CilStackLoc:
    def __init__(self, name: str, loc: int, t: str, isArg: bool):
        self.name = name
        self.loc = loc
        self.isArg = isArg
        self.t = t

    def decl(self) -> str:
        return f"[{self.loc}] {self.t} {self.name}"


class CilBackend(CommonVisitor):
    stackLimit = 500
    defaultToGlobals = False  # treat all vars as global if this is true

    def __init__(self, main: str, ts: TypeSystem):
        self.builder = Builder(main)
        self.main = main  # name of main class
        self.ts = ts
        self.locals = []
        self.enterScope()

    def indent(self):
        self.instr("{")
        self.builder.indent()

    def unindent(self):
        self.builder.unindent()
        self.instr("}")

    def currentBuilder(self):
        return self.builder

    def newLabelName(self) -> str:
        self.counter += 1
        return "IL_" + str(self.counter)

    def label(self, name: str):
        self.builder.unindent()
        self.instr(name + ": nop")
        self.builder.indent()

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

    def loadVarAddr(self, node: Identifier):
        if self.defaultToGlobals or node.varInstanceX().isGlobal:
            self.instr(
                f"ldsflda {node.inferredValueType().getCILName()} {self.main}::{node.getCILName()}")
        elif self.isFromRefArg(node):
            self.load(node.name)
        else:
            self.loadAddr(node.name)

    def loadAddr(self, name: str):
        n = self.locals[-1][name]
        if n is None:
            raise Exception(
                f"Internal compiler error: unknown name {name} for load")
        if n.isArg:
            self.instr(f"ldarga {n.loc}")
        else:
            self.instr(f"ldloca {n.loc}")

    def loadInd(self, t: ValueType):
        if t == BoolType():
            self.instr("ldind.i4")
        elif t == IntType():
            self.instr("ldind.i8")
        else:
            self.instr("ldind.ref")

    def storeInd(self, t: ValueType):
        if t == BoolType():
            self.instr("stind.i4")
        elif t == IntType():
            self.instr("stind.i8")
        else:
            self.instr("stind.ref")

    def arrayStore(self, elementType: ValueType):
        self.instr(f"stelem {elementType.getCILName()}")

    def arrayLoad(self, elementType: ValueType):
        self.instr(f"ldelem {elementType.getCILName()}")

    def newLocalEntry(self, name: str, t: ValueType, isArg: bool = False) -> int:
        # add a new entry to locals table w/o storing anything
        n = len([k for k in self.locals[-1] if self.locals[-1][k].isArg == isArg])
        self.locals[-1][name] = CilStackLoc(name, n, t.getCILName(), isArg)
        return n

    def genLocalName(self, offset: int) -> str:
        return f"__local__{offset}"

    def newLocal(self, name: Optional[str], t: ValueType):
        # store the top of stack as a new local
        n = len([k for k in self.locals[-1] if not self.locals[-1][k].isArg])
        self.instr(f"stloc {n}")
        if name is None:
            name = self.genLocalName(n)
        self.locals[-1][name] = CilStackLoc(name, n, t.getCILName(), False)
        return name

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

        self.instr(f".assembly '{self.main}'")
        self.instr("{")
        self.instr("}")
        self.instr(f".module {self.main}.exe")
        self.instr(
            f".class public auto ansi beforefieldinit {self.main} extends [mscorlib]System.Object")
        self.indent()

        # global vars (static members)
        for v in var_decls:
            self.instr(
                f".field public static {v.var.getTypeX().getCILName()} {v.getIdentifier().getCILName()}")

        # main method, top level statements
        self.instr(
            ".method public static hidebysig default void Main (string[] args)  cil managed")
        self.indent()
        self.instr(".entrypoint")
        self.instr(f".maxstack {self.stackLimit}")
        locals = self.builder.newBlock()
        self.defaultToGlobals = True
        for v in var_decls:
            self.visit(v.value)
            self.instr(
                f"stsfld {v.var.getTypeX().getCILName()} {self.main}::{v.getIdentifier().getCILName()}")
        self.visitStmtList(node.statements)
        self.defaultToGlobals = False
        self.generateLocalsDirective(locals)
        self.instr("ret")
        self.unindent()  # end of main method

        # global functions (static funcs)
        for d in func_decls:
            self.visit(d)

        self.unindent()  # end of main class

        for c in cls_decls:
            self.visit(c)

    def ClassDef(self, node: ClassDef):
        def constructor(superclass: str, func: FuncDef):
            func.type = func.getTypeX().dropFirstParam()
            func.name.name = ".ctor"
            # add call to parent constructor after child field initialization
            # before other constructor statements
            self.FuncDef(func, "specialname rtspecialname instance",
                         node.superclass.getCILName())

        func_decls = [d for d in node.declarations if isinstance(d, FuncDef)]
        var_decls = [d for d in node.declarations if isinstance(d, VarDef)]
        clsName = node.name.getCILName()
        superclass = ClassValueType(node.superclass.getCILName()).getCILName()

        self.instr(
            f".class public auto ansi beforefieldinit {clsName} extends {superclass}")
        self.indent()

        constructor_def = None
        # field decls
        for v in var_decls:
            self.instr(
                f".field public {v.var.getTypeX().getCILName()} {v.getIdentifier().getCILName()}")
        for d in func_decls:
            if d.name.name == "__init__":
                # constructor
                constructor_def = d
                d.declarations = var_decls + d.declarations
                constructor(superclass, d)
            else:
                # method
                d.type = d.getTypeX().dropFirstParam()
                self.FuncDef(d, "virtual instance")
        if constructor_def is None:
            # give a default constructor if none exists
            funcDef = node.getDefaultConstructor()
            constructor(superclass, funcDef)

        self.unindent()  # end class

    def generateLocalsDirective(self, locals: Builder):
        # defer local declarations until we know what we need
        locals.newLine(".locals init (").indent()
        mapping = self.locals[-1]
        localDecls = [mapping[k] for k in mapping if not mapping[k].isArg]
        sortedDecls = sorted(localDecls, key=lambda x: x.loc)
        for i in range(len(sortedDecls)):
            comma = "," if i < len(sortedDecls) - 1 else ""
            locals.newLine(sortedDecls[i].decl() + comma)
        locals.unindent().newLine(")")

    def FuncDef(self, node: FuncDef, funcType: str = "static", superConstructor: Optional[str] = None):
        self.instr(f".method public hidebysig {funcType}")
        self.instr(
            f"{node.getTypeX().getCILSignature(node.name.getCILName())} cil managed")
        self.indent()
        self.instr(f".maxstack {self.stackLimit}")
        self.enterScope()

        # initialize locals
        locals = self.builder.newBlock()
        for i in range(len(node.params)):
            param = node.params[i]
            self.newLocalEntry(param.identifier.name, param.getTypeX(), True)
        for d in node.declarations:
            self.visit(d)
        # pyrefly: ignore [bad-assignment]
        self.returnType = node.getTypeX().returnType

        # handle last return
        if superConstructor:
            self.instr("ldarg.0")
            self.instr(f"call instance void {superConstructor}::.ctor()")
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
        if node.isAttr:
            # codegen for initialization in constructors
            assert node.attrOfClass is not None
            className = ClassValueType(node.attrOfClass)
            self.instr("ldarg 0")
            self.visit(node.value)
            self.instr(
                f"stfld {node.var.getTypeX().getCILName()} {className.getCILName()}::{node.getIdentifier().getCILName()}")
        else:
            self.visit(node.value)
            self.newLocal(node.getIdentifier().name, node.var.getTypeX())

    # STATEMENTS

    def processAssignmentTarget(self, target: Expr):
        if isinstance(target, Identifier):
            if self.defaultToGlobals or target.varInstanceX().isGlobal:
                self.instr(
                    f"stsfld {target.inferredValueType().getCILName()} {self.main}::{target.getCILName()}")
            elif self.isFromRefArg(target):
                temp = self.newLocal(None, target.inferredValueType())
                self.load(target.name)
                self.load(temp)
                self.storeInd(target.inferredValueType())
            else:
                self.store(target.name)
        elif isinstance(target, IndexExpr):
            temp = self.newLocal(None, target.inferredValueType())
            self.visit(target.list)
            self.visit(target.index)
            self.load(temp)
            self.arrayStore(target.inferredValueType())
        elif isinstance(target, MemberExpr):
            temp = self.newLocal(None, target.inferredValueType())
            self.visit(target.object)
            self.load(temp)
            self.instr(
                f"stfld {target.inferredValueType().getCILName()} {target.object.inferredValueType().getCILName()}::{target.member.getCILName()}")
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
        self.instr("pop")

    def isListConcat(self, operator: str, leftType: ValueType, rightType: ValueType) -> bool:
        return leftType.isListType() and rightType.isListType() and operator == "+"

    def BinaryExpr(self, node: BinaryExpr):
        operator = node.operator
        leftType = node.left.inferredValueType()
        rightType = node.right.inferredValueType()
        shortCircuitOperators = {"and", "or"}
        if operator not in shortCircuitOperators:
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
                merged_list = cast(ListValueType, self.ts.join(leftType, rightType))
                self.instr(f"newarr {merged_list.elementType.getCILName()}")
                merged = self.newLocal(None, merged_list)
                self.load(l)
                self.load(merged)
                self.instr("ldc.i4 0")
                self.instr(
                    "callvirt instance void [mscorlib]System.Array::CopyTo(class [mscorlib]System.Array, int32)")
                self.load(r)
                self.load(merged)
                self.load(l)
                self.instr("ldlen")
                self.instr("conv.i4")
                self.instr(
                    "callvirt instance void [mscorlib]System.Array::CopyTo(class [mscorlib]System.Array, int32)")
                self.load(merged)
            elif leftType == StrType():
                self.instr(
                    "call string [mscorlib]System.String::Concat(string, string)")
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
            b = self.newLocal(None, IntType())
            a = self.newLocal(None, IntType())
            # emulate Python modulo with ((a rem b) + b) rem b)
            self.load(a)
            self.load(b)
            self.instr("rem")
            self.load(b)
            self.instr("add.ovf")
            self.load(b)
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
                self.instr(
                    "call instance bool [mscorlib]System.String::Equals(string)")
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
            c = lambda: self.visit(node.left)
            t = lambda: self.visit(node.right)
            e = lambda: self.instr("ldc.i4.0")
            self.ternary(c, t, e)
        elif operator == "or":
            c = lambda: self.visit(node.left)
            t = lambda: self.instr("ldc.i4.1")
            e = lambda: self.visit(node.right)
            self.ternary(c, t, e)
        else:
            raise Exception(
                f"Internal compiler error: unexpected operator {operator}")

    def IndexExpr(self, node: IndexExpr):
        self.visit(node.list)
        self.visit(node.index)
        self.instr("conv.i4")
        t_list = node.list.inferredValueType()
        if isinstance(t_list, ListValueType):
            self.arrayLoad(t_list.elementType)
        else:
            self.instr(
                "call instance char [mscorlib]System.String::get_Chars(int32)")
            self.instr("ldc.i4.1")
            self.instr(
                "newobj instance void [mscorlib]System.String::.ctor(char, int32)")

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
            self.instr(
                f"newobj instance void {name}::.ctor()")
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
            assert isinstance(node.function.inferredType, FuncType)
            signature = node.function.inferredType.getCILSignature(
                f"{self.main}::{name}")
            self.instr(f"call {signature}")
            if node.function.inferredType.returnType.isNone():
                self.NoneLiteral(None)  # push null for void return

    def ForStmt(self, node: ForStmt):
        # itr = {expr}, idx = 0
        self.visit(node.iterable)
        itr = self.newLocal(None, node.iterable.inferredValueType())
        self.instr("ldc.i8 0")
        idx = self.newLocal(None, IntType())
        startLabel = self.newLabelName()
        endLabel = self.newLabelName()
        self.label(startLabel)
        # while idx < len(itr)
        self.load(idx)
        self.instr("conv.i4")
        self.load(itr)
        if isinstance(node.iterable.inferredType, ListValueType):
            self.instr("ldlen")
        else:
            self.instr(
                "callvirt instance int32 [mscorlib]System.String::get_Length()")
        self.instr("conv.i4")
        self.instr("clt")
        self.instr(f"brfalse {endLabel}")
        # x = itr[idx]
        self.load(itr)
        self.load(idx)
        self.instr("conv.i4")
        if isinstance(node.iterable.inferredType, ListValueType):
            self.arrayLoad(node.iterable.inferredType.elementType)
        else:
            self.instr(
                "call instance char [mscorlib]System.String::get_Chars(int32)")
            self.instr("ldc.i4.1")
            self.instr(
                "newobj instance void [mscorlib]System.String::.ctor(char, int32)")
        self.processAssignmentTarget(node.identifier)
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
            elementType = cast(ListValueType, t).elementType
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

    def buildReturn(self, value: Optional[Expr]):
        # pyrefly: ignore [missing-attribute]
        if not self.returnType.isNone():
            if value is None:
                self.NoneLiteral(None)
            else:
                self.visit(value)
        self.instr("ret")

    def ReturnStmt(self, node: ReturnStmt):
        self.buildReturn(node.value)

    def Identifier(self, node: Identifier):
        if self.defaultToGlobals or node.varInstanceX().isGlobal:
            self.instr(
                f"ldsfld {node.inferredValueType().getCILName()} {self.main}::{node.getCILName()}")
        elif self.isFromRefArg(node):
            self.load(node.name)
            self.loadInd(node.inferredValueType())
        else:
            self.load(node.name)

    def MemberExpr(self, node: MemberExpr):
        self.visit(node.object)
        self.instr(
            f"ldfld {node.inferredValueType().getCILName()} {node.object.inferredValueType().getCILName()}::{node.member.getCILName()}")

    def IfExpr(self, node: IfExpr):
        c = lambda: self.visit(node.condition)
        t = lambda: self.visit(node.thenExpr)
        e = lambda: self.visit(node.elseExpr)
        self.ternary(c, t, e)

    def ternary(self, condFn: Callable, thenFn: Callable, elseFn: Callable):
        condFn()
        l1 = self.newLabelName()
        l2 = self.newLabelName()
        self.instr(f"brtrue {l1}")
        elseFn()
        self.instr(f"br {l2}")
        self.label(l1)
        thenFn()
        self.label(l2)

    def MethodCallExpr(self, node: MethodCallExpr):
        assert isinstance(node.method.object.inferredType, ClassValueType)
        className = node.method.object.inferredType.className
        methodName = node.method.member.getCILName()
        if methodName == "__init__" and className in {"int", "bool"}:
            return
        self.visit(node.method.object)
        for i in range(len(node.args)):
            self.visitArg(node.method.inferredType, i + 1, node.args[i])
        assert isinstance(node.method.inferredType, FuncType)
        methodType = node.method.inferredType.dropFirstParam()
        signature = methodType.getCILSignature(
            f"{className}::{methodName}")
        self.instr(f"callvirt instance {signature}")
        if methodType.returnType.isNone():
            self.NoneLiteral(None)  # push null for void return

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        if node.value:
            self.instr("ldc.i4.1")
        else:
            self.instr("ldc.i4.0")

    def IntegerLiteral(self, node: IntegerLiteral):
        self.instr(f"ldc.i8 {node.value}")

    def NoneLiteral(self, node: Optional[NoneLiteral]):
        self.instr("ldnull")

    def StringLiteral(self, node: StringLiteral):
        self.instr(f"ldstr {json.dumps(node.value)}")

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
        self.instr(
            "newobj instance void [mscorlib]System.Exception::.ctor(string)")
        self.instr("throw")

    def emit_input(self):
        self.instr("call string [mscorlib]System.Console::ReadLine()")

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
                self.emit_exn("Built-in function len is unsupported for values of this type")
                return
        self.visit(arg)
        if is_list:
            self.instr("ldlen")
            self.instr("conv.i8")
        else:
            self.instr(
                "callvirt instance int32 [mscorlib]System.String::get_Length()")
            self.instr("conv.i8")

    def emit_print(self, arg: Expr):
        self.visit(arg)
        self.instr(
            f"call void class [mscorlib]System.Console::WriteLine({arg.inferredValueType().getCILName()})")
        self.NoneLiteral(None)

    def isFromRefArg(self, arg: Expr):
        if not isinstance(arg, Identifier):
            return False
        return self.isFromArg(arg) and arg.varInstanceX().isNonlocal

    def isFromArg(self, arg: Expr):
        if not isinstance(arg, Identifier):
            return False
        if arg.varInstanceX().isGlobal:
            return True
        n = self.locals[-1][arg.name]
        if n is None:
            raise Exception(
                f"Internal compiler error: unknown name {arg.name}")
        return n.isArg

    def visitArg(self, funcType, paramIdx: int, arg: Expr):
        argIsRef = self.isFromRefArg(arg)
        paramIsRef = paramIdx in funcType.refParams
        if argIsRef and paramIsRef and cast(Identifier, arg).varInstance == funcType.refParams[paramIdx]:
            # ref -> ref: pass through a ref to a nonlocal
            self.load(cast(Identifier, arg).name)
        elif paramIsRef and argIsRef:
            # ref -> ref:
            # deref, store value in new local, and pass ref to new local
            self.visit(arg)
            temp = self.newLocal(None, arg.inferredValueType())
            self.loadAddr(temp)
        elif paramIsRef:
            # value -> ref
            # store in new local, pass ref
            if isinstance(arg, Identifier) and not self.isFromArg(arg):
                self.loadVarAddr(arg)
            else:
                self.visit(arg)
                temp = self.newLocal(None, arg.inferredValueType())
                self.loadAddr(temp)
        else:
            # value/ref -> value : deref if necessary
            self.visit(arg)
