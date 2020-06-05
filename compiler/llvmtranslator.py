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
        self.classTypes["str"] = ir.LiteralStructType(ir.context.global_context,
                                                      [ir.IntType(64), ir.ArrayType(ir.IntType(8), 0)])
        # object is empty struct
        self.classTypes["object"] = ir.LiteralStructType(ir.context.global_context, [])
        self.classLayouts = defaultdict(lambda: None)

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
        done = {"str", "object", "int", "bool", "<Empty>", "<None>"}
        todo = []
        pass # TODO

    # convert Chocopy type to LLVM type, with 
    # optional flag to return in pointer form for classes & lists
    def typeToLLVM(self, t, aspointer=False):
        if isinstance(t, ClassValueType):
            if t == ts.INT_TYPE:
                return self.INT_TYPE
            if t == ts.BOOL_TYPE:
                return self.BOOL_TYPE
            if t == ts.EMPTY_TYPE: # pointer to empty list
                return self.typeToLLVM(ListValueType(ClassValueType("object")), True)
            if t == ts.NONE_TYPE: # null pointer
                return self.classTypes["object"].as_pointer()
            typ = self.classTypes[t.className]
            return typ.as_pointer() if aspointer else typ
        elif isinstance(t, ListValueType):
            elementType = self.typeToLLVM(t.elementType)
            typ = ir.LiteralStructType(ir.context.global_context,
                [ir.IntType(64), ir.ArrayType(ir.IntType(8), 0)])
            return typ.as_pointer() if aspointer else typ
        elif isinstance(t, FuncValueType):
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
        raise NotImplementedError

    def IndexExpr(self, node: IndexExpr):
        raise NotImplementedError

    def UnaryExpr(self, node: UnaryExpr):
        raise NotImplementedError

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
                self.builder.ret(ir.Constant(self.expReturnType.as_pointer(), None))
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
        return ir.Constant(self.classTypes["object"].as_pointer(), None)

    def StringLiteral(self, node: StringLiteral):
        return ir.Constant.literal_struct([
            ir.Constant(self.INT_TYPE, len(node.value)), 
            ir.Constant(ir.ArrayType(ir.IntType(8), 0), [ord(x) for x in node.value])
            ])

    # TYPES

    def TypedVar(self, node: TypedVar):
        raise NotImplementedError

    def ListType(self, node: ListType):
        raise NotImplementedError

    def ClassType(self, node: ClassType):
        raise NotImplementedError
