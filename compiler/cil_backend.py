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
        self.instr(name+":")
        self.currentBuilder().indent()

    def enterScope(self):
        self.locals.append(defaultdict(lambda: None))

    def exitScope(self):
        self.locals.pop()

    def returnInstr(self, exprType: ValueType):
        raise Exception("unimplemented")

    def wrap(self, val:Expr, elementType:ValueType):
        raise Exception("unimplemented")

    def store(self, name: str, t: ValueType):
        raise Exception("unimplemented")

    def load(self, name: str, t: ValueType):
        raise Exception("unimplemented")

    def arrayStore(self, elementType:ValueType):
        raise Exception("unimplemented")

    def arrayLoad(self, elementType:ValueType):
        raise Exception("unimplemented")

    def newLocalEntry(self, name: str) -> int:
        raise Exception("unimplemented")

    def genLocalName(self, offset: int) -> str:
        raise Exception("unimplemented")

    def newLocal(self, name: str = None, isRef: bool = True) -> int:
        raise Exception("unimplemented")

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
        self.instr(".method public static hidebysig default void Main (string[] args)  cil managed")
        self.indent()
        self.instr(".entrypoint")
        self.instr(f".maxstack {self.localLimit}")
        self.visitStmtList(node.statements)
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

    def AssignStmt(self, node: AssignStmt):
        raise Exception("unimplemented")

    def IfStmt(self, node: IfStmt):
        raise Exception("unimplemented")

    def ExprStmt(self, node: ExprStmt):
        self.visit(node.expr)
        # TODO

    def BinaryExpr(self, node: BinaryExpr):
        raise Exception("unimplemented")

    def IndexExpr(self, node: IndexExpr):
        raise Exception("unimplemented")

    def UnaryExpr(self, node: UnaryExpr):
        raise Exception("unimplemented")

    def CallExpr(self, node: CallExpr):
        # TODO
        for i in range(len(node.args)):
            self.visitArg(node.function.inferredType, i, node.args[i])
        self.instr("call void class [mscorlib]System.Console::WriteLine(string)")
        # raise Exception("unimplemented")

    def ForStmt(self, node: ForStmt):
        raise Exception("unimplemented")

    def ListExpr(self, node: ListExpr):
        raise Exception("unimplemented")

    def WhileStmt(self, node: WhileStmt):
        raise Exception("unimplemented")

    def ReturnStmt(self, node: ReturnStmt):
        raise Exception("unimplemented")

    def Identifier(self, node: Identifier):
        raise Exception("unimplemented")

    def MemberExpr(self, node: MemberExpr):
        raise Exception("unimplemented")
    
    def IfExpr(self, node: IfExpr):
        raise Exception("unimplemented")

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
        raise Exception("unimplemented")

    def emit_exn(self, msg: str):
        raise Exception("unimplemented")

    def emit_input(self):
        raise Exception("unimplemented")

    def emit_len(self, arg: Expr):
        raise Exception("unimplemented")

    def emit_print(self, arg: Expr):
        raise Exception("unimplemented")

    def visitArg(self, funcType, paramIdx: int, arg: Expr):
        self.visit(arg)
        # TODO
