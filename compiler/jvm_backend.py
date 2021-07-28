from .astnodes import *
from .types import *
from .builder import Builder
from .typesystem import TypeSystem
from .visitor import Visitor
from collections import defaultdict
import json

class JvmBackend(Visitor):
    # record all free vars from nested functions

    def __init__(self, main: str, ts:TypeSystem):
        self.classes = dict()
        self.classes[main] = Builder(main)
        self.currentClass = main
        self.main = main # name of main class
        self.locals = [defaultdict(lambda: None)]
        self.counter = 0 # for labels
        self.returnType = None
        self.stackLimit = 50
        self.localLimit = 50
        self.ts = ts

    def currentBuilder(self):
        return self.classes[self.currentClass]

    def visit(self, node: Node):
        node.visit(self)

    def instr(self, instr:str):
        self.currentBuilder().newLine(instr)

    def newLabelName(self)->str:
        self.counter += 1
        return "L"+str(self.counter)

    def label(self, name:str)->str:
        self.currentBuilder().unindent()
        self.instr(name+":")
        self.currentBuilder().indent()

    def enterScope(self):
        self.locals.append(defaultdict(lambda: None))

    def exitScope(self):
        self.locals.pop()

    def returnInstr(self, exprType: ValueType):
        if exprType.isJavaRef():
            self.instr("areturn")
        else:
            self.instr("ireturn")

    def store(self, name:str, t:ValueType):
        n = self.locals[-1][name]
        if n is None:
            raise Exception("Internal compiler error: unknown name {} for store".format(name))
        if t.isJavaRef():
            self.instr("astore {}".format(n))
        else:
            self.instr("istore {}".format(n))

    def load(self, name:str, t:ValueType):
        n = self.locals[-1][name]
        if n is None:
            raise Exception("Internal compiler error: unknown name {} for load".format(name))
        if t.isJavaRef():
            self.instr("aload {}".format(n))
        else:
            self.instr("iload {}".format(n))

    def arrayStore(self, t:ValueType):
        # expect the stack to be array, idx, value
        if t.isJavaRef():
            self.instr("aastore")
        else:
            self.instr("iastore")

    def arrayLoad(self, t:ValueType):
        # expect the stack to be array, idx
        if t.isJavaRef():
            self.instr("aaload")
        else:
            self.instr("iaload")

    def newLocalEntry(self, name:str)->int:
        # add a new entry to locals table w/o storing anything
        n = len(self.locals[-1])
        self.locals[-1][name] = n
        return n

    def genLocalName(self, offset:int)->str:
        return "__local__{}".format(offset)

    def newLocal(self, name:str=None, isRef:bool=True)->int:
        # store the top of stack as a new local
        n = len(self.locals[-1])
        if isRef:
            self.instr("astore {}".format(n))
        else:
            self.instr("istore {}".format(n))
        if name is None:
            name = self.genLocalName(n)
        self.locals[-1][name] = n
        return n

    def Program(self, node: Program):
        func_decls = [d for d in node.declarations if isinstance(d, FuncDef)]
        cls_decls = [d for d in node.declarations if isinstance(d, ClassDef)]
        var_decls = [d for d in node.declarations if isinstance(d, VarDef)]

        self.instr(".version 49 0")
        self.instr(".class public super {}".format(self.main))
        self.instr(".super java/lang/Object")
        self.instr(".method public static main : ([Ljava/lang/String;)V")
        self.currentBuilder().indent()
        self.instr(".limit stack {}".format(self.stackLimit))
        self.instr(".limit locals {}".format(len(node.declarations) + self.localLimit))
        for d in var_decls:
            self.visit(d)
        for s in node.statements:
            self.visit(s)
        self.instr("return")
        self.currentBuilder().unindent()
        self.instr(".end method")
        for d in func_decls:
            self.visit(d)
        self.instr(".end class")
        for d in cls_decls:
            self.visit(d)

    def ClassDef(self, node: ClassDef):
        pass # TODO

    def FuncDef(self, node: FuncDef):
        self.enterScope()
        self.instr(".method public static {} : {}".format(node.name.name, node.type.getJavaSignature()))
        self.currentBuilder().indent()
        self.instr(".limit stack {}".format(self.stackLimit))
        self.instr(".limit locals {}".format(len(node.declarations) + self.localLimit))
        for i in range(len(node.params)):
            self.newLocalEntry(node.params[i].identifier.name)
        for d in node.declarations:
            # TODO build nested funcs (probably by hoisting)
            self.visit(d)
        self.returnType = node.type.returnType
        # handle last return
        hasReturn = False
        for s in node.statements:
            self.visit(s)
            if s.isReturn:
                hasReturn = True
        if not hasReturn:
            self.buildReturn(None)
        self.exitScope()
        self.currentBuilder().unindent()
        self.instr(".end method")

    def VarDef(self, node: VarDef):
        if node.isAttr:
            pass # TODO field defs
        else:
            self.visit(node.value)
            self.newLocal(node.var.identifier.name, node.value.inferredType.isJavaRef())

    # STATEMENTS

    def processAssignmentTarget(self, target:Expr):
        if isinstance(target, Identifier):
            self.store(target.name, target.inferredType)
        elif isinstance(target, IndexExpr):
            # stack should be array, idx, value
            self.visit(target.list)
            self.instr("swap")
            self.visit(target.index)
            self.instr("swap")
            self.arrayStore(target.inferredType)
        elif isinstance(target, MemberExpr):
            pass # TODO
        else:
            raise Exception("Internal compiler error: unsupported assignment target")

    def AssignStmt(self, node: AssignStmt):
        self.visit(node.value)
        targets = node.targets[::-1]
        if len(targets) > 1:
            self.instr("dup")
            for t in targets:
                self.processAssignmentTarget(t)
        else:
            self.processAssignmentTarget(targets[0])

    def IfStmt(self, node: IfStmt):
        # TODO nop for empty
        pass

    def ExprStmt(self, node: ExprStmt):
        self.visit(node.expr)

    def comparator(self, instr:str, firstBranchTrue:bool=False):
        l1 = self.newLabelName()
        l2 = self.newLabelName()
        self.instr("{} {}".format(instr, l1))
        if firstBranchTrue:
            self.instr("iconst_1")
        else:
            self.instr("iconst_0")
        self.instr("goto {}".format(l2))
        self.label(l1)
        if firstBranchTrue:
            self.instr("iconst_0")
        else:
            self.instr("iconst_1") 
        self.label(l2)

    def isListConcat(self, operator:str, leftType:ValueType, rightType:ValueType)->bool:
        return leftType.isListType() and rightType.isListType() and operator == "+"

    def BinaryExpr(self, node: BinaryExpr):
        operator = node.operator
        leftType = node.left.inferredType
        rightType = node.right.inferredType
        if not self.isListConcat(operator, leftType, rightType):
            self.visit(node.left)
            self.visit(node.right)
        # concatenation and addition
        if operator == "+":
            if self.isListConcat(operator, leftType, rightType):
                self.visit(node.left)
                self.visit(node.right)
                self.instr("dup2")
                arrR = self.newLocal(None, True)
                # stack is L, R, L
                self.instr("arraylength")
                lenL = self.newLocal(None, False)
                self.instr("arraylength")
                lenR = self.newLocal(None, False)
                self.instr("iload {}".format(lenL))
                self.instr("iload {}".format(lenR))
                self.instr("iadd")
                # stack is L, total_length
                t = node.inferredType
                if ((isinstance(t, ListValueType) and t.elementType.isJavaRef()) 
                    or t == EmptyType()):
                    # refs
                    self.instr("invokestatic Method java/util/Arrays copyOf ([Ljava/lang/Object;I)[Ljava/lang/Object;")
                    self.instr("checkcast {}".format(t.getJavaSignature()))
                else:
                    # primitives
                    self.instr("invokestatic Method java/util/Arrays copyOf ({}I){}"
                        .format(
                            self.ts.join(leftType, rightType).getJavaSignature(), 
                            t.getJavaSignature()
                        ))
                # stack is new_array
                newArr = self.newLocal(None, True)
                self.instr("aload {}".format(arrR))
                self.instr("iconst_0")
                self.instr("aload {}".format(newArr))
                self.instr("iload {}".format(lenL))
                self.instr("iload {}".format(lenR))
                # stack is R, 0, new_array, len(L), len(R)
                self.instr("invokestatic Method java/lang/System arraycopy (Ljava/lang/Object;ILjava/lang/Object;II)V")
                self.instr("aload {}".format(newArr))
            elif leftType == StrType():
                self.instr("invokevirtual Method java/lang/String concat (Ljava/lang/String;)Ljava/lang/String;")
            elif leftType == IntType():
                self.instr("iadd")
            else:
                raise Exception("Internal compiler error: unexpected operand types for +")
        # other arithmetic operators
        elif operator == "-":
            self.instr("isub")
        elif operator == "*":
            self.instr("imul")
        elif operator == "//":
            self.instr("invokestatic Method java/lang/Math floorDiv (II)I")
        elif operator == "%":
            self.instr("irem")
        # relational operators
        elif operator == "<":
            self.comparator("if_icmplt")
        elif operator == "<=":
            self.comparator("if_icmple")
        elif operator == ">":
            self.comparator("if_icmpgt")
        elif operator == ">=":
            self.comparator("if_icmpge")
        elif operator == "==":
            if leftType.isJavaRef():
                self.instr("invokevirtual Method java/lang/String equals (Ljava/lang/Object;)Z")
            else:
                self.comparator("if_icmpeq")
        elif operator == "!=":
            if leftType.isJavaRef():
                self.instr("invokevirtual Method java/lang/String equals (Ljava/lang/Object;)Z")
                self.comparator("ifne", True)
            else:
                self.comparator("if_icmpne")
        elif operator == "is":
            self.comparator("if_acmpeq")
        # logical operators
        elif operator == "and":
            self.instr("iand")
        elif operator == "or":
            self.instr("ior")
        else:
            raise Exception("Internal compiler error: unexpected operator {}".format(operator))

    def IndexExpr(self, node: IndexExpr):
        # TODO string indexing
        self.visit(node.list)
        self.visit(node.index)
        self.arrayLoad(node.inferredType)

    def UnaryExpr(self, node: UnaryExpr):
        self.visit(node.operand)
        if node.operator == "-":
            self.instr("ineg")
        elif node.operator == "not":
            self.comparator("ifne", True)

    def buildConstructor(self, node: CallExpr):
        className = node.function.name
        classType = ClassValueType(className)
        javaName = classType.getJavaName()
        self.instr("new {}".format(javaName))
        self.instr("dup")
        self.instr("invokespecial Method {} <init> ()V".format(javaName))

    def CallExpr(self, node: CallExpr):
        signature = node.function.inferredType.getJavaSignature()
        name = node.function.name
        if node.isConstructor:
            self.buildConstructor(node)
            return
        # TODO shadowing
        if name == "print":
            self.emit_print(node.args[0])
        elif name == "len":
            self.emit_len(node.args[0])
        elif name == "input":
            self.emit_input()
        elif name == "__assert__":
            self.emit_assert(node.args[0])
        else:
            for arg in node.args:
                self.visit(arg)
            self.instr("invokestatic Method {} {} {}".format(self.main, name, signature))
            if node.function.inferredType.returnType.isNone():
                self.NoneLiteral(None) # push null for void return

    def ForStmt(self, node: ForStmt):
        pass

    def ListExpr(self, node: ListExpr):
        t = node.inferredType
        length = len(node.elements)
        self.instr("ldc {}".format(length))
        elementType = None
        if isinstance(t, ClassValueType):
            elementType = ClassValueType("object")
        else:
            elementType = t.elementType
        if isinstance(t, ClassValueType) or elementType.isJavaRef():
            self.instr("anewarray {}".format(elementType.getJavaName()))
        else:
            self.instr("newarray {}".format(elementType.getJavaName()))
        for i in range (len(node.elements)):
            self.instr("dup")
            self.instr("ldc {}".format(i))
            self.visit(node.elements[i])
            self.arrayStore(elementType)

    def WhileStmt(self, node: WhileStmt):
        pass

    def buildReturn(self, value:Expr):
        if self.returnType.isNone():
            self.instr("return")
        else:
            if value is None:
                self.NoneLiteral(None)
            else:
                self.visit(value)
            self.returnInstr(self.returnType)

    def ReturnStmt(self, node: ReturnStmt):
        self.buildReturn(node.value)

    def Identifier(self, node: Identifier):
        self.load(node.name, node.inferredType)

    def MemberExpr(self, node: MemberExpr):
        pass

    def IfExpr(self, node: IfExpr):
        self.visit(node.condition)
        l1 = self.newLabelName()
        l2 = self.newLabelName()
        self.instr("{} {}".format("ifne", l1))
        self.visit(node.elseExpr)
        self.instr("goto {}".format(l2))
        self.label(l1)
        self.visit(node.thenExpr)
        self.label(l2)

    def MethodCallExpr(self, node: MethodCallExpr):
        # TODO special case for init
        pass

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        if node.value:
            self.instr("iconst_1")
        else:
            self.instr("iconst_0")

    def IntegerLiteral(self, node: IntegerLiteral):
        self.instr("ldc {}".format(node.value))

    def NoneLiteral(self, node: NoneLiteral):
        self.instr("aconst_null")

    def StringLiteral(self, node: StringLiteral):
        self.instr("ldc "+json.dumps(node.value))

    # TYPES

    def TypedVar(self, node: TypedVar):
        pass

    def ListType(self, node: ListType):
        pass

    def ClassType(self, node: ClassType):
        pass

    def emit(self)->str:
        return self.currentBuilder().emit()

    # SUGAR

    def NonLocalDecl(self, node: NonLocalDecl):
        pass

    def GlobalDecl(self, node: GlobalDecl):
        pass

    # BUILT-INS - note: these are in-lined
    def emit_assert(self, arg:Expr):
        label = self.newLabelName()
        self.visit(arg)
        self.instr("ifne {}".format(label))
        msg = "failed assertion on line {}".format(arg.location[0])
        self.emit_exn(msg)
        self.label(label)

    def emit_exn(self, msg:str):
        self.instr("new java/lang/Exception")
        self.instr("dup")
        self.instr("ldc {}".format(json.dumps(msg)))
        self.instr("invokespecial Method java/lang/Exception <init> (Ljava/lang/String;)V")
        self.instr("athrow")

    def emit_input(self):
        self.instr("new java/util/Scanner")
        self.instr("dup")
        self.instr("getstatic Field java/lang/System in Ljava/io/InputStream;")
        self.instr("invokespecial Method java/util/Scanner <init> (Ljava/io/InputStream;)V") 
        l = self.newLocal()
        self.instr("aload {}".format(l))
        self.currentBuilder().addLine("invokevirtual Method java/util/Scanner nextLine ()Ljava/lang/String;")

    def emit_len(self, arg:Expr):
        t = arg.inferredType
        is_list = False
        if isinstance(t, ListValueType):
            is_list = True
        else:
            if t == NoneType():
                is_list = True
            elif t == EmptyType():
                is_list = True
            elif t == StrType():
                is_list = False
            else:
                self.emit_exn("Built-in function len is unsupported for values of type {}".format(arg.inferredType.classname))
        self.visit(arg)
        if is_list:
            self.instr("arraylength")
        else:
            self.instr("invokevirtual Method java/lang/String length ()I")

    def emit_print(self, arg:Expr):
        if isinstance(arg.inferredType, ListValueType) or arg.inferredType.className not in {"bool", "int", "str"}:
            self.emit_exn("Built-in function print is unsupported for values of type {}".format(arg.inferredType.classname))
        t = arg.inferredType.getJavaSignature()
        self.instr("getstatic Field java/lang/System out Ljava/io/PrintStream;")
        self.visit(arg)
        self.instr("invokevirtual Method java/io/PrintStream println ({})V".format(t))
        self.NoneLiteral(None) # push None for void return
