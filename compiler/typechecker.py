from .astnodes import *
from .types import *
from collections import defaultdict
from .typesystem import TypeSystem, ClassInfo
from .visitor import Visitor
from typing import List, Optional, Any, assert_type


class TypeChecker(Visitor):
    symbolTable: List[defaultdict]
    currentClass: Optional[str]
    errors: List[CompilerError]
    expReturnType: Optional[ValueType]
    program: Optional[Program]

    def __init__(self, ts: TypeSystem):
        # typechecker attributes and their chocopy typing judgement analogues:
        # O : symbolTable
        # M : classes
        # C : currentClass
        # R : expReturnType

        # stack of hashtables representing scope
        # each table holds identifier->type mappings defined in that scppe
        self.symbolTable = [defaultdict(lambda: None)]

        # standard library functions
        self.symbolTable[0]["print"] = FuncType([ObjectType()], NoneType())
        self.symbolTable[0]["input"] = FuncType([], StrType())
        self.symbolTable[0]["len"] = FuncType([ObjectType()], IntType())
        self.symbolTable[0]["__assert__"] = FuncType([BoolType()], NoneType())

        self.ts = ts

        self.errors = []  # list of errors encountered
        self.currentClass = None  # name of current class
        self.expReturnType = None  # expected return type of current function

        self.program = None
        self.addErrors = True

    def visit(self, node: Node) -> Any:
        if isinstance(node, Program) or isinstance(node, ClassDef) or isinstance(node, FuncDef):
            return node.visit(self)
        else:
            return node.postorder(self)

    def funcParams(self, node: FuncDef):
        pass

    def enterScope(self):
        self.symbolTable.append(defaultdict(lambda: None))

    def exitScope(self):
        self.symbolTable.pop()

    # SYMBOL TABLE LOOKUPS

    def getType(self, var: str):
        # get the type of an identifier in the current scope, or None if not found
        for table in self.symbolTable[::-1]:
            if var in table:
                return table[var]
        return None

    def getLocalType(self, var: str):
        # get the type of an identifier in the current scope, or None if not found
        # ignore global variables
        for table in self.symbolTable[1:][::-1]:
            if var in table:
                return table[var]
        return None

    def getNonLocalType(self, var: str):
        # get the type of an identifier outside the current scope, or None if not found
        # ignore global variables
        for table in self.symbolTable[1:-1][::-1]:
            if var in table:
                return table[var]
        return None

    def getGlobal(self, var: str):
        return self.symbolTable[0][var]

    def addType(self, var: str, t: SymbolType):
        self.symbolTable[-1][var] = t

    def defInCurrentScope(self, var: str) -> bool:
        # return if the name was defined in the current scope
        return self.symbolTable[-1][var] is not None

    # ERROR HANDLING

    def addError(self, node: Node, message: str):
        if self.addErrors:
            if node.errorMsg is not None:  # 1 error msg per node
                return
            message = F"{message}. Line {node.location[0]} Col {node.location[1]}"
            node.errorMsg = message
            assert self.program is not None
            self.program.errors.errors.append(
                CompilerError(node.location, message))
            self.errors.append(CompilerError(node.location, message))

    def binopError(self, node):
        self.addError(node, "Cannot use operator {} on types {} and {}".format(
            node.operator, node.left.inferredType, node.right.inferredType))

    # UTIL

    def getSignature(self, node: FuncDef):
        rType = self.visit(node.returnType)
        return FuncType([self.visit(t) for t in node.params], rType)

    def Program(self, node: Program):
        self.program = node
        for d in node.declarations:
            identifier = d.getIdentifier()
            if self.defInCurrentScope(identifier.name) or self.ts.classExists(identifier.name):
                self.addError(
                    identifier, f"Duplicate declaration of identifier: {identifier.name}")
            if isinstance(d, ClassDef):
                className = d.name.name
                superclass = d.superclass.name
                if not self.ts.classExists(superclass):
                    self.addError(d.superclass,
                                  F"Unknown superclass: {superclass}")
                    superclass = "object"
                if superclass in ["int", "bool", "str", className]:
                    self.addError(d.superclass,
                                  F"Illegal superclass: {superclass}")
                    superclass = "object"
                self.ts.classes[className] = ClassInfo(className, superclass)
            if isinstance(d, FuncDef):
                self.funcParams(d)
                self.addType(d.getIdentifier().name, self.getSignature(d))
            if isinstance(d, VarDef):
                self.addType(identifier.name, self.visit(d.var))
        for d in node.declarations:
            if d.getIdentifier().errorMsg is not None:
                continue
            self.visit(d)
        if len(self.errors) > 0:
            return
        for s in node.statements:
            self.visit(s)

    def VarDef(self, node: VarDef):
        annotationType = self.visit(node.var)
        if not self.ts.canAssign(node.value.inferredType, annotationType):
            self.addError(
                node, f"Expected {annotationType}, got {node.value.inferredType}")
        return annotationType

    def ClassDef(self, node: ClassDef):
        className = node.name.name
        self.currentClass = className
        # add all attrs and methods before checking method bodies
        for d in node.declarations:
            if isinstance(d, FuncDef):  # methods
                funcName = d.getIdentifier().name
                self.funcParams(d)
                funcType = self.getSignature(d)
                if funcName in self.ts.classes[className].methods or funcName in self.ts.classes[className].attrs:
                    self.addError(d.getIdentifier(),
                                  F"Duplicate declaration of identifier: {funcName}")
                    continue
                t = self.ts.getAttrOrMethod(className, funcName)
                if t is not None:
                    if not isinstance(t, FuncType):
                        self.addError(d.getIdentifier(),
                                      F"Method name shadows attribute: {funcName}")
                        continue
                    if not t.methodEquals(funcType):  # excluding self argument
                        self.addError(d.getIdentifier(),
                                      F"Redefined method doesn't match superclass signature: {funcName}")
                        continue
                self.ts.classes[className].methods[funcName] = funcType
            if isinstance(d, VarDef):  # attributes
                attrName = d.getIdentifier().name
                if self.ts.getAttrOrMethod(className, attrName):
                    self.addError(d.getIdentifier(),
                                  F"Cannot redefine attribute: {attrName}")
                    continue
                self.ts.classes[className].attrs[attrName] = (self.visit(
                    d.var), d.value)
                self.ts.classes[className].orderedAttrs.append(attrName)
        for d in node.declarations:
            self.visit(d)
        self.currentClass = None
        return None

    def FuncDef(self, node: FuncDef):
        self.enterScope()
        funcName = node.getIdentifier().name
        funcType = self.getSignature(node)
        node.type = funcType
        self.expReturnType = funcType.returnType
        if not node.isMethod:  # top level function decl OR nested function
            if self.ts.classExists(funcName):
                self.addError(node.getIdentifier(),
                              F"Functions cannot shadow classes: {funcName}")
                return
            if self.defInCurrentScope(funcName):
                self.addError(node.getIdentifier(
                ), f"Duplicate declaration of identifier: {funcName}")
                return
            self.addType(funcName, funcType)
        else:  # method decl
            if (len(node.params) == 0 or node.params[0].identifier.name != "self" or
                    (not isinstance(funcType.parameters[0], ClassValueType)) or
                    funcType.parameters[0].className != self.currentClass):
                self.addError(
                    node.getIdentifier(), f"Missing self param in method: {funcName}")
                return
        for p in node.params:
            t = self.visit(p)
            pName = p.identifier.name
            if self.defInCurrentScope(pName) or self.ts.classExists(pName):
                self.addError(
                    p.identifier, f"Duplicate parameter name: {pName}")
                continue
            if t is not None:
                self.addType(pName, t)

        for d in node.declarations:
            identifier = d.getIdentifier()
            name = identifier.name
            if self.defInCurrentScope(name) or self.ts.classExists(name):
                self.addError(
                    identifier, f"Duplicate declaration of identifier: {name}")
                continue
            if isinstance(d, FuncDef):
                self.funcParams(d)
                self.addType(name, self.getSignature(d))
            if isinstance(d, VarDef):
                self.addType(name, self.visit(d.var))
            if isinstance(d, NonLocalDecl) or isinstance(d, GlobalDecl):
                self.addType(name, self.visit(d))
        rType = self.expReturnType
        for d in node.declarations:
            self.visit(d)
            self.expReturnType = rType
        hasReturn = False
        for s in node.statements:
            self.visit(s)
            if s.isReturn:
                hasReturn = True
        if (not hasReturn) and (not self.ts.canAssign(NoneType(), self.expReturnType)):
            self.addError(node.getIdentifier(
            ), f"Expected return statement of type {self.expReturnType}")
        self.expReturnType = None
        self.exitScope()
        return funcType

    # STATEMENTS (returns None) AND EXPRESSIONS (returns inferred type)

    def NonLocalDecl(self, node: NonLocalDecl):
        if self.expReturnType is None:
            self.addError(node, "Nonlocal decl outside of function")
            return
        identifier = node.getIdentifier()
        name = identifier.name
        t = self.getNonLocalType(name)
        if t is None or not isinstance(t, ValueType):
            self.addError(
                identifier, f"Unknown nonlocal variable: {name}")
            return
        identifier.inferredType = t
        return t

    def GlobalDecl(self, node: GlobalDecl):
        if self.expReturnType is None:
            self.addError(node, "Global decl outside of function")
            return
        identifier = node.getIdentifier()
        name = identifier.name
        t = self.getGlobal(name)
        if t is None or not isinstance(t, ValueType):
            self.addError(
                identifier, f"Unknown global variable: {name}")
            return
        identifier.inferredType = t
        return t

    def AssignStmt(self, node: AssignStmt):
        # variables can only be assigned to if they're defined in current scope
        if len(node.targets) > 1 and node.value.inferredType == ListValueType(NoneType()):
            self.addError(
                node.value, "Multiple assignment of [<None>] is forbidden")
        else:
            for t in node.targets:
                if isinstance(t, IndexExpr) and t.list.inferredType == StrType():
                    self.addError(t, "Cannot assign to index of string")
                    return
                if isinstance(t, Identifier) and not self.defInCurrentScope(t.name):
                    self.addError(
                        t, f"Identifier not defined in current scope: {t.name}")
                    return
                if not self.ts.canAssign(node.value.inferredType, t.inferredValueType()):
                    self.addError(
                        node, f"Expected {t.inferredType}, got {node.value.inferredType}")
                    return

    def IfStmt(self, node: IfStmt):
        # isReturn=True if there's >=1 statement in BOTH branches that have isReturn=True
        # if a branch is empty, isReturn=False
        if node.condition.inferredType != BoolType():
            self.addError(
                node.condition, f"Expected {BoolType()}, got {node.condition.inferredType}")
            return
        thenBody = False
        elseBody = False
        for s in node.thenBody:
            if s.isReturn:
                thenBody = True
        for s in node.elseBody:
            if s.isReturn:
                elseBody = True
        node.isReturn = (thenBody and elseBody)

    def BinaryExpr(self, node: BinaryExpr):
        operator = node.operator
        static_types = {IntType(),
                        BoolType(), StrType()}
        leftType = node.left.inferredType
        rightType = node.right.inferredType

        # concatenation and addition
        if operator == "+":
            if isinstance(leftType, ListValueType) and isinstance(rightType, ListValueType):
                node.inferredType = ListValueType(
                    self.ts.join(leftType.elementType, rightType.elementType))
                return node.inferredType
            elif leftType == rightType and leftType in {StrType(), IntType()}:
                node.inferredType = leftType
                return leftType
            else:
                self.binopError(node)

        # other arithmetic operators
        elif operator in {"-", "*", "//", "%"}:
            if leftType == IntType() and rightType == IntType():
                node.inferredType = IntType()
                return IntType()
            else:
                self.binopError(node)

        # relational operators
        elif operator in {"<", "<=", ">", ">="}:
            if leftType == IntType() and rightType == IntType():
                node.inferredType = BoolType()
                return BoolType()
            else:
                self.binopError(node)
        elif operator in {"==", "!="}:
            if leftType == rightType and \
                    leftType in static_types:
                node.inferredType = BoolType()
                return BoolType()
            else:
                self.binopError(node)
        elif operator == "is":
            if leftType not in static_types and rightType not in static_types:
                node.inferredType = BoolType()
                return BoolType()
            else:
                self.binopError(node)

        # logical operators
        elif operator in {"and", "or"}:
            if leftType == BoolType() and rightType == BoolType():
                node.inferredType = BoolType()
                return BoolType()
            else:
                self.binopError(node)

        else:
            node.inferredType = ObjectType()
            return ObjectType()

    def IndexExpr(self, node: IndexExpr):
        if node.index.inferredType != IntType():
            self.addError(
                node, f"Expected {IntType()} index, got {node.index.inferredType}")
        # indexing into a string returns a new string
        if node.list.inferredType == StrType():
            node.inferredType = StrType()
            return node.inferredType
        # indexing into a list of type T returns a value of type T
        elif isinstance(node.list.inferredType, ListValueType):
            node.inferredType = node.list.inferredType.elementType
            return node.inferredType
        else:
            self.addError(node, f"Cannot index into {node.list.inferredType}")
            node.inferredType = ObjectType()
            return ObjectType()

    def UnaryExpr(self, node: UnaryExpr):
        operandType = node.operand.inferredType
        if node.operator == "-":
            if operandType == IntType():
                node.inferredType = IntType()
                return IntType()
            else:
                self.addError(node, f"Expected int, got {operandType}")
        elif node.operator == "not":
            if operandType == BoolType():
                node.inferredType = BoolType()
                return BoolType()
            else:
                self.addError(node, f"Expected bool, got {operandType}")
        else:
            node.inferredType = ObjectType()
            return ObjectType()

    def CallExpr(self, node: CallExpr):
        fname = node.function.name
        t = None
        if self.ts.classExists(fname):
            # constructor
            node.isConstructor = True
            t = self.ts.getMethod(fname, "__init__")
            assert t is not None
            if len(t.parameters) != len(node.args) + 1:
                self.addError(
                    node, f"Expected {len(t.parameters) - 1} args, got {len(node.args)}")
            else:
                for i in range(len(t.parameters) - 1):
                    if not self.ts.canAssign(node.args[i].inferredType, t.parameters[i + 1]):
                        self.addError(
                            node, f"Expected {t.parameters[i + 1]}, got {node.args[i].inferredType}")
                        continue
            node.inferredType = ClassValueType(fname)
        else:
            t = self.getType(fname)
            if not isinstance(t, FuncType):
                self.addError(node, f"Not a function: {fname}")
                node.inferredType = ObjectType()
                return ObjectType()
            if len(t.parameters) != len(node.args):
                self.addError(
                    node, f"Expected {len(t.parameters)} args, got {len(node.args)}")
            else:
                for i in range(len(t.parameters)):
                    if not self.ts.canAssign(node.args[i].inferredType, t.parameters[i]):
                        self.addError(
                            node, f"Expected {t.parameters[i]}, got {node.args[i].inferredType}")
                        continue
            node.inferredType = t.returnType
        node.function.inferredType = t
        return node.inferredType

    def ForStmt(self, node: ForStmt):
        # set isReturn=True if any statement in body has isReturn=True
        iterType = node.iterable.inferredType
        if not self.defInCurrentScope(node.identifier.name):
            self.addError(
                node.identifier, f"Identifier not mutable in current scope: {node.identifier.name}")
            return
        if isinstance(iterType, ListValueType):
            if not self.ts.canAssign(iterType.elementType, node.identifier.inferredValueType()):
                self.addError(
                    node.identifier, f"Expected {iterType.elementType}, got {node.identifier.inferredType}")
                return
        elif StrType() == iterType:
            if not self.ts.canAssign(StrType(), node.identifier.inferredValueType()):
                self.addError(
                    node.identifier, f"Expected {StrType()}, got {node.identifier.inferredType}")
                return
        else:
            self.addError(
                node.iterable, f"Expected iterable, got {node.iterable.inferredType}")
            return
        for s in node.body:
            if s.isReturn:
                node.isReturn = True

    def ListExpr(self, node: ListExpr):
        if len(node.elements) == 0:
            node.inferredType = EmptyType()
        else:
            e_type = node.elements[0].inferredValueType()
            for e in node.elements:
                e_type = self.ts.join(e_type, e.inferredValueType())
            node.inferredType = ListValueType(e_type)
        return node.inferredType

    def WhileStmt(self, node: WhileStmt):
        if node.condition.inferredType != BoolType():
            self.addError(
                node.condition, f"Expected {BoolType()}, got {node.condition.inferredType}")
            return
        for s in node.body:
            if s.isReturn:
                node.isReturn = True

    def ReturnStmt(self, node: ReturnStmt):
        if self.expReturnType is None:
            self.addError(
                node, "Return statement outside of function definition")
        elif node.value is None:
            if not self.ts.canAssign(NoneType(), self.expReturnType):
                self.addError(
                    node, f"Expected {self.expReturnType}, got {NoneType()}")
        elif not self.ts.canAssign(node.value.inferredType, self.expReturnType):
            self.addError(
                node, f"Expected {self.expReturnType}, got {node.value.inferredType}")
        node.expType = self.expReturnType
        return

    def Identifier(self, node: Identifier):
        varType = None
        if self.expReturnType is None and self.currentClass is None:
            varType = self.getGlobal(node.name)
        else:
            varType = self.getType(node.name)
        if varType is not None and isinstance(varType, ValueType):
            node.inferredType = varType
        else:
            self.addError(node, f"Unknown identifier: {node.name}")
            node.inferredType = ObjectType()
        return node.inferredType

    def MemberExpr(self, node: MemberExpr):
        static_types = {IntType(),
                        BoolType(), StrType()}
        if node.object.inferredType in static_types or not isinstance(node.object.inferredType, ClassValueType):
            self.addError(
                node, f"Expected object, got {node.object.inferredType}")
        else:
            class_name, member_name = node.object.inferredType.className, node.member.name
            if self.ts.getAttr(class_name, member_name) is None:
                self.addError(
                    node, f"Attribute {member_name} doesn't exist for class {class_name}")
                node.inferredType = ObjectType()
                return ObjectType()
            else:
                node.inferredType = self.ts.getAttr(class_name, member_name)
        return node.inferredType

    def IfExpr(self, node: IfExpr):
        if node.condition.inferredType != BoolType():
            self.addError(
                node, f"Expected boolean, got {node.condition.inferredType}")
        node.inferredType = self.ts.join(
            node.thenExpr.inferredValueType(), node.elseExpr.inferredValueType())
        return node.inferredType

    def MethodCallExpr(self, node: MethodCallExpr):
        method_member = node.method
        t = None  # method signature
        static_types = {IntType(),
                        BoolType(), StrType()}
        if method_member.object.inferredType in static_types or not isinstance(method_member.object.inferredType, ClassValueType):
            self.addError(
                method_member, f"Expected object, got {method_member.object.inferredType}")
            node.inferredType = ObjectType()
            return node.inferredType
        else:
            class_name, member_name = method_member.object.inferredType.className, method_member.member.name
            t = self.ts.getMethod(class_name, member_name)
            if t is None:
                self.addError(
                    node, f"Method {member_name} doesn't exist for class {class_name}")
                node.inferredType = ObjectType()
                return node.inferredType
        # self arguments
        if len(t.parameters) != len(node.args) + 1:
            self.addError(
                node, f"Expected {len(t.parameters) - 1} args, got {len(node.args)}")
        else:
            for i in range(len(t.parameters) - 1):
                if not self.ts.canAssign(node.args[i].inferredType, t.parameters[i + 1]):
                    self.addError(
                        node, f"Expected {t.parameters[i + 1]}, got {node.args[i].inferredType}")
                    continue
        node.method.inferredType = t
        node.inferredType = t.returnType
        return node.inferredType

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        node.inferredType = BoolType()
        return node.inferredType

    def IntegerLiteral(self, node: IntegerLiteral):
        node.inferredType = IntType()
        return node.inferredType

    def NoneLiteral(self, node: NoneLiteral):
        node.inferredType = NoneType()
        return node.inferredType

    def StringLiteral(self, node: StringLiteral):
        node.inferredType = StrType()
        return node.inferredType

    # TYPES

    def TypedVar(self, node: TypedVar):
        # return the type of the annotaton
        node.t = self.visit(node.type)
        return node.t

    def ListType(self, node: ListType):
        return ListValueType(self.visit(node.elementType))

    def ClassType(self, node: ClassType):
        if node.className not in {"<None>", "<Empty>"} and not self.ts.classExists(node.className):
            self.addError(node, f"Unknown class: {node.className}")
            return ObjectType()
        else:
            return ClassValueType(node.className)
