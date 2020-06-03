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
        self.STR_TYPE = ir.ArrayType(ir.IntType(8), 0)

        self.classTypes = defaultdict(lambda: None)
        # strings are variable-length arrays of i8
        self.classTypes["str"] = ir.LiteralStructType(ir.context.global_context,
                                                      [ir.IntType(8), ir.ArrayType(ir.IntType(8), 0)])
        # object is empty struct
        self.classTypes["object"] = ir.LiteralStructType(ir.context.global_context, [])
        
        self.stdPrint()
        self.stdLen()
        self.stdInput()

        self.builder = ir.IRBuilder()

    def visit(self, node: Node):
        return node.visit(self)

    # set up standard library functions

    def stdPrint(self):
        # may need different prints for different types
        pass  # TODO

    def stdLen(self):
        pass  # TODO

    def stdInput(self):
        pass  # TODO

    # TOP LEVEL & DECLARATIONS

    def Program(self, node: Program):
        pass  # TODO

    def VarDef(self, node: VarDef):
        pass  # TODO

    def ClassDef(self, node: ClassDef):
        pass  # TODO

    def FuncDef(self, node: FuncDef):
        pass  # TODO

    def NonLocalDecl(self, node: NonLocalDecl):
        pass  # TODO

    def GlobalDecl(self, node: GlobalDecl):
        pass  # TODO

    # STATEMENTS & EXPRESSIONS

    def ExprStmt(self, node: ExprStmt):
        self.visit(node.expr)

    def AssignStmt(self, node: AssignStmt):
        pass  # TODO

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
        pass  # TODO

    def IndexExpr(self, node: IndexExpr):
        pass  # TODO

    def UnaryExpr(self, node: UnaryExpr):
        pass  # TODO

    def CallExpr(self, node: CallExpr):
        pass  # TODO

    def ForStmt(self, node: ForStmt):
        pass  # TODO

    def ListExpr(self, node: ListExpr):
        pass  # TODO

    def WhileStmt(self, node: WhileStmt):
        pass  # TODO

    def ReturnStmt(self, node: ReturnStmt):
        pass  # TODO

    def Identifier(self, node: Identifier):
        pass  # TODO

    def MemberExpr(self, node: MemberExpr):
        pass  # TODO

    def IfExpr(self, node: IfExpr):
        pass  # TODO

    def MethodCallExpr(self, node: MethodCallExpr):
        pass  # TODO

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        return ir.Constant(self.BOOL_TYPE, node.value)

    def IntegerLiteral(self, node: IntegerLiteral):
        return ir.Constant(self.INT_TYPE, node.value)

    def NoneLiteral(self, node: NoneLiteral):
        return ir.Constant(self.classTypes["object"], None)

    def StringLiteral(self, node: StringLiteral):
        return ir.Constant.literal_struct([
            ir.Constant(self.INT_TYPE, len(node.value)), 
            ir.Constant(ir.ArrayType(ir.IntType(8), 0), [ord(x) for x in node.value])
            ])

    # TYPES

    def TypedVar(self, node: TypedVar):
        pass  # TODO

    def ListType(self, node: ListType):
        pass  # TODO

    def ClassType(self, node: ClassType):
        pass  # TODO
