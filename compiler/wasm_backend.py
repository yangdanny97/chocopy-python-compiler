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

    def _if(self):
        self.newLine(f"(if")
        self.indent()

    def _then(self):
        self.newLine(f"(then")
        self.indent()

    def _else(self):
        self.newLine(f"(else")
        self.indent()

    def func(self, name: str, params: List[str] = [], resType=None) -> Builder:
        # return new block for declaring extra locals
        params = " ".join(params)
        result = ""
        if resType is not None:
            result = f" (result {resType})"
        self.newLine(f"(func ${name} {params}{result}")
        self.indent()
        return self.newBlock()

    def end(self):
        self.unindent()
        self.newLine(")")

    def emit(self) -> str:
        lines = []
        for l in self.lines:
            if isinstance(l, str):
                if " drop" in l and " i32.const 0" in lines[-1]:
                    lines[-1] = None
                    continue
                lines.append(l)
            else:
                lines.append(l.emit())
        lines = [l for l in lines if l is not None]
        return "\n".join(lines)

    def newBlock(self) -> Builder:
        child = WasmBuilder(self.name)
        child.indentation = self.indentation
        self.lines.append(child)
        return child


class WasmBackend(CommonVisitor):
    defaultToGlobals = False  # treat all vars as global if this is true
    localCounter = 0
    locals = None

    def __init__(self, main: str, ts: TypeSystem):
        self.builder = WasmBuilder(main)
        self.main = main  # name of main method
        self.ts = ts

    def currentBuilder(self):
        return self.classes[self.currentClass]

    def newLabelName(self) -> str:
        self.counter += 1
        return "label_"+str(self.counter)

    def instr(self, instr: str):
        self.builder.newLine(instr)

    def setLocal(self, name: str):
        self.instr(f"local.set ${name}")

    def teeLocal(self, name: str):
        self.instr(f"local.tee ${name}")

    def getLocal(self, name: str):
        self.instr(f"local.get ${name}")

    def genLocalName(self, suffix=None) -> str:
        self.localCounter += 1
        suffix = "" if suffix is None else ("_" + suffix)
        return f"local{suffix}{self.localCounter}"

    def newLocal(self, name: str = None, t: str = "i32") -> str:
        # add a new local decl, does not store anything
        if name is None:
            name = self.genLocalName()
        self.locals.newLine(f"(local ${name} {t})")
        return name

    def visitStmtList(self, stmts: List[Stmt]):
        if len(stmts) == 0:
            self.instr("nop")
        else:
            for s in stmts:
                self.visit(s)

    def alloc(self, local=None):
        # consume i32 from top of stack, allocate that many bytes
        self.instr("call $alloc")
        if local is not None:
            self.setLocal(local)

    def nullthrow(self):
        # throw if top of stack is 0, otherwise returns top of stack
        self.instr("call $nullthrow")

    def Program(self, node: Program):
        func_decls = [d for d in node.declarations if isinstance(d, FuncDef)]
        var_decls = [d for d in node.declarations if isinstance(d, VarDef)]
        self.builder.module()
        self.instr('(import "imports" "logInt" (func $log_int (param i64)))')
        self.instr('(import "imports" "logBool" (func $log_bool (param i32)))')
        self.instr('(import "imports" "logString" (func $log_str (param i32)))')
        self.instr('(import "imports" "assert" (func $assert (param i32)))')
        self.instr('(memory (import "js" "mem") 1)')
        self.instr(f"(global $heap (mut i32) (i32.const 4))")
        # initialize all globals to 0 for now, since we don't statically allocate strings or arrays
        for v in var_decls:
            self.instr(
                f"(global ${v.var.identifier.name} (mut {v.var.t.getWasmName()}) ({v.var.t.getWasmName()}.const 0))")
        for d in func_decls:
            self.visit(d)
        module_builder = self.builder
        self.builder = module_builder.newBlock()

        self.locals = self.builder.func("main")
        self.defaultToGlobals = True
        # initialize memory counter
        self.instr("i32.const 0")  # addr 0
        self.instr("i32.const 8")  # store value 8
        self.instr("i32.store")
        # initialize globals
        for v in var_decls:
            self.visit(v.value)
            self.instr(f"global.set ${v.getIdentifier().name}")
        self.visitStmtList(node.statements)
        self.defaultToGlobals = False
        self.builder.end()

        self.builder = module_builder
        self.instr(self.stdlib())
        self.instr(f"(start $main)")
        self.builder.end()

    def FuncDef(self, node: FuncDef):
        params = []
        for i in range(len(node.params)):
            params.append(node.params[i].getWasmParam(i, node.type))
        self.returnType = node.type.returnType
        ret = None if self.returnType.isNone() else self.returnType.getWasmName()
        self.locals = self.builder.func(node.name.name, params, ret)
        for d in node.declarations:
            self.visit(d)
        self.visitStmtList(node.statements)
        self.builder.end()

    def VarDef(self, node: VarDef):
        varName = node.var.identifier.name
        if node.isAttr:
            raise Exception("TODO")
        elif node.var.varInstance.isNonlocal:
            self.instr("i32.const 8")
            self.instr("call $alloc")
            addr = self.newLocal(varName)
            self.teeLocal(addr)
            self.visit(node.value)
            self.instr(f"{node.value.inferredType.getWasmName()}.store")
        else:
            self.visit(node.value)
            n = self.newLocal(varName, node.value.inferredType.getWasmName())
            self.setLocal(n)

    # # STATEMENTS

    def setIdentifier(self, target: Identifier, val: str):
        # val is the name of the local that the value is stored in
        if self.defaultToGlobals or target.varInstance.isGlobal:
            self.getLocal(val)
            self.instr(f"global.set ${target.name}")
        elif target.varInstance.isNonlocal:
            self.getLocal(target.name)
            self.getLocal(val)
            self.instr(f"{target.inferredType.getWasmName()}.store")
        else:
            self.getLocal(val)
            self.setLocal(target.name)

    def processAssignmentTarget(self, target: Expr, val: str):
        # val is the name of the local that the value is stored in
        if isinstance(target, Identifier):
            self.setIdentifier(target, val)
        elif isinstance(target, IndexExpr):
            self.visit(target.list)
            iterable = self.newLocal(self.genLocalName("iterable"))
            self.setLocal(iterable)
            idx = self.validateIdx(iterable, target)
            # 8 * idx + 4 + list addr
            self.getLocal(idx)
            self.instr("i32.const 8")
            self.instr("i32.mul")
            self.instr("i32.const 4")
            self.instr("i32.add")
            self.getLocal(iterable)
            self.instr("i32.add")
            self.getLocal(val)
            self.instr(f"{target.inferredType.getWasmName()}.store")
        elif isinstance(target, MemberExpr):
            raise Exception("TODO")
        else:
            raise Exception(
                "Internal compiler error: unsupported assignment target")

    def AssignStmt(self, node: AssignStmt):
        self.visit(node.value)
        val = self.newLocal(self.genLocalName(
            "val"), node.value.inferredType.getWasmName())
        self.setLocal(val)
        targets = node.targets[::-1]
        for t in targets:
            self.processAssignmentTarget(t, val)

    def IfStmt(self, node: IfStmt):
        self.visit(node.condition)
        self.builder._if()
        self.builder._then()
        self.visitStmtList(node.thenBody)
        self.builder.end()
        self.builder._else()
        self.visitStmtList(node.elseBody)
        self.builder.end()
        self.builder.end()

    def ExprStmt(self, node: ExprStmt):
        self.visit(node.expr)
        self.instr("drop")

    def isListConcat(self, operator: str, leftType: ValueType, rightType: ValueType) -> bool:
        return leftType.isListType() and rightType.isListType() and operator == "+"

    def loadChar(self, string: str, idx: str):
        self.getLocal(string)
        self.getLocal(idx)
        self.instr("call $get_char")

    def strCompare(self):
        self.instr("call $str_cmp")

    def strConcat(self):
        self.instr("call $str_concat")

    def listConcat(self):
        self.instr("call $list_concat")

    def BinaryExpr(self, node: BinaryExpr):
        operator = node.operator
        leftType = node.left.inferredType
        rightType = node.right.inferredType
        self.visit(node.left)
        self.visit(node.right)
        # concatenation and addition
        if operator == "+":
            if self.isListConcat(operator, leftType, rightType):
                self.listConcat()
            elif leftType == StrType():
                self.strConcat()
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
            if leftType == IntType():
                self.instr("i64.eq")
            elif leftType == StrType():
                self.strCompare()
            else:
                self.instr("i32.eq")
        elif operator == "!=":
            if leftType == IntType():
                self.instr("i64.ne")
            elif leftType == StrType():
                self.strCompare()
                self.instr("i32.eqz")
            else:
                self.instr("i32.ne")
        elif operator == "is":
            # pointer comparisons
            self.instr("i32.eq")
        # logical operators
        elif operator == "and":
            self.instr("i32.and")
        elif operator == "or":
            self.instr("i32.or")
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
            self.instr("i32.eqz")

    def CallExpr(self, node: CallExpr):
        name = node.function.name
        if node.isConstructor:
            raise Exception("TODO")
        if name == "print":
            self.emit_print(node.args[0])
        elif name == "len":
            self.emit_len(node.args[0])
        elif name == "input":
            raise Exception("TODO")
        elif name == "__assert__":
            self.emit_assert(node.args[0])
        else:
            for i in range(len(node.args)):
                self.visitArg(node.function.inferredType, i, node.args[i])
            self.instr(f"call ${name}")
            if node.function.inferredType.returnType.isNone():
                self.NoneLiteral(None)  # push null for void return

    def WhileStmt(self, node: WhileStmt):
        block = self.newLabelName()
        loop = self.newLabelName()
        self.builder.block(block)
        self.builder.loop(loop)
        self.visit(node.condition)
        self.instr(f"i32.eqz")
        self.instr(f"br_if ${block}")
        for s in node.body:
            self.visit(s)
        self.instr(f"br ${loop}")
        self.builder.end()
        self.builder.end()

    def ForStmt(self, node: ForStmt):
        block = self.newLabelName()
        loop = self.newLabelName()

        iterable = self.newLocal(self.genLocalName("iterable"))
        idx = self.newLocal(self.genLocalName("idx"))
        length = self.newLocal(self.genLocalName("length"))
        # this temporarily stores the current value
        temp = self.newLocal(self.genLocalName(
            "temp"), node.identifier.inferredType.getWasmName())

        self.visit(node.iterable)
        self.teeLocal(iterable)
        self.nullthrow()

        self.instr("i32.load")
        self.setLocal(length)

        # idx = 0
        self.instr("i32.const 0")
        self.setLocal(idx)

        self.builder.block(block)
        self.builder.loop(loop)

        # exit loop if idx >= length
        self.getLocal(idx)
        self.getLocal(length)
        self.instr("i32.lt_s")
        self.instr(f"i32.eqz")

        self.instr(f"br_if ${block}")

        isList = node.iterable.inferredType.isListType()
        contentsType = node.identifier.inferredType.getWasmName()
        self.idxHelper(iterable, idx, isList, contentsType)
        self.setLocal(temp)
        self.setIdentifier(node.identifier, temp)

        for s in node.body:
            self.visit(s)

        # idx += 1
        self.getLocal(idx)
        self.instr("i32.const 1")
        self.instr("i32.add")
        self.setLocal(idx)

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
            self.instr(f"local.get ${node.name}")
            self.instr(f"{node.inferredType.getWasmName()}.load")
        else:
            self.instr(f"local.get ${node.name}")

    def IfExpr(self, node: IfExpr):
        n = self.newLocal(self.genLocalName("ifexpr_result"),
                          node.inferredType.getWasmName())
        self.visit(node.condition)
        self.builder._if()
        self.builder._then()
        self.visit(node.thenExpr)
        self.setLocal(n)
        self.builder.end()
        self.builder._else()
        self.visit(node.elseExpr)
        self.setLocal(n)
        self.builder.end()
        self.builder.end()
        self.getLocal(n)

    def ListExpr(self, node: ListExpr):
        length = len(node.elements)
        t = node.inferredType
        elementType = None
        if isinstance(t, ClassValueType):
            if node.emptyListType:
                elementType = node.emptyListType
            else:
                elementType = ClassValueType("object")
        else:
            elementType = t.elementType

        # 8 bytes per element + 4 for the length, rounded up to nearest 8
        increase = (length + 1) * 8
        self.instr(f"i32.const {increase}")

        addr = self.newLocal(self.genLocalName("addr"))
        self.alloc(addr)

        # store the length
        self.getLocal(addr)
        self.instr(f"i32.const {length}")  # value
        self.instr(f"i32.store")  # alignment: 32-bit
        # unlike strings, each item in the list gets 64 bits instead of 8
        for i in range(length):
            offset = i * 8 + 4
            # addr: mem + 4 + idx * 8
            self.getLocal(addr)
            self.instr(f"i32.const {offset}")
            self.instr("i32.add")
            self.visit(node.elements[i])
            self.instr(f"{elementType.getWasmName()}.store")

        # load the address the list was stored at to the stack
        self.getLocal(addr)

    def validateIdx(self, iterable: str, node: IndexExpr):
        idx = self.newLocal(self.genLocalName("idx"))

        self.visit(node.index)
        self.instr("i32.wrap_i64")
        self.setLocal(idx)

        self.getLocal(iterable)
        self.getLocal(idx)
        self.instr("call $check_bounds")
        return idx

    def idxHelper(self, iterable: str, idx: str, isList: bool, contentsType: str):
        if isList:
            # 8 * idx + 4 + list addr
            self.getLocal(idx)
            self.instr("i32.const 8")
            self.instr("i32.mul")
            self.instr("i32.const 4")
            self.instr("i32.add")
            self.getLocal(iterable)
            self.instr("i32.add")
            self.instr(f"{contentsType}.load")
        else:  # must be a string, need to alloc a new string
            self.getLocal(iterable)
            self.getLocal(idx)
            self.instr("call $str_idx")

    def IndexExpr(self, node: IndexExpr):
        self.visit(node.list)
        iterable = self.newLocal(self.genLocalName("iterable"))
        self.setLocal(iterable)
        idx = self.validateIdx(iterable, node)
        self.idxHelper(iterable, idx, node.list.inferredType.isListType(),
                       node.inferredType.getWasmName())

    # # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        if node.value:
            self.instr(f"i32.const 1")
        else:
            self.instr(f"i32.const 0")

    def IntegerLiteral(self, node: IntegerLiteral):
        self.instr(f"i64.const {node.value}")

    def NoneLiteral(self, node: NoneLiteral):
        self.instr(f"i32.const 0")

    def StringLiteral(self, node: StringLiteral):
        length = len(node.value)
        memory = length + 4
        # 1 byte per char + 4 for length, rounded to nearest 8
        increase = 8 + (8 * (memory // 8))
        self.instr(f"i32.const {increase}")

        addr = self.newLocal(self.genLocalName("addr"))
        self.alloc(addr)

        # store the length
        self.getLocal(addr)
        self.instr(f"i32.const {length}")  # value
        self.instr(f"i32.store")
        for i in range(length):
            offset = i + 4
            val = ord(node.value[i])
            # addr: mem + 4 + idx
            self.getLocal(addr)
            self.instr(f"i32.const {offset}")
            self.instr("i32.add")
            self.instr(f"i32.const {val}")
            self.instr("i32.store8")

        # load the address the string was stored at to the stack
        self.getLocal(addr)

    def visitArg(self, funcType, paramIdx: int, arg: Expr):
        argIsRef = isinstance(arg, Identifier) and arg.varInstance.isNonlocal
        paramIsRef = paramIdx in funcType.refParams
        if argIsRef and paramIsRef and arg.varInstance == funcType.refParams[paramIdx]:
            # ref arg and ref param, pass ref arg
            self.getLocal(arg.name)
        elif paramIsRef:
            # non-ref arg and ref param, or do not pass ref arg
            # unwrap if necessary, re-wrap
            self.instr("i32.const 8")
            self.instr("call $alloc")
            addr = self.newLocal(self.genLocalName("arg_" + str(paramIdx)))
            self.teeLocal(addr)
            self.visit(arg)
            self.instr(f"{arg.inferredType.getWasmName()}.store")
            self.getLocal(addr)

        else:  # non-ref param, maybe unwrap
            self.visit(arg)

    # BUILT-INS
    def emit_assert(self, arg: Expr):
        self.visit(arg)
        self.instr("call $assert")
        self.NoneLiteral(None)

    def emit_print(self, arg: Expr):
        if isinstance(arg.inferredType, ListValueType) or arg.inferredType.className not in {"bool", "int", "str"}:
            raise Exception(
                f"Built-in function print is unsupported for values of type {arg.inferredType.classname}")
        self.visit(arg)
        self.instr(f"call $log_{arg.inferredType.className}")
        self.NoneLiteral(None)

    def emit_len(self, arg: Expr):
        # the length of a string or array is always in the first 4 bytes
        self.visit(arg)
        self.instr("call $len")
        self.instr("i64.extend_i32_u")

    def stdlib(self) -> str:
        return """
    ;; allocate and return addr of memory
    ;; based on https://github.com/ucsd-cse231-s22/chocopy-wasm-compiler-A/blob/2022/stdlib/memory.wat
    (func $alloc (param $bytes i32) (result i32)
        (local $addr i32)
        global.get $heap
        local.set $addr
        local.get $bytes
        global.get $heap
        i32.add
        global.set $heap
        local.get $addr
    )
    ;; copy $size bytes from $src to $dest
    ;; this just blindly copies memory and does not do any sort of validation/checks
    (func $mem_cpy (param $src i32) (param $dest i32) (param $size i32)
        (local $idx i32)
        (local $temp i32)
        i32.const 0
        local.set $idx
        (block $block
            (loop $loop
                local.get $idx
                local.get $size
                i32.lt_s
                i32.eqz
                br_if $block
                ;; read byte from $src + offset
                local.get $idx
                local.get $src
                i32.add
                i32.load8_u
                local.set $temp
                ;; write byte to $dest + offset
                local.get $idx
                local.get $dest
                i32.add
                local.get $temp
                i32.store8
                ;; increment offset
                local.get $idx
                i32.const 1
                i32.add
                local.set $idx
                br $loop
            )
        )
    )
    ;; return the length of a string or list as i32
    (func $len (param $addr i32) (result i32)
        local.get $addr
        call $nullthrow
        i32.load
    )
    ;; throw if $addr is null, otherwise return $addr
    (func $nullthrow (param $addr i32) (result i32)
        local.get $addr
        i32.eqz
        (if
            (then
                unreachable
            )
        )
        local.get $addr
    )
    ;; check the bounds of a string or list access, throwing if illegal
    (func $check_bounds (param $addr i32) (param $idx i32)
        local.get $addr
        call $len
        local.get $idx
        i32.gt_s
        i32.eqz
        (if
            (then
                unreachable
            )
        )
        i32.const 0
        local.get $idx
        i32.gt_s
        (if
            (then
                unreachable
            )
        )
    )
    ;; index a string, returning the character as an i32
    (func $get_char (param $addr i32) (param $idx i32) (result i32)
        local.get $addr
        i32.const 4
        i32.add
        local.get $idx
        i32.add
        i32.load8_u
    )
    ;; index a string, allocating a new string for the single character and returning the address
    (func $str_idx (param $addr i32) (param $idx i32) (result i32)
        (local $new i32)
        i32.const 8
        call $alloc
        local.set $new
        local.get $new
        i32.const 1
        i32.store
        local.get $new
        i32.const 4
        i32.add
        local.get $addr
        local.get $idx
        call $get_char
        i32.store8
        local.get $new
    )
    ;; concatenate two strings, returning the address of the new string
    (func $str_concat (param $s1 i32) (param $s2 i32) (result i32)
        (local $len1 i32)
        (local $len2 i32)
        (local $addr i32)
        ;; allocate memory
        local.get $s1
        call $len
        local.tee $len1
        local.get $s2
        call $len
        local.tee $len2
        i32.add
        i32.const 4
        i32.add
        i32.const 8
        i32.div_u
        i32.const 8
        i32.add
        call $alloc
        local.tee $addr
        ;; store length
        local.get $len1
        local.get $len2
        i32.add
        i32.store
        ;; copy string 1
        local.get $s1
        i32.const 4
        i32.add
        local.get $addr
        i32.const 4
        i32.add
        local.get $len1
        call $mem_cpy
        ;; copy string 2
        local.get $s2
        i32.const 4
        i32.add
        local.get $addr
        i32.const 4
        i32.add
        local.get $len1
        i32.add
        local.get $len2
        call $mem_cpy
        local.get $addr
    )
    ;; compare two strings, returning true if the two strings have the same contents
    (func $str_cmp (param $left i32) (param $right i32) (result i32)
        (local $result i32)
        (local $length i32)
        (local $idx i32)
        i32.const 1
        local.set $result
        local.get $left
        i32.load
        local.tee $length
        local.get $right
        i32.load
        i32.eq
        (if
            (then
                i32.const 0
                local.set $idx
                (block $block
                    (loop $loop
                        local.get $idx
                        local.get $length
                        i32.lt_s
                        i32.eqz
                        br_if $block
                        local.get $left
                        local.get $idx
                        call $get_char
                        local.get $right
                        local.get $idx
                        call $get_char
                        i32.eq
                        local.get $result
                        i32.and
                        local.set $result
                        local.get $result
                        i32.eqz
                        br_if $block
                        local.get $idx
                        i32.const 1
                        i32.add
                        local.set $idx
                        br $loop
                    )
                )
            )
            (else
                i32.const 0
                local.set $result
            )
        )
        local.get $result
    )
    ;; concatenate two lists, returning the address of the new list
    (func $list_concat (param $l1 i32) (param $l2 i32) (result i32)
        (local $len1 i32)
        (local $len2 i32)
        (local $addr i32)
        ;; allocate 8 * (len1 + len2 + 1) bytes
        local.get $l1
        call $len
        local.tee $len1
        local.get $l2
        call $len
        local.tee $len2
        i32.add
        i32.const 1
        i32.add
        i32.const 8
        i32.mul
        call $alloc
        local.tee $addr
        ;; store length
        local.get $len1
        local.get $len2
        i32.add
        i32.store
        ;; copy list 1
        local.get $l1
        i32.const 4
        i32.add
        local.get $addr
        i32.const 4
        i32.add
        local.get $len1
        i32.const 8
        i32.mul
        call $mem_cpy
        ;; copy list 2
        local.get $l2
        i32.const 4
        i32.add
        local.get $addr
        i32.const 4
        i32.add
        local.get $len1
        i32.const 8
        i32.mul
        i32.add
        local.get $len2
        i32.const 8
        i32.mul
        call $mem_cpy
        local.get $addr
    )
        """
