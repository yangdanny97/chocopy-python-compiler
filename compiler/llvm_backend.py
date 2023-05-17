from .astnodes import *
from .types import *
from .typesystem import TypeSystem
from .visitor import Visitor
from collections import defaultdict
from typing import List

import llvmlite.ir as ir
import llvmlite.binding as llvm


int8_t = ir.IntType(8)  # for booleans
int32_t = ir.IntType(32)  # for ints
voidptr_t = ir.IntType(8).as_pointer()


class LlvmBackend(Visitor):
    locals = []
    counter = 0

    def __init__(self, ts: TypeSystem):
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        self.module = ir.Module()
        self.builder = None

    def enterScope(self):
        self.locals.append(defaultdict(lambda: None))

    def exitScope(self):
        self.locals.pop()

    def visit(self, node: Node):
        return node.visit(self)

    def visitStmtList(self, stmts: List[Stmt]):
        for s in stmts:
            self.visit(s)

    def newLocal(self):
        self.counter += 1
        return f".local_{self.counter}"

    # TOP LEVEL & DECLARATIONS

    def Program(self, node: Program):
        funcType = ir.FunctionType(ir.VoidType(), [])
        func = ir.Function(self.module, funcType, "__main__")
        self.enterScope()
        bb_entry = func.append_basic_block('entry')
        self.builder = ir.IRBuilder(bb_entry)
        self.visitStmtList(node.statements)
        self.builder.ret_void()
        self.exitScope()

    def VarDef(self, node: VarDef):
        pass

    def ClassDef(self, node: ClassDef):
        pass

    def FuncDef(self, node: FuncDef):
        funcname = node.name
        returnType = node.type.returnType.getLLVMType()
        argTypes = [p.getLLVMType() for p in node.type.parameters]
        funcType = ir.FunctionType(returnType, argTypes)
        func = ir.Function(self.module, funcType, funcname)
        self.enterScope()
        bb_entry = func.append_basic_block('entry')
        self.builder = ir.IRBuilder(bb_entry)
        for i, arg in enumerate(func.args):
            arg.name = node.proto.argnames[i]
            alloca = self.builder.alloca(
                node.type.parameters[i].getLLVMType(), name=arg.name)
            self.builder.store(arg, alloca)
            self.locals[-1][arg.name] = alloca
        self.visitStmtList(node.statements)
        # self.builder.ret(retval)
        self.exitScope()
        return func

    # STATEMENTS

    def NonLocalDecl(self, node: NonLocalDecl):
        pass

    def GlobalDecl(self, node: GlobalDecl):
        pass

    def AssignStmt(self, node: AssignStmt):
        pass

    def IfStmt(self, node: IfStmt):
        pass

    def ExprStmt(self, node: ExprStmt):
        self.visit(node.expr)

    def isListConcat(self, operator: str, leftType: ValueType, rightType: ValueType) -> bool:
        return leftType.isListType() and rightType.isListType() and operator == "+"

    def BinaryExpr(self, node: BinaryExpr):
        operator = node.operator
        leftType = node.left.inferredType
        rightType = node.right.inferredType
        lhs = self.visit(node.left)
        rhs = self.visit(node.right)
        # concatenation and addition
        if operator == "+":
            if self.isListConcat(operator, leftType, rightType):
                raise Exception("unimplemented")
            elif leftType == StrType():
                raise Exception("unimplemented")
            elif leftType == IntType():
                return self.builder.add(lhs, rhs)
            else:
                raise Exception(
                    "Internal compiler error: unexpected operand types for +")
        # other arithmetic operators
        elif operator == "-":
            return self.builder.sub(lhs, rhs)
        elif operator == "*":
            return self.builder.mul(lhs, rhs)
        elif operator == "//":
            return self.builder.sdiv(lhs, rhs)
        elif operator == "%":
            return self.builder.urem(lhs, rhs)
        # relational operators
        elif operator in {"<", "<=", ">", ">="}:
            return self.builder.icmp_signed(operator, lhs, rhs)
        elif operator == "==":
            if leftType == IntType():
                return self.builder.icmp_signed(operator, lhs, rhs)
            elif leftType == StrType():
                raise Exception("Unimplemented")
            else:
                return self.instr("i32.eq")
        elif operator == "!=":
            if leftType == IntType():
                return self.builder.icmp_signed(operator, lhs, rhs)
            elif leftType == StrType():
                raise Exception("Unimplemented")
            else:
                # pointer comparisons
                return self.builder.icmp_unsigned(operator, lhs, rhs)
        elif operator == "is":
            # pointer comparisons
            return self.builder.icmp_unsigned("==", lhs, rhs)
        # logical operators
        elif operator == "and":
            return self.builder.and_(lhs, rhs)
        elif operator == "or":
            return self.builder.or_(lhs, rhs)
        else:
            raise Exception(
                f"Internal compiler error: unexpected operator {operator}")

    def IndexExpr(self, node: IndexExpr):
        pass

    def UnaryExpr(self, node: UnaryExpr):
        if node.operator == "-":
            val = self.visit(node.operand)
            return self.builder.neg(val)
        elif node.operator == "not":
            false = ir.Constant(int8_t, 0)
            val = self.visit(node.operand)
            return self.builder.icmp_unsigned('==', false, val)

    def CallExpr(self, node: CallExpr):
        if node.function.name == "print":
            self.emit_print(node.args[0])
            return
        callee_func = self.module.get_global(node.function.name)
        if callee_func is None or not isinstance(callee_func, ir.Function):
            raise Exception("unknown function")
        if len(callee_func.args) != len(node.args):
            raise Exception('Call argument length mismatch',
                            node.function.name)
        call_args = [self.visit(arg) for arg in node.args]
        return self.builder.call(callee_func, call_args, 'calltmp')

    def ForStmt(self, node: ForStmt):
        pass

    def ListExpr(self, node: ListExpr):
        pass

    def WhileStmt(self, node: WhileStmt):
        pass

    def ReturnStmt(self, node: ReturnStmt):
        pass

    def Identifier(self, node: Identifier):
        addr = self.locals[-1][node.name]
        return self.builder.load(addr, node.name)

    def MemberExpr(self, node: MemberExpr):
        pass

    def IfExpr(self, node: IfExpr):
        pass

    def MethodCallExpr(self, node: MethodCallExpr):
        pass

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        return ir.Constant(int8_t, 1 if node.value else 0)

    def IntegerLiteral(self, node: IntegerLiteral):
        return ir.Constant(int32_t, node.value)

    def NoneLiteral(self, node: NoneLiteral):
        return ir.Constant(int32_t, 0)

    def StringLiteral(self, node: StringLiteral):
        const = self.make_bytearray((node.value + '\00').encode('ascii'))
        alloca = self.builder.alloca(ir.ArrayType(int8_t, len(node.value) + 1), name=self.newLocal())
        self.builder.store(const, alloca)
        return alloca

    # TYPES

    def TypedVar(self, node: TypedVar):
        pass

    def ListType(self, node: ListType):
        pass

    def ClassType(self, node: ClassType):
        pass

    # BUILT-INS

    def emit_print(self, arg: Expr):
        if isinstance(arg.inferredType, ListValueType) or arg.inferredType.className not in {"bool", "int", "str"}:
            raise Exception("unsupported")
        if arg.inferredType.className == "bool":
            raise Exception("TODO")
        elif arg.inferredType.className == 'int':
            return self.printf("%i\n", False, self.visit(arg))
        else:
            return self.printf("%s\n", True, self.visit(arg))

    # UTILS

    def make_bytearray(self, buf):
        b = bytearray(buf)
        n = len(b)
        return ir.Constant(ir.ArrayType(int8_t, n), b)

    def is_null(self, value):
        return self.builder.icmp_unsigned('==', value.type(None), value)

    def is_nonnull(self, value):
        return self.builder.icmp_unsigned('!=', value.type(None), value)

    def printf(self, format: str, cast: bool, arg):
        func_t = ir.FunctionType(int32_t, [voidptr_t], True)
        fmt_bytes = self.make_bytearray((format + '\00').encode('ascii'))
        alloca = self.builder.alloca(ir.ArrayType(int8_t, 4), name=self.newLocal())
        self.builder.store(fmt_bytes, alloca)
        try:
            fn = self.module.get_global('printf')
        except KeyError:
            fn = ir.Function(self.module, func_t, 'printf')
        fmt_ptr = self.builder.bitcast(alloca, voidptr_t)
        if cast:
            arg = self.builder.bitcast(arg, voidptr_t)
        return self.builder.call(fn, [fmt_ptr, arg])
