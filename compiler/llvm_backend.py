from .astnodes import *
from .types import *
from .typesystem import TypeSystem
from .visitor import Visitor
from collections import defaultdict
from typing import List
import json

import llvmlite.ir as ir
import llvmlite.binding as llvm

JMP_BUF_BYTES = 200

bool_t = ir.IntType(1)  # for booleans
int8_t = ir.IntType(8)  # chars, or booleans in arrays
int32_t = ir.IntType(32)  # for ints
voidptr_t = ir.IntType(8).as_pointer()
jmp_buf_t = ir.ArrayType(ir.IntType(8), JMP_BUF_BYTES)


class LlvmBackend(Visitor):
    locals = []
    counter = 0
    globals = {}
    externs = {}
    constructors = {}

    def __init__(self, ts: TypeSystem):
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        self.module = ir.Module()
        self.builder = None
        # (class name, method name) -> (idx in vtable, defining class name)
        self.methodOffsets = dict()
        self.ts = ts

    def initializeOffsets(self):
        tblOffset = 0
        methodTableOffsets = dict()
        # assign positions in the global method table
        classes = [c for c in self.ts.classes if c !=
                   "<None>" and c != "<Empty>"]
        for cls in classes:
            ctorType = ir.FunctionType(ir.VoidType(), [voidptr_t])
            ctor = ir.Function(self.module, ctorType, cls)
            self.constructors[cls] = ctor
            for methName, _, defCls in self.ts.getOrderedMethods(cls):
                if cls == defCls:
                    methodTableOffsets[(cls, methName)] = tblOffset
                    tblOffset += 1
        # calculate info for each class
        for cls in classes:
            methods = self.ts.getOrderedMethods(cls)
            for idx, methInfo in enumerate(methods):
                name, _, defCls = methInfo
                self.methodOffsets[(cls, name)] = (idx, defCls)

    def enterScope(self):
        self.locals.append(defaultdict(lambda: None))

    def exitScope(self):
        self.locals.pop()

    def visit(self, node: Node):
        return node.visit(self)

    def visitStmtList(self, stmts: List[Stmt]):
        for s in stmts:
            self.visit(s)

    # TOP LEVEL & DECLARATIONS

    def Program(self, node: Program):
        self.initializeOffsets()
        self.global_constant('__true',
                             ir.ArrayType(int8_t, 5),
                             self.make_bytearray('True\00'.encode('ascii')))
        self.global_constant('__false',
                             ir.ArrayType(int8_t, 6),
                             self.make_bytearray('False\00'.encode('ascii')))
        self.global_constant('__fmt_i',
                             ir.ArrayType(int8_t, 4),
                             self.make_bytearray('%i\n\00'.encode('ascii')))
        self.global_constant('__fmt_s',
                             ir.ArrayType(int8_t, 4),
                             self.make_bytearray('%s\n\00'.encode('ascii')))
        self.global_constant('__fmt_assert',
                             ir.ArrayType(int8_t, 29),
                             self.make_bytearray('Assertion failed on line %i\n\00'.encode('ascii')))
        self.global_constant('__fmt_err',
                             ir.ArrayType(int8_t, 18),
                             self.make_bytearray('Error on line %i\n\00'.encode('ascii')))
        self.global_constant('__fmt_str_concat',
                             ir.ArrayType(int8_t, 5),
                             self.make_bytearray('%s%s\00'.encode('ascii')))
        self.global_constant(
            "__jmp_buf", jmp_buf_t, ir.Constant(jmp_buf_t, bytearray([0] * JMP_BUF_BYTES)))

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

        sprintf_t = ir.FunctionType(voidptr_t, [voidptr_t, voidptr_t], True)
        self.externs['sprintf'] = ir.Function(
            self.module, sprintf_t, 'sprintf')

        malloc_t = ir.FunctionType(voidptr_t, [int32_t])
        self.externs['malloc'] = ir.Function(self.module, malloc_t, 'malloc')

        strcmp_t = ir.FunctionType(int32_t, [voidptr_t, voidptr_t])
        self.externs['strcmp'] = ir.Function(self.module, strcmp_t, 'strcmp')

        memcpy_t = ir.FunctionType(voidptr_t, [voidptr_t, voidptr_t, int32_t])
        self.externs['memcpy'] = ir.Function(self.module, memcpy_t, 'memcpy')

        # begin main function
        # declare global variables, methods, and functions
        varDefs = [d for d in node.declarations if isinstance(d, VarDef)]
        for d in varDefs:
            t = d.var.t.getLLVMType()
            self.global_variable(d.var.name(), t)
        funcDefs = [d for d in node.declarations if isinstance(d, FuncDef)]
        for d in funcDefs:
            self.declareFunc(d)
        classDefs = [d for d in node.declarations if isinstance(d, ClassDef)]
        for cls in classDefs:
            methodDefs = [d for d in cls.declarations if isinstance(d, FuncDef)]
            for m in methodDefs:
                if m.getIdentifier().name != "__init__":
                    raise Exception("TODO")
        # provide default __init__ impl for classes
        for cls in self.constructors:
            ctor = self.constructors[cls]
            if len(ctor.blocks) == 0:
                bb = ctor.append_basic_block('entry')
                ir.IRBuilder(bb).ret_void()

        # define functions
        for d in funcDefs:
            self.visit(d)

        # main function
        funcType = ir.FunctionType(ir.VoidType(), [])
        func = ir.Function(self.module, funcType, "__main__")

        self.enterScope()
        entry_block = func.append_basic_block('entry')
        self.builder = ir.IRBuilder(entry_block)

        status = self.builder.call(self.externs['setjmp'], [
                                   self.module.get_global('__jmp_buf')])
        cond = self.builder.icmp_signed("!=", int32_t(0), status)

        error_block = self.builder.append_basic_block('error_handling')
        program_block = self.builder.append_basic_block('program_code')
        end_program = self.builder.append_basic_block('end_program')
        self.builder.cbranch(cond,
                             error_block,
                             program_block)

        self.builder.position_at_start(error_block)
        self.printf(self.module.get_global('__fmt_err'), status)

        self.builder.branch(end_program)
        error_block = self.builder.block

        self.builder.position_at_start(program_block)
        # initialize globals
        for d in varDefs:
            val = self.visit(d.value)
            addr = self.module.get_global(d.var.name())
            assert addr is not None
            self.builder.store(val, addr)
        self.visitStmtList(node.statements)

        self.builder.branch(end_program)
        program_block = self.builder.block
        self.builder.position_at_start(end_program)
        self.builder.ret_void()
        self.exitScope()

    def VarDef(self, node: VarDef):
        val = self.visit(node.value)
        saved_block = self.builder.block
        addr = self.builder.alloca(
            node.var.t.getLLVMType(), None, node.getName())
        self.builder.position_at_end(saved_block)
        self.builder.store(val, addr)
        self.locals[-1][node.getName()] = addr

    def ClassDef(self, node: ClassDef):
        pass

    def declareFunc(self, node: FuncDef):
        self.returnType = node.type.returnType
        funcname = node.name.name
        returnType = node.type.returnType.getLLVMType()
        argTypes = [p.getLLVMType() for p in node.type.parameters]
        funcType = ir.FunctionType(returnType, argTypes)
        ir.Function(self.module, funcType, funcname)

    def FuncDef(self, node: FuncDef):
        # TODO - methods
        shouldReturnValue = not self.returnType.isNone()
        func = self.module.get_global(node.getIdentifier().name)
        self.returnType = node.type.returnType
        shouldReturnValue = not self.returnType.isNone()
        self.enterScope()
        bb_entry = func.append_basic_block('entry')
        self.builder = ir.IRBuilder(bb_entry)
        for i, arg in enumerate(func.args):
            arg.name = node.params[i].name()
            alloca = self.builder.alloca(
                node.type.parameters[i].getLLVMType(), name=arg.name)
            self.builder.store(arg, alloca)
            self.locals[-1][arg.name] = alloca
        for d in node.declarations:
            self.visit(d)
        self.visitStmtList(node.statements)
        # implicitly return None if possible
        if shouldReturnValue is not None and (
            len(node.statements) == 0 or
            not isinstance(node.statements[-1], ReturnStmt)
        ):
            self.builder.ret(self.NoneLiteral(None))
        self.exitScope()
        return func

    # STATEMENTS

    def AssignStmt(self, node: AssignStmt):
        val = self.visit(node.value)
        for var in node.targets[::-1]:
            if isinstance(var, MemberExpr):
                raise Exception("unimplemented")
            elif isinstance(var, IndexExpr):
                lst = self.visit(var.list)
                idx = self.visit(var.index)
                self.assert_nonnull(lst, var.list.location[0])
                ptr = self.listIndex(
                    lst, idx, var.inferredType.getLLVMType(), True, var.index.location[0])
                self.builder.store(val, ptr)
            elif isinstance(var, Identifier):
                addr = self.getAddr(var)
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

    def getListDataPtr(self, lst, elemType):
        lst = self.builder.bitcast(lst, int32_t.as_pointer())
        lst = self.builder.gep(lst, [int32_t(1)])
        return self.builder.bitcast(lst, elemType.as_pointer())

    def BinaryExpr(self, node: BinaryExpr):
        operator = node.operator
        leftType = node.left.inferredType
        rightType = node.right.inferredType
        lhs = self.visit(node.left)
        rhs = self.visit(node.right)
        # concatenation and addition
        if operator == "+":
            if self.isListConcat(operator, leftType, rightType):
                lhs = self.toVoidPtr(lhs)
                rhs = self.toVoidPtr(rhs)
                llen = self.list_len(lhs)
                rlen = self.list_len(rhs)
                total_len = self.builder.add(llen, rlen, 'total_len')
                if node.inferredType == EmptyType():
                    elemType = int8_t
                else:
                    elemType = node.inferredType.elementType.getLLVMType()
                assert elemType is not None
                size = self.builder.add(int32_t(4), self.builder.mul(
                    total_len, self.sizeof(elemType)), 'bytes')
                new_arr = self.builder.call(
                    self.externs['malloc'], [size], 'new_list')
                size_ptr = self.builder.bitcast(new_arr, int32_t.as_pointer())
                self.builder.store(total_len, size_ptr)

                data_lhs_start = self.getListDataPtr(new_arr, elemType)
                lhs_data = self.getListDataPtr(lhs, elemType)
                rhs_data = self.getListDataPtr(rhs, elemType)
                lhs_bytes = self.builder.mul(llen, self.sizeof(elemType))

                self.builder.call(self.externs['memcpy'], [
                    self.toVoidPtr(data_lhs_start), self.toVoidPtr(lhs_data), lhs_bytes])

                data_rhs_start = self.builder.gep(data_lhs_start, [llen])
                rhs_bytes = self.builder.mul(rlen, self.sizeof(elemType))

                self.builder.call(self.externs['memcpy'], [
                                  self.toVoidPtr(data_rhs_start), self.toVoidPtr(rhs_data), rhs_bytes])
                return new_arr
            elif leftType == StrType():
                lhs = self.toVoidPtr(lhs)
                rhs = self.toVoidPtr(rhs)
                llen = self.builder.call(self.externs['strlen'], [lhs])
                rlen = self.builder.call(self.externs['strlen'], [rhs])
                total_len = self.builder.add(self.builder.add(
                    llen, rlen), int32_t(1))
                new_str = self.builder.call(
                    self.externs['malloc'], [total_len], 'new_str')
                fmt = self.toVoidPtr(self.module.get_global('__fmt_str_concat'))
                self.builder.call(self.externs['sprintf'], [
                                  new_str, fmt, lhs, rhs])
                return new_str
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
                cmp = self.builder.call(self.externs['strcmp'], [lhs, rhs])
                return self.builder.icmp_signed("==", cmp, int32_t(0))
            else:
                # bool
                return self.builder.icmp_signed(operator, lhs, rhs)
        elif operator == "!=":
            if leftType == IntType():
                return self.builder.icmp_signed(operator, lhs, rhs)
            elif leftType == StrType():
                cmp = self.builder.call(self.externs['strcmp'], [lhs, rhs])
                return self.builder.icmp_signed("!=", cmp, int32_t(0))
            else:
                # bool
                return self.builder.icmp_signed(operator, lhs, rhs)
        elif operator == "is":
            # pointer comparisons
            return self.builder.icmp_unsigned("==",
                                              self.builder.ptrtoint(
                                                  lhs, int32_t),
                                              self.builder.ptrtoint(rhs, int32_t))
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
            lst = self.visit(node.list)
            idx = self.visit(node.index)
            self.assert_nonnull(lst, node.list.location[0])
            ptr = self.listIndex(lst, idx,
                                 node.inferredType.getLLVMType(),
                                 True, node.index.location[0])
            return self.builder.load(ptr)

    def listIndex(self, list, index, elemType, check_bounds=False, line: int = 0):
        # return pointer to list[index]
        length = self.list_len(list)
        if check_bounds:
            self.ifHelper(
                lambda: self.builder.icmp_signed(
                    '>', int32_t(0), index),
                lambda: self.longJmp(line)
            )
            self.ifHelper(
                lambda: self.builder.icmp_signed('<=',
                                                 length,
                                                 index),
                lambda: self.longJmp(line)
            )
        data = self.getListDataPtr(list, elemType)
        # return pointer to value in array
        return self.builder.gep(data, [index])

    def strIndex(self, string, index, check_bounds=False, line: int = 0):
        string = self.toVoidPtr(string)
        # bounds checks
        if check_bounds:
            self.ifHelper(
                lambda: self.builder.icmp_signed(
                    '>', int32_t(0), index),
                lambda: self.longJmp(line)
            )
            self.ifHelper(
                lambda: self.builder.icmp_signed('<=',
                                                 self.builder.call(
                                                     self.externs['strlen'], [string]),
                                                 index),
                lambda: self.longJmp(line)
            )
        ptr = self.builder.gep(string, [index])
        char = self.builder.load(ptr)
        addr = self.builder.call(self.externs['malloc'], [
                                 int32_t(2)], 'char')
        addr = self.toVoidPtr(addr)
        char_ptr = self.builder.gep(addr, [int32_t(0)])
        self.builder.store(char, char_ptr, 8)
        t_ptr = self.builder.gep(addr, [int32_t(1)])
        self.builder.store(int8_t(0), t_ptr, 8)
        return addr

    def UnaryExpr(self, node: UnaryExpr):
        if node.operator == "-":
            val = self.visit(node.operand)
            return self.builder.neg(val)
        elif node.operator == "not":
            val = self.visit(node.operand)
            return self.builder.icmp_unsigned('==', bool_t(0), val)

    def constructor(self, node: CallExpr):
        # TODO - calculate size
        obj = self.builder.call(self.externs['malloc'], [ir.Constant(int32_t, 1)], 'new_object')
        self.builder.call(self.constructors[node.function.name], [obj])
        return obj

    def CallExpr(self, node: CallExpr):
        if node.isConstructor:
            return self.constructor(node)
        elif node.function.name == "print":
            return self.emit_print(node.args[0])
        elif node.function.name == "__assert__":
            self.emit_assert(node.args[0])
            return
        elif node.function.name == "len":
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
        var = self.getAddr(node.identifier)
        idx_var = self.builder.alloca(int32_t, None, 'idx')
        self.builder.store(int32_t(0), idx_var)
        iterable = self.visit(node.iterable)

        if node.iterable.inferredType == StrType():
            self.whileHelper(
                lambda: self.builder.icmp_signed("<",
                                                 self.builder.load(idx_var),
                                                 self.builder.call(self.externs['strlen'], [iterable])),
                lambda: self.forBody(node,
                                     var,
                                     lambda currIdx: self.strIndex(
                                         iterable, currIdx),
                                     idx_var))
        else:
            self.assert_nonnull(iterable, node.iterable.location[0])
            length = self.list_len(iterable)
            self.whileHelper(
                lambda: self.builder.icmp_signed("<",
                                                 self.builder.load(idx_var),
                                                 length),
                lambda: self.forBody(node,
                                     var,
                                     lambda currIdx: self.builder.load(self.listIndex(
                                         iterable, currIdx, node.identifier.inferredType.getLLVMType())),
                                     idx_var))

    def forBody(self, node: ForStmt, var, idxFn, idx_var):
        currIdx = self.builder.load(idx_var)
        self.builder.store(idxFn(currIdx), var)
        self.visitStmtList(node.body)
        self.builder.store(self.builder.add(
            currIdx, int32_t(1)), idx_var)

    def ListExpr(self, node: ListExpr):
        n = len(node.elements)
        if n == 0:
            if node.emptyListType:
                elemType = node.emptyListType.getLLVMType()
            else:
                # fallback to voidptr
                elemType = int8_t
        else:
            elemType = node.inferredType.elementType.getLLVMType()
        assert elemType is not None
        size = self.builder.add(int32_t(4), self.builder.mul(
            int32_t(n), self.sizeof(elemType)))
        addr = self.builder.call(self.externs['malloc'], [
                                 size], 'list_literal')
        addr = self.builder.bitcast(addr, int32_t.as_pointer())
        for i in range(n):
            value = self.visit(node.elements[i])
            data = self.getListDataPtr(addr, elemType)
            idx_ptr = self.builder.gep(data, [int32_t(i)])
            self.builder.store(value, idx_ptr)
        len_ptr = self.builder.gep(
            addr, [int32_t(0)])
        self.builder.store(int32_t(n), len_ptr)
        addr = self.toVoidPtr(addr)
        return addr

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
        if not self.builder.block.is_terminated:
            self.builder.branch(while_block)
        do_block = self.builder.block

        self.builder.position_at_start(end_block)

    def ReturnStmt(self, node: ReturnStmt):
        if self.returnType.isNone():
            self.builder.ret(self.NoneLiteral(None))
        else:
            val = None
            if node.value is None:
                val = self.NoneLiteral(None)
            else:
                val = self.visit(node.value)
            self.builder.ret(val)

    def getAddr(self, node: Identifier):
        if node.varInstance.isGlobal:
            return self.module.get_global(node.name)
        elif node.varInstance.isNonlocal:
            raise Exception("unimplemented")
        else:
            addr = self.locals[-1][node.name]
            assert addr is not None
            return addr

    def Identifier(self, node: Identifier):
        addr = self.getAddr(node)
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
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_block)
        then_block = self.builder.block

        if elseFn is not None:
            self.builder.position_at_start(else_block)
            else_val = elseFn()
            if not self.builder.block.is_terminated:
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
        return bool_t(1 if node.value else 0)

    def IntegerLiteral(self, node: IntegerLiteral):
        return int32_t(node.value)

    def NoneLiteral(self, _: NoneLiteral):
        return voidptr_t(None)

    def StringLiteral(self, node: StringLiteral):
        bytes = bytearray((node.value + '\00').encode('ascii'))
        size = int32_t(1 + len(node.value))
        addr = self.builder.call(self.externs['malloc'], [size], 'str_literal')
        for i in range(len(bytes)):
            idx_ptr = self.builder.gep(addr, [int32_t(i)])
            self.builder.store(int8_t(bytes[i]), idx_ptr)
        return addr

    # BUILT-INS

    def emit_len(self, arg: Expr):
        val = self.visit(arg)
        if arg.inferredType == StrType():
            val = self.toVoidPtr(val)
            return self.builder.call(self.externs['strlen'], [val])
        else:
            return self.list_len(val)

    def assert_nonnull(self, val, line):
        val = self.toVoidPtr(val)
        self.ifHelper(
            lambda: self.builder.icmp_signed(
                '==', voidptr_t(None), val),
            lambda: self.longJmp(line)
        )

    def list_len(self, arg):
        val = self.builder.bitcast(arg, int32_t.as_pointer())
        return self.builder.load(val, 'len')

    def emit_assert(self, arg: Expr):
        line = arg.location[0]
        arg = self.visit(arg)
        return self.ifHelper(
            lambda: self.builder.icmp_unsigned(
                '==', bool_t(0), arg),
            lambda: self.longJmp(line)
        )

    def longJmp(self, line: int):
        jmp_buf = self.module.get_global('__jmp_buf')
        self.builder.call(self.externs['longjmp'], [
                          jmp_buf, int32_t(line)])

    def emit_print(self, arg: Expr):
        if isinstance(arg.inferredType, ListValueType) or arg.inferredType.className not in {"bool", "int", "str"}:
            raise Exception("Only bool, int, or str may be printed")
        if arg.inferredType == BoolType():
            text = self.ifHelper(
                lambda: self.visit(arg),
                lambda: self.toVoidPtr(self.module.get_global('__true')),
                lambda: self.toVoidPtr(self.module.get_global('__false')),
                voidptr_t)
            self.printf(self.module.get_global('__fmt_s'), text)
        elif arg.inferredType.className == 'int':
            self.printf(self.module.get_global('__fmt_i'), self.visit(arg))
        else:
            self.printf(self.module.get_global('__fmt_s'), self.visit(arg))
        return self.NoneLiteral(None)

    # UTILS

    def make_bytearray(self, buf):
        b = bytearray(buf)
        n = len(b)
        return ir.Constant(ir.ArrayType(int8_t, n), b)

    def printf(self, format, arg):
        fmt_ptr = self.toVoidPtr(format)
        return self.builder.call(self.externs['printf'], [fmt_ptr, arg])

    def global_constant(self, name, t, value):
        module = self.module
        data = ir.GlobalVariable(module, t, name)
        data.linkage = 'internal'
        data.global_constant = True
        data.initializer = value
        return data

    def global_variable(self, name, t):
        module = self.module
        data = ir.GlobalVariable(module, t, name)
        data.linkage = 'internal'
        data.initializer = t(None)
        data.global_constant = False
        return data

    def sizeof(self, t):
        if not t.is_pointer:
            width = t.width
            # each item in array must be at least 1 byte
            if width < 8:
                return int32_t(1)
            return int32_t(width // 8)
        else:
            null = t.as_pointer()(None)
            offset = null.gep([int32_t(1)])
            size = self.builder.ptrtoint(offset, int32_t, 'sizeof')
            return size

    def toVoidPtr(self, ptr):
        return self.builder.bitcast(ptr, voidptr_t)
