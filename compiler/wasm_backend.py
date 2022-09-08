from .astnodes import *
from .types import *
from .builder import Builder
from .typesystem import TypeSystem
from .visitor import CommonVisitor
from typing import List

class WasmBuilder(Builder):
    def __init__(self, name: str):
        super(WasmBuilder, self).__init__(name)
    
    def module(self):
        self.newLine("(module")
        self.indent()

    def block(self, name: str):
        self.newLine(f"(block ${name}")
        self.indent()

    def loop(self, name: str):
        self.newLine(f"(loop ${name}")
        self.indent()

    def param(self, name:str, type: str)->str:
        return f"(param ${name} {type})"

    def func(self, name:str, params: List[str]=[], resType=None):
        params = " ".join(params)
        result = ""
        if resType is not None:
            result = f" (result {resType})"
        self.newLine(f"(func ${name} {params}{result}")
        self.indent()

    def end(self):
        self.unindent()
        self.newLine(")")

class WasmBackend(CommonVisitor):
    defaultToGlobals = False  # treat all vars as global if this is true
    localCounter = 0

    def __init__(self, main: str, ts: TypeSystem):
        self.builder = WasmBuilder(main)
        self.main = main  # name of main method
        self.ts = ts
        self.enterScope()


    def currentBuilder(self):
        return self.classes[self.currentClass]

    def newLabelName(self) -> str:
        self.counter += 1
        return "label_"+str(self.counter)

    def instr(self, instr: str):
        self.builder.newLine(instr)

    def store(self, name: str):
        self.instr(f"local.set ${name}")

    def load(self, name: str):
        self.instr(f"local.get ${name}")

    def genLocalName(self) -> str:
        self.localCounter+=1
        return f"local_{self.localCounter}"

    def newLocal(self, name: str = None, t: str = "i64")->str:
        # store the top of stack as a new local
        if name is None:
            name = self.genLocalName()
        self.instr(f"(local ${name} {t})")
        self.store(name)
        return name

    def visitStmtList(self, stmts: List[Stmt]):
        if len(stmts) == 0:
            self.instr("nop")
        else:
            for s in stmts:
                self.visit(s)

    def Program(self, node: Program):
        func_decls = [d for d in node.declarations if isinstance(d, FuncDef)]
        var_decls = [d for d in node.declarations if isinstance(d, VarDef)]
        self.builder.module()
        self.instr('(import "console" "log" (func $log_int (param i64)))')
        self.instr('(import "console" "log" (func $log_bool (param i64)))')
        self.instr('(import "console" "assert" (func $assert (param i64)))')
        for v in var_decls:
            self.instr(f"(global ${v.var.identifier.name} {v.var.t.getWasmName()}")
            self.builder.indent()
            self.visit(v.value)
            self.builder.end()
        for d in func_decls:
            self.visit(d)
        self.builder.func("main")
        self.defaultToGlobals = True
        self.visitStmtList(node.statements)
        self.defaultToGlobals = False
        self.builder.end()
        self.instr(f"(start $main)")
        self.builder.end()

    def FuncDef(self, node: FuncDef):
        params = [self.builder.param(p.identifier.name, p.t.getWasmName()) for p in node.params]
        self.returnType = node.type.returnType
        ret = None if self.returnType.isNone() else self.returnType.getWasmName()
        self.builder.func(node.name.name, params, ret)
        for d in node.declarations:
            self.visit(d)
        self.visitStmtList(node.statements)
        self.builder.end()

    def VarDef(self, node: VarDef):
        varName = node.var.identifier.name
        if node.isAttr:
            raise Exception("TODO")
        elif node.var.varInstance.isNonlocal:
            raise Exception("TODO")
        else:
            self.visit(node.value)
            self.newLocal(varName, node.value.inferredType.getWasmName())

    # # STATEMENTS

    def processAssignmentTarget(self, target: Expr):
        if isinstance(target, Identifier):
            if self.defaultToGlobals or target.varInstance.isGlobal:
                self.instr(f"global.set ${target.name}")
            elif target.varInstance.isNonlocal:
                raise Exception("TODO")
            else:
                self.store(target.name)
        elif isinstance(target, IndexExpr):
            raise Exception("TODO")
        elif isinstance(target, MemberExpr):
            raise Exception("TODO")
        else:
            raise Exception(
                "Internal compiler error: unsupported assignment target")

    def AssignStmt(self, node: AssignStmt):
        self.visit(node.value)
        targets = node.targets[::-1]
        if len(targets) > 1:
            name = self.newLocal(None, node.value.inferredType.getWasmName())
            for t in targets:
                self.load(name)
                self.processAssignmentTarget(t)
        else:
            self.processAssignmentTarget(targets[0])

    def IfStmt(self, node: IfStmt):
        self.visit(node.condition)
        self.instr("(if")
        self.builder.indent()
        self.instr("(then")
        self.builder.indent()
        self.visitStmtList(node.thenBody)
        self.builder.end()
        self.instr("(else")
        self.builder.indent()
        self.visitStmtList(node.elseBody)
        self.builder.end()
        self.builder.end()

    def ExprStmt(self, node: ExprStmt):
        self.visit(node.expr)
        self.instr("drop")

    def isListConcat(self, operator: str, leftType: ValueType, rightType: ValueType) -> bool:
        return leftType.isListType() and rightType.isListType() and operator == "+"

    def BinaryExpr(self, node: BinaryExpr):
        operator = node.operator
        leftType = node.left.inferredType
        rightType = node.right.inferredType
        self.visit(node.left)
        self.visit(node.right)
        # concatenation and addition
        if operator == "+":
            if self.isListConcat(operator, leftType, rightType):
                raise Exception("TODO")
            elif leftType == StrType():
                raise Exception("TODO")
            elif leftType == IntType():
                self.instr("i64.add")
            else:
                raise Exception(
                    "Internal compiler error: unexpected operand types for +")
        # other arithmetic operators
        elif operator == "-":
            self.instr("i64.sub")
        elif operator == "*":
            self.instr("i64.mul")
        elif operator == "//":
            self.instr("i64.div_s")
        elif operator == "%":
            self.instr("i64.rem_s")
        # relational operators
        elif operator == "<":
            self.instr("i64.lt_s")
        elif operator == "<=":
            self.instr("i64.gt_s")
            self.instr("i64.eqz")
        elif operator == ">":
            self.instr("i64.gt_s")
        elif operator == ">=":
            self.instr("i64.lt_s")
            self.instr("i64.eqz")
        elif operator == "==":
            # TODO: refs
            self.instr("i64.eq")
        elif operator == "!=":
            self.instr("i64.ne")
        elif operator == "is":
            raise Exception("TODO")
        # logical operators
        elif operator == "and":
            self.instr("i64.and")
        elif operator == "or":
            self.instr("i64.or")
        else:
            raise Exception(
                f"Internal compiler error: unexpected operator {operator}")

    def UnaryExpr(self, node: UnaryExpr):
        if node.operator == "-":
            self.instr("i64.const 0")
            self.visit(node.operand)
            self.instr("i64.sub")
        elif node.operator == "not":
            self.visit(node.operand)
            self.instr("i64.eqz")

    def CallExpr(self, node: CallExpr):
        name = node.function.name
        if node.isConstructor:
            raise Exception("TODO")
        if name == "print":
            self.emit_print(node.args[0])
        elif name == "len":
            raise Exception("TODO")
        elif name == "input":
            raise Exception("TODO")
        elif name == "__assert__":
            self.emit_assert(node.args[0])
        else:
            for i in range(len(node.args)):
                self.visit(node.args[i])
            self.instr(f"call ${name}")
            if node.function.inferredType.returnType.isNone():
                self.NoneLiteral(None)  # push null for void return

    def WhileStmt(self, node: WhileStmt):
        block = self.newLabelName()
        loop = self.newLabelName()
        self.builder.block(block)
        self.builder.loop(loop)
        self.visit(node.condition)
        self.instr(f"i64.eqz")
        self.instr(f"br_if ${block}")
        for s in node.body:
            self.visit(s)
        self.instr(f"br ${loop}")
        self.builder.end()
        self.builder.end()

    def buildReturn(self, value: Expr):
        if self.returnType.isNone():
            self.instr("return")
        else:
            if value is None:
                self.NoneLiteral(None)
            else:
                self.visit(value)
            self.instr("return")

    def ReturnStmt(self, node: ReturnStmt):
        self.buildReturn(node.value)

    def Identifier(self, node: Identifier):
        if self.defaultToGlobals or node.varInstance.isGlobal:
            self.instr(f"global.get ${node.name}")
        elif node.varInstance.isNonlocal:
            raise Exception("TODO")
        else:
            self.instr(f"local.get ${node.name}")

    def IfExpr(self, node: IfExpr):
        self.visit(node.condition)
        self.instr("(if")
        self.builder.indent()
        self.instr("(then")
        self.builder.indent()
        self.visit(node.thenExpr)
        self.builder.end()
        self.instr("(else")
        self.builder.indent()
        self.visit(node.elseExpr)
        self.builder.end()
        self.builder.end()

    # # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        if node.value:
            self.instr(f"i64.const 1")
        else:
            self.instr(f"i64.const 0")

    def IntegerLiteral(self, node: IntegerLiteral):
        self.instr(f"i64.const f{node.value}")

    def NoneLiteral(self, node: NoneLiteral):
        self.instr(f"i64.const 0")

    # # BUILT-INS - note: these are in-lined
    def emit_assert(self, arg: Expr):
        self.visit(arg)
        self.instr("call $assert")
        self.instr("i64.const 0")

    def emit_print(self, arg: Expr):
        if isinstance(arg.inferredType, ListValueType) or arg.inferredType.className not in {"bool", "int", "str"}:
            raise Exception(f"Built-in function print is unsupported for values of type {arg.inferredType.classname}")
        self.visit(arg)
        self.instr(f"call $log_{arg.inferredType.className}")
        self.instr("i64.const 0")




