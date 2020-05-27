from .astnodes import *
from .types import *
from collections import defaultdict


class TypeChecker:
    def __init__(self):
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

        # type hierachy: dictionary of class->superclass mappings
        self.superclasses = defaultdict(lambda: None)

        # set up default class hierarchy
        self.superclasses["object"] = None
        self.superclasses["int"] = "object"
        self.superclasses["bool"] = "object"
        self.superclasses["str"] = "object"
        self.superclasses["<None>"] = "object"
        self.superclasses["<Empty>"] = "object"

        # symbol tables for each class's methods
        self.classes = defaultdict(lambda: {})

        self.classes["object"] = {"__init__": FuncType([], ObjectType())}
        self.classes["int"] = {"__init__": FuncType([], IntType())}
        self.classes["bool"] = {"__init__": FuncType([], BoolType())}
        self.classes["str"] = {"__init__": FuncType([], StrType())}

        self.INT_TYPE = IntType()
        self.STR_TYPE = StrType()
        self.BOOL_TYPE = BoolType()
        self.NONE_TYPE = NoneType()
        self.EMPTY_TYPE = EmptyType()
        self.OBJECT_TYPE = ObjectType()

        self.errors = []  # list of errors encountered
        self.currentClass = None  # name of current class
        self.expReturnType = None  # expected return type of current function

        self.program = None

    def typecheck(self, node):
        return node.typecheck(self)

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

    # CLASSES

    def getMethod(self, className: str, methodName: str):
        if methodName not in self.classes[className]:
            if self.superclasses[className] is None:
                return None
            return self.getMethod(self.superclasses[className], methodName)
        if not isinstance(self.classes[className][methodName], FuncType):
            return None
        return self.classes[className][methodName]

    def getAttr(self, className: str, attrName: str):
        if attrName not in self.classes[className]:
            if self.superclasses[className] is None:
                return None
            return self.getAttr(self.superclasses[className], attrName)
        if not isinstance(self.classes[className][attrName], ValueType):
            return None
        return self.classes[className][attrName]

    def getAttrOrMethod(self, className: str, name: str):
        if name not in self.classes[className]:
            if self.superclasses[className] is None:
                return None
            return self.getAttrOrMethod(self.superclasses[className], name)
        return self.classes[className][name]

    def classExists(self, className: str) -> bool:
        # we cannot check for None because it is a defaultdict
        return className in self.classes

    # TYPE HIERARCHY UTILS

    def isSubClass(self, a: str, b: str) -> bool:
        # return if a is the same class or subclass of b
        curr = a
        while curr is not None:
            if curr == b:
                return True
            else:
                curr = self.superclasses[curr]
        return False

    def isSubtype(self, a: ValueType, b: ValueType) -> bool:
        # return if a is a subtype of b
        if b == self.OBJECT_TYPE:
            return True
        if isinstance(a, ClassValueType) and isinstance(b, ClassValueType):
            return self.isSubClass(a.className, b.className)
        return a == b

    def canAssign(self, a: ValueType, b: ValueType) -> bool:
        # return if value of type a can be assigned/passed to type b (ex: b = a)
        if self.isSubtype(a, b):
            return True
        if a == self.NONE_TYPE and b not in [self.INT_TYPE, self.STR_TYPE, self.BOOL_TYPE]:
            return True
        if isinstance(b, ListValueType) and a == self.EMPTY_TYPE:
            return True
        if (isinstance(b, ListValueType) and isinstance(a, ListValueType)
                and a.elementType == self.NONE_TYPE):
            return self.canAssign(a.elementType, b.elementType)
        return False

    def join(self, a: ValueType, b: ValueType):
        # return closest mutual ancestor on typing tree
        if self.canAssign(a, b):
            return b
        if self.canAssign(b, a):
            return a
        if isinstance(b, ListValueType) and isinstance(a, ListValueType):
            return ListValueType(self.join(b.elementType, a.elementType))
        # if only 1 of the types is a list then the closest ancestor is object
        if isinstance(b, ListValueType) or isinstance(a, ListValueType):
            return self.OBJECT_TYPE
        # for 2 classes that aren't related by subtyping
        # find paths from A & B to root of typing tree
        aAncestors = []
        bAncestors = []
        while self.superclasses[a] is not None:
            aAncestors.append(self.superclasses[a])
            a = self.superclasses[a]
        while self.superclasses[b] is not None:
            aAncestors.append(self.superclasses[b])
            b = self.superclasses[b]
        # reverse lists to find lowest common ancestor
        aAncestors = aAncestors[::-1]
        bAncestors = bAncestors[::-1]
        for i in range(min(len(aAncestors), len(bAncestors))):
            if aAncestors[i] != bAncestors[i]:
                return aAncestors[i-1]
        # this really shouldn't be returned
        return self.OBJECT_TYPE

    # ERROR HANDLING

    def addError(self, node: Node, message: str):
        message = F"{message}. Line {node.location[0]} Col {node.location[1]}"
        node.errorMsg = message
        self.program.errors.errors.append(
            CompilerError(node.location, message))
        self.errors.append(message)

    def binopError(self, node):
        self.addError(node, "Cannot use operator {} on types {} and {}".format(
            node.operator, node.left.inferredType, node.right.inferredType))

    # DECLARATIONS (returns type of declaration, besides Program)

    def Program(self, node: Program):
        self.program = node
        # add all classnames before checking globals/functions/class decl bodies
        for d in node.declarations:
            if isinstance(d, ClassDef):
                if self.classExists(d.name.name):
                    self.addError(
                        d.name, F"Classes cannot shadow other classes: {d.name.name}")
                    continue
                self.classes[d.name] = {}
        for d in node.declarations:
            if isinstance(d, ClassDef):
                className = d.name.name
                superclass = d.superclass.name
                if not self.classExists(superclass):
                    self.addError(d.superclass,
                                F"Unknown superclass: {superclass}")
                    continue
                if superclass in ["int", "bool", "str", className]:
                    self.addError(d.superclass,
                                F"Illegal superclass: {superclass}")
                    continue
                self.superclasses[className] = superclass
        if len(self.errors) > 0:
            return
        for d in node.declarations:
            identifier = d.getIdentifier()
            if self.defInCurrentScope(identifier.name) or self.classExists(identifier.name):
                self.addError(
                    identifier, F"Duplicate declaration of identifier: {identifier.name}")
                continue
            dType = self.typecheck(d)
            if dType is not None:
                self.addType(identifier.name, dType)
        if len(self.errors) > 0:
            return
        for s in node.statements:
            self.typecheck(s)

    def VarDef(self, node: VarDef):
        varName = node.getIdentifier().name
        annotationType = self.typecheck(node.var)
        if not self.canAssign(node.value.inferredType, annotationType):
            self.addError(
                node, F"Expected {annotationType}, got {node.value.inferredType}")
        return annotationType

    def ClassDef(self, node: ClassDef):
        className = node.name.name
        self.currentClass = className
        # add all attrs and methods before checking method bodies
        for d in node.declarations:
            if isinstance(d, FuncDef):  # methods
                funcName = d.getIdentifier().name
                if funcName in self.classes[className]:
                    self.addError(node.getIdentifier(),
                                  F"Duplicate declaration of identifier: {funcName}")
                    continue
                t = self.getAttrOrMethod(className, funcName)
                if not isinstance(t, FuncType):
                    self.addError(node.getIdentifier(
                    ), F"Method name shadows attribute: {funcName}")
                    continue
                if funcName != "__init__":  # for all methods besides constructor, check signatures match
                    if not t.methodEquals(funcType):  # excluding self argument
                        self.addError(node.getIdentifier(
                        ), F"Redefined method doesn't match superclass signature: {funcName}")
                        continue
                self.classes[className][funcName] = FuncType(
                    [self.typecheck(t) for t in d.params], self.typecheck(d.returnType))
            if isinstance(d, VarDef):  # attributes
                attrName = d.getIdentifier().name
                if self.getAttrOrMethod(className, attrName):
                    self.addError(node.getIdentifier(),
                                  F"Cannot redefine attribute: {funcName}")
                    continue
                self.classes[className][attrName] = self.typecheck(d.var)
        for d in node.declarations:
            self.typecheck(d)
        self.currentClass = None
        return None

    def FuncDef(self, node: FuncDef):
        funcName = node.getIdentifier().name
        rType = self.typecheck(node.returnType)
        funcType = FuncType([self.typecheck(t) for t in node.params], rType)
        self.expReturnType = rType
        if not node.isMethod:  # top level function decl OR nested function
            if self.classExists(funcName):
                self.addError(node.getIdentifier(),
                              F"Functions cannot shadow classes: {funcName}")
                return
            if self.defInCurrentScope(funcName):
                self.addError(node.getIdentifier(
                ), F"Duplicate declaration of identifier: {funcName}")
                return
        else:  # method decl
            if (len(node.params) == 0 or node.params[0].identifier.name != "self" or
                    (not isinstance(funcType.parameters[0], ClassValueType)) or
                    funcType.parameters[0].className != self.currentClass):
                self.addError(
                    node, F"Missing self argument in method: {funcName}")
                return
        for p in node.params:
            t = self.typecheck(p)
            pName = p.identifier.name
            if self.defInCurrentScope(pName) or self.classExists(pName):
                self.addError(
                    p.identifier, F"Duplicate parameter name: {pName}")
                continue
            if t is not None:
                self.addType(pName, t)
        for d in node.declarations:
            identifier = d.getIdentifier()
            name = identifier.name
            if self.defInCurrentScope(name) or self.classExists(name):
                self.addError(
                    identifier, F"Duplicate declaration of identifier: {name}")
                continue
            dType = self.typecheck(d)
            if dType is not None:
                self.addType(name, dType)
        hasReturn = False
        for s in node.statements:
            self.typecheck(s)
            if s.isReturn:
                hasReturn = True
        if not hasReturn and self.expReturnType != self.NONE_TYPE:
            self.addError(node, "Expected return statement")
        self.expReturnType = None
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
                identifier, F"Unknown nonlocal variable: {name}")
            return
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
                identifier, F"Unknown global variable: {name}")
            return
        return t

    def AssignStmt(self, node: AssignStmt):
        # variables can only be assigned to if they're defined in current scope
        if len(node.targets) > 1 and node.value.inferredType == ListValueType(self.NONE_TYPE):
            self.addError(
                node.value, "Multiple assignment of [<None>] is forbidden")
        else:
            for t in node.targets:
                if not self.canAssign(node.value.inferredType, t.inferredType):
                    self.addError(
                        node, F"Expected {t.inferredType}, got {node.value.inferredType}")
                    return

    def IfStmt(self, node: IfStmt):
        # isReturn=True if there's >=1 statement in BOTH branches that have isReturn=True
        # if a branch is empty, isReturn=False
        if node.condition.inferredType != self.BOOL_TYPE:
            self.addError(
                node.condition, F"Expected {self.BOOL_TYPE}, got {node.condition.inferredType}")
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
        static_types = {self.INT_TYPE, self.BOOL_TYPE, self.STR_TYPE}
        leftType = node.left.inferredType
        rightType = node.right.inferredType

        # concatenation and addition
        if operator == "+":
            if isinstance(leftType, ListValueType) and isinstance(rightType, ListValueType):
                node.inferredType = ListValueType(self.join(leftType.elementType, rightType.elementType))
                return node.inferredType
            elif leftType == rightType and leftType in {self.STR_TYPE, self.INT_TYPE}:
                node.inferredType = leftType
                return leftType
            else:
                self.binopError(node)

        # other arithmetic operators
        if operator in {"-", "*", "//", "%"}:
            if leftType == self.INT_TYPE and rightType == self.INT_TYPE:
                node.inferredType = self.INT_TYPE
                return self.INT_TYPE
            else:
                self.binopError(node)

        # relational operators
        if operator in {"<", "<=", ">", ">="}:
            if leftType == self.INT_TYPE and rightType == self.INT_TYPE:
                node.inferredType = self.BOOL_TYPE
                return self.BOOL_TYPE
            else:
                self.binopError(node)
        if operator in {"==", "!="}:
            if leftType == rightType and \
                    leftType in static_types:
                node.inferredType = self.BOOL_TYPE
                return self.BOOL_TYPE
            else:
                self.binopError(node)
        if operator == "is":
            if leftType not in static_types and rightType not in static_types:
                node.inferredType = self.BOOL_TYPE
                return self.BOOL_TYPE
            else:
                self.binopError(node)

        # logical operators
        if operator in {"and", "or"}:
            if leftType == self.BOOL_TYPE and rightType == self.BOOL_TYPE:
                node.inferredType = self.BOOL_TYPE
                return self.BOOL_TYPE
            else:
                self.binopError(node)

        node.inferredType = self.OBJECT_TYPE
        return self.OBJECT_TYPE

    def IndexExpr(self, node: IndexExpr):
        # it is not possible to index into [<None>] and [<Empty>]
        if node.lst.inferredType == self.NONE_TYPE or node.lst.inferredType == self.EMPTY_TYPE:
            self.addError(node, "It is not possible to index into [<None>] and [<Empty>]")
        # indexing into a string returns a new string
        if node.lst.inferredType == self.STRING_TYPE:
            node.inferredType = self.STRING_TYPE
            return node.inferredType
        # indexing into a list of type T returns a value of type T
        if node.lst.inferredType == self.LIST_TYPE:
            node.inferredType = node.lst.elements[0].inferredType
            return node.inferredType

    def UnaryExpr(self, node: UnaryExpr):
        operandType = node.operand.inferredType
        if node.operator == "-":
            if operandType == self.INT_TYPE:
                node.inferredType = self.INT_TYPE
                return self.INT_TYPE
            else:
                self.addError(node, F"Expected int, got {operandType}")
        if node.operator == "not":
            if operandType == self.BOOL_TYPE:
                node.inferredType = self.BOOL_TYPE
                return self.BOOL_TYPE
            else:
                self.addError(node, F"Expected bool, got {operandType}")

        node.inferredType = self.OBJECT_TYPE
        return self.OBJECT_TYPE

    def CallExpr(self, node: CallExpr):
        return node.inferredType  # TODO

    def ForStmt(self, node: ForStmt):
        # set isReturn=True if any statement in body has isReturn=True
        iterType = node.iterable.inferredType
        if isinstance(iterType, ListValueType):
            if self.canAssign(iterType.elementType, node.identifier.inferredType):
                self.addError(
                    node.identifier, F"Expected {iterType.elementType}, got {node.identifier.inferredType}")
                return
        elif self.STR_TYPE == iterType:
            if self.canAssign(self.STR_TYPE, node.identifier.inferredType):
                self.addError(
                    node.identifier, F"Expected {self.STR_TYPE}, got {node.identifier.inferredType}")
                return
        else:
            self.addError(
                node.iterable, F"Expected iterable, got {node.iterable.inferredType}")
            return
        for s in node.body:
            if s.isReturn:
                node.isReturn = True

    def ListExpr(self, node: ListExpr):
        if len(node.elements) == 0:
            node.inferredType = self.EMPTY_TYPE
        else:
            e_type = node.elements[0].inferredType
            for e in node.elements:
                e_type = self.join(e_type, e.inferredType)
            node.inferredType = ListValueType(e_type)
        return node.inferredType

    def WhileStmt(self, node: WhileStmt):
        if node.condition.inferredType != self.BOOL_TYPE:
            self.addError(
                node.condition, F"Expected {self.BOOL_TYPE}, got {node.condition.inferredType}")
            return
        for s in node.body:
            if s.isReturn:
                node.isReturn = True

    def ReturnStmt(self, node: ReturnStmt):
        if self.expReturnType is None:
            self.addError(
                node, "Return statement outside of function definition")
        elif node.value is None:
            if  not self.canAssign(self.NONE_TYPE, self.expReturnType):
                self.addError(
                    node, F"Expected {self.expReturnType}, got {self.NONE_TYPE}")
        elif not self.canAssign(node.value.inferredType, self.expReturnType):
            self.addError(
                node, F"Expected {self.expReturnType}, got {node.value.inferredType}")
        return

    def Identifier(self, node: Identifier):
        varType = None
        if self.expReturnType is None and self.currentClass is None:
            varType = self.getGlobal(node.name)
        else:
            varType = self.getLocalType(node.name)
        if varType is not None and isinstance(varType, ValueType):
            node.inferredType = varType
        else:
            self.addError(node, F"Not a variable: {node.name}")
            node.inferredType = self.OBJECT_TYPE
        return node.inferredType

    def MemberExpr(self, node: MemberExpr):
        return node.inferredType  # TODO

    def IfExpr(self, node: IfExpr):
        if node.condition.inferredType != self.BOOL_TYPE:
            self.addError(F"Expected boolean, got {node.condition.inferredType}")
        if node.condition == True:
            node.inferredType = node.thenExpr.inferredType
        else:
            node.inferredType = node.elseExpr.inferredType
        return node.inferredType

    def MethodCallExpr(self, node: MethodCallExpr):
        return node.inferredType  # TODO

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
        return self.typecheck(node.type)

    def ListType(self, node: ListType):
        return ListValueType(self.typecheck(node.elementType))

    def ClassType(self, node: ClassType):
        if not self.classExists(node.className):
            self.addError(node, F"Unknown class: {node.className}")
            return self.OBJECT_TYPE
        else:
            return ClassValueType(node.className)
