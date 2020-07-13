from .astnodes import *
from .types import *
from collections import defaultdict
from .typechecker import TypeChecker
from .visitor import Visitor
from .typesystem import TypeSystem
from llvmlite import ir, binding

class LLVMTranslator(Visitor):
    def __init__(self, name: str, ts: TypeSystem):
        self.ts = ts

        self.binding = binding
        self.binding.initialize()
        self.binding.initialize_native_target()
        self.binding.initialize_native_asmprinter()

        self.module = ir.Module(name)
        self.module.triple = binding.get_default_triple()

        self.INT_TYPE = ir.IntType(64)
        self.BOOL_TYPE = ir.BoolType(64)

        self.classTypes = defaultdict(lambda: None)
        # strings are variable-length arrays of i8
        strType = self.module.context.get_identified_type("str")
        strType.set_body([ir.IntType(64), ir.ArrayType(ir.IntType(8), 0)])
        self.classTypes["str"] = strType

        # object is empty struct
        objType = self.module.context.get_identified_type("object")
        objType.set_body([])
        self.classTypes["object"] = objType

        self.builder = ir.IRBuilder()
        self.function = None
        self.currentClass = None  # name of current class
        self.expReturnType = None  # expected return type of current function

        self.setupClasses()

        # map variable names to llvm ptr values
        self.symboltable = [defaultdict(lambda: None)]

    # set up standard library functions

    def stdPrint(self):
        # need different prints for different types
        raise NotImplementedError

    def stdLen(self):
        raise NotImplementedError

    def stdInput(self):
        raise NotImplementedError

    # utils

    def setupClasses(self):
        # set up struct types for each class
        exclude = {"str", "object", "int", "bool", "<Empty>", "<None>"}
        for c in self.ts.classes:
            if c not in exclude:
                attrs = self.ts.getOrderedAttrs(c)
                attrTypes = [self.typeToLLVM(x[1], True) for x in attrs]
                typ = self.module.context.get_identified_type(c)
                typ.set_body(attrTypes)
                self.classTypes[c] = typ

    # convert Chocopy type to LLVM type, with
    # optional flag to return in pointer form for classes & lists
    def typeToLLVM(self, t, aspointer=False):
        if isinstance(t, ClassValueType):
            if t == ts.INT_TYPE:
                return self.INT_TYPE
            if t == ts.BOOL_TYPE:
                return self.BOOL_TYPE
            if t == ts.EMPTY_TYPE:  # pointer to empty list
                return self.typeToLLVM(ListValueType(ClassValueType("object")), True)
            if t == ts.NONE_TYPE:  # null pointer
                return self.module.context.get_identified_type("object").as_pointer()
            typ = self.module.context.get_identified_type(t.className)
            return typ.as_pointer() if aspointer else typ
        elif isinstance(t, ListValueType):
            elementType = self.typeToLLVM(t.elementType)
            typ = ir.LiteralStructType(self.module.context,
                                       [ir.IntType(64), ir.ArrayType(ir.IntType(8), 0)])
            return typ.as_pointer() if aspointer else typ
        elif isinstance(t, FuncType):
            parameters = [self.typeToLLVM(x, True) for x in t.parameters]
            returnType = self.typeToLLVM(t.returnType, True)
            return ir.FunctionType(returnType, parameters)

    def deref(self, ptr):
        if isinstance(ptr.type, ir.PointerType):
            return self.builder.load(ptr)
        return ptr

    # TOP LEVEL & DECLARATIONS

    def Program(self, node: Program):
        for d in node.declarations:
            if isinstance(d, VarDef):
                self.GlobalVarDef(d)
            else:
                self.visit(d)
        # create "main" function
        mainFunc = FuncDef([], Identifier([], "main"), [], ClassType([], "None"), [], node.statements)
        self.visit(mainFunc)

    def GlobalVarDef(self, node):
        value = self.visit(node.value)
        t = None
        if node.value.inferredType in ["int", "bool"]: 
            t = self.typeToLLVM(node.var.t, False)
        else: 
            t = self.typeToLLVM(node.var.t, True)
        ptr = ir.GlobalVariable(self.module, t)
        self.builder.store(value, ptr)
        self.symboltable[-1][node.getIdentifier().name] = ptr

    def VarDef(self, node: VarDef):
        value = self.visit(node.value)
        t = None
        if node.value.inferredType in ["int", "bool"]: 
            t = self.typeToLLVM(node.var.t, False)
        else: 
            t = self.typeToLLVM(node.var.t, True)
        ptr = self.builder.alloca(t)
        self.builder.store(value, ptr)
        self.symboltable[-1][node.getIdentifier().name] = ptr

    def ClassDef(self, node: ClassDef):
        raise NotImplementedError

    def FuncDef(self, node: FuncDef):
        raise NotImplementedError

    # STATEMENTS & EXPRESSIONS

    def ExprStmt(self, node: ExprStmt):
        self.visit(node.expr)

    def AssignStmt(self, node: AssignStmt):
        value = self.visit(node.value)
        for t in node.targets:
            if isinstance(t, Identifier):
                ptr = self.visit(t)
                if node.value.inferredType in ["int", "bool"]: 
                    # deref and store primitives
                    value = self.deref(value)
                    self.builder.store(value, ptr)
                else: 
                    # aliasing
                    self.builder.store(value, ptr)
                    self.symboltable[-1][t.name] = value
            elif isinstance(t, IndexExpr):
                raise NotImplementedError
            elif isinstance(t, MemberExpr):
                raise NotImplementedError

    def IfStmt(self, node: IfStmt):
        pred = self.deref(self.visit(node.condition))
        if len(node.elseBody) == 0:
            with self.builder.if_then(pred) as then:
                with then:
                    for s in node.thenBody:
                        self.visit(s)
        else:
            with self.builder.if_else(pred) as (then, otherwise):
                with then:
                    for s in node.thenBody:
                        self.visit(s)
                with otherwise:
                    for s in node.elseBody:
                        self.visit(s)

    def BinaryExpr(self, node: BinaryExpr):
        left = self.visit(node.left)
        right = self.visit(node.right)
        leftType = node.left.inferredType
        rightType = node.right.inferredType

        deref = True
        if operator == "is":
            deref = False
        elif operator in ["==", "!="]:
            if leftType.name not in ["int", "bool", "str"]:
                deref = False

        if deref:
            left = self.deref(left)
            right = self.deref(right)

        # concatenation and addition
        if operator == "+":
            if isinstance(leftType, ListValueType) and isinstance(rightType, ListValueType):
                raise NotImplementedError  # TODO list concat
            elif leftType == StrType() and rightType == StrType():
                raise NotImplementedError  # TODO concat
            elif leftType == IntType() and rightType == IntType():
                return self.builder.add(left, right)
        elif operator == "-":
            return self.builder.sub(left, right)
        elif operator == "*":
            return self.builder.mul(left, right)
        elif operator == "//":
            return self.builder.sdiv(left, right)
        elif operator == "%":
            return self.builder.srem(left, right)
        elif operator == "<":
            return self.builder.icmp_signed("<", left, right)
        elif operator == "<=":
            return self.builder.icmp_signed("<=", left, right)
        elif operator == ">":
            return self.builder.icmp_signed(">", left, right)
        elif operator == ">=":
            return self.builder.icmp_signed(">=", left, right)
        elif operator == "==":
            if leftType == StrType() and rightType == StrType():
                raise NotImplementedError
            # TODO string equality
            return self.builder.icmp_signed("==", left, right)
        elif operator == "!=":
            if leftType == StrType() and rightType == StrType():
                raise NotImplementedError
            # TODO string equality
            return self.builder.icmp_signed("!=", left, right)
        elif operator == "is":
            # convert pointers to ints & compare
            return self.builder.icmp_unsigned("==",
                                              self.builder.ptrtoint(
                                                  left, self.INT_TYPE),
                                              self.builder.ptrtoint(right, self.INT_TYPE))
        elif operator == "and":
            return self.builder.and_(left, right)
        elif operator == "or":
            return self.builder.or_(left, right)

    def IndexExpr(self, node: IndexExpr):
        lst = self.visit(node.list)
        index = self.deref(self.visit(node.index))
        values = self.builder.gep(lst, [ir.Constant(self.INT_TYPE, 1)])
        value = self.builder.gep(values, [index])
        return self.builder.load(value)

    def UnaryExpr(self, node: UnaryExpr):
        operand = self.visit(node.operand)
        if node.operator == "-":
            return self.builder.neg(operand)
        elif node.operator == "not":
            return self.builder.not_(operand)

    def CallExpr(self, node: CallExpr):
        args = [self.visit(x) for x in node.args]
        name = node.function.name
        if name == "print":
            raise NotImplementedError
        elif name == "len":
            lst = self.visit(node.args[0])
            self.deref(self.builder.gep(lst, [ir.Constant(self.INT_TYPE, 0)]))
        elif name == "input":
            raise NotImplementedError
        else:
            func = self.module.get_global(name)
            self.builder.call(func, args)

    def ForStmt(self, node: ForStmt):
        raise NotImplementedError

    def ListExpr(self, node: ListExpr):
        raise NotImplementedError

    def WhileStmt(self, node: WhileStmt):
        # loop construction referenced from: http://dev.stephendiehl.com/numpile/
        test_block = self.function.append_basic_block('while.cond')
        body_block = self.function.append_basic_block('while.body')
        end_block = self.function.append_basic_block("while.end")

        # Setup the loop condition
        self.builder.branch(test_block)
        self.builder.position_at_end(test_block)
        cond = self.deref(self.visit(node.condition))
        self.builder.cbranch(cond, body_block, end_block)

        # Generate the loop body
        self.builder.position_at_end(test_block)
        map(self.visit, node.body)

        # Exit the loop
        self.builder.branch(test_block)
        self.builder.position_at_end(end_block)

    def ReturnStmt(self, node: ReturnStmt):
        if node.value is None or isinstance(node.value, NoneLiteral):
            if isinstance(self.expReturnType, ir.VoidType):
                self.builder.ret_void()
            else:
                self.builder.ret(ir.Constant(
                    self.expReturnType.as_pointer(), None))
        else:
            val = self.visit(node.value)
            self.builder.ret(val)

    def Identifier(self, node: Identifier):
        for t in self.symboltable[::-1]:
            if node.name in t:
                return t[node.name]

    def MemberExpr(self, node: MemberExpr):
        raise NotImplementedError

    def IfExpr(self, node: IfExpr):
        result = self.builder.alloca(self.typeToLLVM(node.thenExpr.inferredtype))
        pred = self.deref(self.visit(node.condition))
        with self.builder.if_else(pred) as (then, otherwise):
            with then:
                thenExpr = self.visit(node.thenExpr)
                self.builder.store(thenExpr, result)
            with otherwise:
                elseExpr = self.visit(node.elseExpr)
                self.builder.store(elseExpr, result)

    def MethodCallExpr(self, node: MethodCallExpr):
        # add self argument
        args = [self.visit(node.method.object)] + [self.visit(x) for x in node.args]
        # node.method.object has a ClassType
        name = node.method.object.inferredType.className + "_" + node.method.member.name
        func = self.module.get_global(name)
        self.builder.call(func, args)

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        return ir.Constant(self.BOOL_TYPE, node.value)

    def IntegerLiteral(self, node: IntegerLiteral):
        return ir.Constant(self.INT_TYPE, node.value)

    def NoneLiteral(self, node: NoneLiteral):
        return self.builder.inttoptr(
            ir.Constant(self.INT_TYPE, 0),
            self.module.get_identified_type("object"))

    def StringLiteral(self, node: StringLiteral):
        # encoding format referenced from: https://github.com/hassanalinali/Lesma
        string = node.value
        n = len(string) + 1
        value = bytearray((' ' * n).encode('ascii'))
        value[-1] = 0
        value[:-1] = string.encode('utf-8')
        strType = self.module.get_identified_type("str")
        return strType([ir.Constant(self.INT_TYPE, len(string)),
                        ir.Constant(ir.ArrayType(ir.IntType(8), n), value)])

