from .astnodes import *
from .types import *
from .typesystem import TypeSystem
from .visitor import Visitor
from collections import defaultdict
from typing import List

import llvmlite.ir as ir
import llvmlite.binding as llvm

bool_t = ir.IntType(1)  # for booleans
int8_t = ir.IntType(8)  # chars
int32_t = ir.IntType(32)  # for ints
voidptr_t = ir.IntType(8).as_pointer()
jmp_buf_t = ir.ArrayType(ir.IntType(8), 100)


class LlvmBackend(Visitor):
    locals = []
    counter = 0
    globals = {}
    externs = {}

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
        # globals for commonly used strings
        self.globals = {
            'true': self.global_constant('true',
                                         ir.ArrayType(int8_t, 5),
                                         self.make_bytearray('True\00'.encode('ascii'))),
            'false': self.global_constant('false',
                                          ir.ArrayType(int8_t, 6),
                                          self.make_bytearray('False\00'.encode('ascii'))),
            'fmt_i': self.global_constant('fmt_i',
                                          ir.ArrayType(int8_t, 4),
                                          self.make_bytearray('%i\n\00'.encode('ascii'))),
            'fmt_s': self.global_constant('fmt_s',
                                          ir.ArrayType(int8_t, 4),
                                          self.make_bytearray('%s\n\00'.encode('ascii'))),
            'fmt_assert': self.global_constant('fmt_assert',
                                               ir.ArrayType(int8_t, 29),
                                               self.make_bytearray('Assertion failed on line %i\n\00'.encode('ascii'))),
            'fmt_err': self.global_constant('fmt_err',
                                            ir.ArrayType(int8_t, 18),
                                            self.make_bytearray('Error on line %i\n\00'.encode('ascii')))
        }

        printf_t = ir.FunctionType(int32_t, [voidptr_t], True)
        self.externs['printf'] = ir.Function(self.module, printf_t, 'printf')
        setjmp_t = ir.FunctionType(int32_t, [jmp_buf_t.as_pointer()])
        self.externs['setjmp'] = ir.Function(self.module, setjmp_t, 'setjmp')
        longjmp_t = ir.FunctionType(
            ir.VoidType(), [jmp_buf_t.as_pointer(), int32_t])
        self.externs['longjmp'] = ir.Function(
            self.module, longjmp_t, 'longjmp')
        strlen_t = ir.FunctionType(int32_t, [voidptr_t])
        self.externs['strlen'] = ir.Function(self.module, strlen_t, 'strlen')

        funcType = ir.FunctionType(ir.VoidType(), [])
        func = ir.Function(self.module, funcType, "__main__")

        self.enterScope()
        entry_block = func.append_basic_block('entry')
        self.builder = ir.IRBuilder(entry_block)

        jmp_buf = self.global_constant(
            "jmp_buf", jmp_buf_t, ir.Constant(jmp_buf_t, bytearray([0] * 100)))
        status = self.builder.call(self.externs['setjmp'], [jmp_buf])
        cond = self.builder.icmp_signed("!=", ir.Constant(int32_t, 0), status)

        error_block = self.builder.append_basic_block('error_handling')
        program_block = self.builder.append_basic_block('program_code')
        end_program = self.builder.append_basic_block('end_program')
        self.builder.cbranch(cond,
                             error_block,
                             program_block)

        self.builder.position_at_start(error_block)
        # if setjmp returns a positive status N, then a user-defined assertion failed on line N
        # if setjmp returns a negative status N, then a built-in invariant (such as a bounds check) failed on line -N
        self.ifHelper(lambda: self.builder.icmp_signed(
            '>', ir.Constant(int32_t, 0), status),
            lambda: self.printf(self.globals['fmt_assert'], status),
            lambda: self.printf(
                self.globals['fmt_err'], self.builder.neg(status))
        )

        self.builder.branch(end_program)
        error_block = self.builder.block

        self.builder.position_at_start(program_block)
        self.programHelper(node)

        self.builder.branch(end_program)
        program_block = self.builder.block
        self.builder.position_at_start(end_program)
        self.builder.ret_void()
        self.exitScope()

    def programHelper(self, node: Program):
        self.visitStmtList(
            [d for d in node.declarations if isinstance(d, VarDef)])
        self.visitStmtList(node.statements)

    def VarDef(self, node: VarDef):
        val = self.visit(node.value)
        saved_block = self.builder.block
        addr = self.create_entry_block_alloca(
            node.getName(), node.var.t.getLLVMType())
        self.builder.position_at_end(saved_block)
        self.builder.store(val, addr)
        self.locals[-1][node.getName()] = addr

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

    def AssignStmt(self, node: AssignStmt):
        val = self.visit(node.value)
        for var in node.targets[::-1]:
            if isinstance(var, MemberExpr):
                raise Exception("unimplemented")
            elif isinstance(var, IndexExpr):
                raise Exception("unimplemented")
            elif isinstance(var, Identifier):
                addr = self.locals[-1][var.name]
                self.builder.store(val, addr)
            else:
                raise Exception("Illegal assignment")

    def IfStmt(self, node: IfStmt):
        if len(node.elseBody) == 0:
            self.ifHelper(lambda: self.visit(node.condition), lambda: self.visitStmtList(
                node.thenBody))
        else:
            self.ifHelper(lambda: self.visit(node.condition), lambda: self.visitStmtList(
                node.thenBody), lambda: self.visitStmtList(node.elseBody))

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
            return self.builder.srem(lhs, rhs)
        # relational operators
        elif operator in {"<", "<=", ">", ">="}:
            return self.builder.icmp_signed(operator, lhs, rhs)
        elif operator == "==":
            if leftType == IntType():
                return self.builder.icmp_signed(operator, lhs, rhs)
            elif leftType == StrType():
                raise Exception("Unimplemented")
            else:
                return self.builder.icmp_signed(operator, lhs, rhs)
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
        if node.list.inferredType == StrType():
            string = self.visit(node.list)
            idx = self.visit(node.index)
            return self.strIndex(string, idx, True, node.index.location[0])
        else:
            raise Exception("unimplemented")

    def strIndex(self, string, index, check_bounds=False, line: int = 0):
        string = self.builder.bitcast(string, voidptr_t)
        # bounds checks
        # negate the line number for built-in checks
        if check_bounds:
            self.ifHelper(
                lambda: self.builder.icmp_signed(
                    '>', ir.Constant(int32_t, 0), index),
                lambda: self.longJmp(-line)
            )
            self.ifHelper(
                lambda: self.builder.icmp_signed('<=',
                                                 self.builder.call(
                                                     self.externs['strlen'], [string]),
                                                 index),
                lambda: self.longJmp(-line)
            )
        ptr = self.builder.gep(string, [index])
        char = self.builder.load(ptr)
        alloca = self.builder.alloca(ir.ArrayType(
            int8_t, 2), name=self.newLocal())
        alloca = self.builder.bitcast(alloca, voidptr_t)
        char_ptr = self.builder.gep(alloca, [ir.Constant(int32_t, 0)])
        self.builder.store(char, char_ptr, 8)
        t_ptr = self.builder.gep(alloca, [ir.Constant(int32_t, 1)])
        self.builder.store(ir.Constant(int8_t, 0), t_ptr, 8)
        return alloca

    def UnaryExpr(self, node: UnaryExpr):
        if node.operator == "-":
            val = self.visit(node.operand)
            return self.builder.neg(val)
        elif node.operator == "not":
            val = self.visit(node.operand)
            return self.builder.icmp_unsigned('==', ir.Constant(bool_t, 0), val)

    def CallExpr(self, node: CallExpr):
        if node.function.name == "print":
            self.emit_print(node.args[0])
            return
        if node.function.name == "__assert__":
            self.emit_assert(node.args[0])
            return
        if node.function.name == "len":
            return self.emit_len(node.args[0])
        callee_func = self.module.get_global(node.function.name)
        if callee_func is None or not isinstance(callee_func, ir.Function):
            raise Exception("unknown function")
        if len(callee_func.args) != len(node.args):
            raise Exception('Call argument length mismatch',
                            node.function.name)
        call_args = [self.visit(arg) for arg in node.args]
        return self.builder.call(callee_func, call_args, 'calltmp')

    def ForStmt(self, node: ForStmt):
        var = self.locals[-1][node.identifier.name]
        idx = self.builder.alloca(int32_t, None, 'idx')
        self.builder.store(ir.Constant(int32_t, 0), idx)
        iterable = self.visit(node.iterable)

        if node.iterable.inferredType == StrType():
            self.whileHelper(
                lambda: self.builder.icmp_signed("<",
                                                 self.builder.load(idx),
                                                 self.builder.call(self.externs['strlen'], [iterable])),
                lambda: self.forBody(node,
                                     var,
                                     lambda currIdx: self.strIndex(
                                         iterable, currIdx),
                                     idx))
        else:
            raise Exception("unimplemented")

    def forBody(self, node: ForStmt, var, idxFn, idx):
        currIdx = self.builder.load(idx)
        self.builder.store(idxFn(currIdx), var)
        self.visitStmtList(node.body)
        self.builder.store(self.builder.add(
            currIdx, ir.Constant(int32_t, 1)), idx)

    def ListExpr(self, node: ListExpr):
        pass

    def WhileStmt(self, node: WhileStmt):
        self.whileHelper(
            lambda: self.visit(node.condition),
            lambda: self.visitStmtList(node.body))

    def whileHelper(self, condFn, bodyFn):
        while_block = self.builder.append_basic_block('while')
        do_block = self.builder.append_basic_block('do')
        end_block = self.builder.append_basic_block('end')
        self.builder.branch(while_block)

        self.builder.position_at_start(while_block)
        cond = condFn()
        self.builder.cbranch(cond,
                             do_block,
                             end_block)
        while_block = self.builder.block

        self.builder.position_at_start(do_block)
        bodyFn()
        self.builder.branch(while_block)
        do_block = self.builder.block

        self.builder.position_at_start(end_block)

    def ReturnStmt(self, node: ReturnStmt):
        if self.returnType.isNone():
            self.builder.ret_void()
        else:
            val = None
            if node.value is None:
                val = self.NoneLiteral(None)
            else:
                val = self.visit(node.value)
            self.builder.ret(val)

    def Identifier(self, node: Identifier):
        addr = self.locals[-1][node.name]
        assert addr is not None
        return self.builder.load(addr, node.name)

    def MemberExpr(self, node: MemberExpr):
        pass

    def IfExpr(self, node: IfExpr):
        return self.ifHelper(lambda: self.visit(node.condition),
                             lambda: self.visit(node.thenExpr),
                             lambda: self.visit(node.elseExpr),
                             node.inferredType.getLLVMType())

    def ifHelper(self, condFn, thenFn, elseFn=None, returnType=None):
        cond = condFn()
        if returnType is not None:
            assert elseFn is not None

        then_block = self.builder.append_basic_block('then')
        if elseFn is not None:
            else_block = self.builder.append_basic_block('else')
        merge_block = self.builder.append_basic_block('merge')
        self.builder.cbranch(cond,
                             then_block,
                             else_block if elseFn is not None else merge_block)

        self.builder.position_at_start(then_block)
        then_val = thenFn()
        self.builder.branch(merge_block)
        then_block = self.builder.block

        if elseFn is not None:
            self.builder.position_at_start(else_block)
            else_val = elseFn()
            self.builder.branch(merge_block)
            else_block = self.builder.block

        self.builder.position_at_start(merge_block)

        if returnType is not None:
            phi = self.builder.phi(returnType, 'phi')
            phi.add_incoming(then_val, then_block)
            phi.add_incoming(else_val, else_block)
            return phi

    def MethodCallExpr(self, node: MethodCallExpr):
        pass

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        return ir.Constant(bool_t, 1 if node.value else 0)

    def IntegerLiteral(self, node: IntegerLiteral):
        return ir.Constant(int32_t, node.value)

    def NoneLiteral(self, node: NoneLiteral):
        return ir.Constant(ir.PointerType(None), None)

    def StringLiteral(self, node: StringLiteral):
        const = self.make_bytearray((node.value + '\00').encode('ascii'))
        alloca = self.builder.alloca(ir.ArrayType(
            int8_t, len(node.value) + 1), name=self.newLocal())
        self.builder.store(const, alloca)
        return self.builder.bitcast(alloca, voidptr_t)

    # BUILT-INS

    def emit_len(self, arg: Expr):
        if arg.inferredType == StrType():
            val = self.builder.bitcast(self.visit(arg), voidptr_t)
            return self.builder.call(self.externs['strlen'], [val])
        else:
            raise Exception("unimplemented")

    def emit_assert(self, arg: Expr):
        return self.ifHelper(
            lambda: self.builder.icmp_unsigned(
                '==', ir.Constant(bool_t, 0), self.visit(arg)),
            lambda: self.longJmp(arg.location[0])
        )

    def longJmp(self, line: int):
        jmp_buf = self.module.get_global("jmp_buf")
        self.builder.call(self.externs['longjmp'], [
                          jmp_buf, ir.Constant(int32_t, line)])

    def emit_print(self, arg: Expr):
        if isinstance(arg.inferredType, ListValueType) or arg.inferredType.className not in {"bool", "int", "str"}:
            raise Exception("Only bool, int, or str may be printed")
        if arg.inferredType.className == "bool":
            text = self.ifHelper(
                lambda: self.visit(arg),
                lambda: self.builder.bitcast(self.globals['true'], voidptr_t),
                lambda: self.builder.bitcast(self.globals['false'], voidptr_t),
                voidptr_t)
            return self.printf(self.globals['fmt_s'], text)
        elif arg.inferredType.className == 'int':
            return self.printf(self.globals['fmt_i'], self.visit(arg))
        else:
            return self.printf(self.globals['fmt_s'], self.visit(arg))

    # UTILS

    def make_bytearray(self, buf):
        b = bytearray(buf)
        n = len(b)
        return ir.Constant(ir.ArrayType(int8_t, n), b)

    def printf(self, format, arg):
        fmt_ptr = self.builder.bitcast(format, voidptr_t)
        return self.builder.call(self.externs['printf'], [fmt_ptr, arg])

    def create_entry_block_alloca(self, name, t):
        builder = ir.IRBuilder()
        builder.position_at_start(self.builder.function.entry_basic_block)
        return builder.alloca(t, size=None, name=name)

    def global_constant(self, name, t, value):
        module = self.module
        data = ir.GlobalVariable(module, t, name, 0)
        data.linkage = 'internal'
        data.global_constant = True
        data.initializer = value
        return data
