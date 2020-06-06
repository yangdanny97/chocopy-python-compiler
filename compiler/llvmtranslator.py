from .astnodes import *
from .types import *
from collections import defaultdict
from .typechecker import TypeChecker
from .translator import Translator
from .typesystem import TypeSystem
from llvmlite import ir, binding


class LLVMTranslator(Translator):
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
        self.currentClass = None  # name of current class
        self.expReturnType = None  # expected return type of current function

        self.setupClasses()

        self.stdPrint()
        self.stdLen()
        self.stdInput()

    def visit(self, node: Node):
        return node.visit(self)

    # set up standard library functions

    def stdPrint(self):
        # may need different prints for different types
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

    # TOP LEVEL & DECLARATIONS

    def Program(self, node: Program):
        raise NotImplementedError

    def VarDef(self, node: VarDef):
        raise NotImplementedError

    def ClassDef(self, node: ClassDef):
        raise NotImplementedError

    def FuncDef(self, node: FuncDef):
        raise NotImplementedError

    def NonLocalDecl(self, node: NonLocalDecl):
        raise NotImplementedError

    def GlobalDecl(self, node: GlobalDecl):
        raise NotImplementedError

    # STATEMENTS & EXPRESSIONS

    def ExprStmt(self, node: ExprStmt):
        self.visit(node.expr)

    def AssignStmt(self, node: AssignStmt):
        raise NotImplementedError

    def IfStmt(self, node: IfStmt):
        pred = self.visit(node.condition)
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
            return self.builder.icmp_signed("==", left, right)
        elif operator == "!=":
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
        raise NotImplementedError

    def UnaryExpr(self, node: UnaryExpr):
        operand self.visit(node.operand)
        if node.operator == "-":
            return self.builder.neg(operand)
        elif node.operator == "not":
            return self.builder.not_(operand)

    def CallExpr(self, node: CallExpr):
        raise NotImplementedError

    def ForStmt(self, node: ForStmt):
        raise NotImplementedError

    def ListExpr(self, node: ListExpr):
        raise NotImplementedError

    def WhileStmt(self, node: WhileStmt):
        raise NotImplementedError

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
        raise NotImplementedError

    def MemberExpr(self, node: MemberExpr):
        raise NotImplementedError

    def IfExpr(self, node: IfExpr):
        raise NotImplementedError

    def MethodCallExpr(self, node: MethodCallExpr):
        raise NotImplementedError

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
        # TODO may need to null-terminate
        value = [ord(x) for x in node.value]
        strType = self.module.get_identified_type("str")
        return strType([ir.Constant(self.INT_TYPE, len(node.value)),
                        ir.Constant(ir.ArrayType(ir.IntType(8), 0), value)])

    # TYPES

    def TypedVar(self, node: TypedVar):
        raise NotImplementedError

    def ListType(self, node: ListType):
        raise NotImplementedError

    def ClassType(self, node: ClassType):
        raise NotImplementedError
