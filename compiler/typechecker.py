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
        self.superclasses["<none>"] = "object"
        self.superclasses["<empty>"] = "object"

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

        self.errors = [] # list of errors encountered
        self.currentClass = None # name of current class
        self.expReturnType = None # expected return type of current function

        self.program = None

    def typecheck(self, node):
        node.typecheck(self)

    def enterScope(self):
        self.symbolTable.append(defaultdict(lambda: None))

    def exitScope(self):
        self.symbolTable.pop()

    def getType(self, var:str):
        # get the type of an identifier in the current scope, or None if not found
        for table in self.symbolTable[::-1]:
            if var in table:
                return table[var]
        return None

    def addType(self, var:str, t:SymbolType):
        self.symbolTable[-1][var] = t

    def defInCurrentScope(self, var:str)->bool:
        # return if the name was defined in the current scope
        return self.symbolTable[-1][var] is not None

    def isSubClass(self, a:str, b:str)->bool:
        # return if a is the same class or subclass of b
        curr = a
        while curr is not None:
            if curr == b:
                return True
            else:
                curr = self.superclasses[curr]
        return False

    def getMethod(self, className:str, methodName:str):
        if methodName not in self.classes[className]:
            if self.superclasses[className] is None:
                return None
            return self.getMethod(self.superclasses[className], methodName)
        if not isinstance(self.classes[className][methodName], FuncType):
            return None
        return self.classes[className][methodName]

    def getAttr(self, className:str, attrName:str):
        if attrName not in self.classes[className]:
            if self.superclasses[className] is None:
                return None
            return self.getAttr(self.superclasses[className], attrName)
        if not isinstance(self.classes[className][attrName], ValueType):
            return None
        return self.classes[className][attrName]

    def classExists(self, className:str)->bool:
        # we cannot check for None because it is a defaultdict
        return className in self.classes

    def isSubtype(self, a:SymbolType, b:SymbolType)->bool:
        # return if a is a subtype of b
        if b == self.OBJECT_TYPE:
            return True
        if isinstance(a, ClassValueType) and isinstance(b, ClassValueType):
            return self.isSubClass(a.className, b.className)
        return a == b

    def canAssign(self, a:SymbolType, b:SymbolType)->bool:
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

    def addError(self, node:Node, message:str):
        message = "Semantic Error: {}. Line {:d} Col {:d}".format(message, node.location[0], node.location[1])
        node.errorMsg = message
        self.program.errors.errors.append(CompilerError(node.location, message))
        self.errors.append(message)

    # visit methods for each AST node

    def Program(self, node:Program):
        self.program = node
        for d in self.declarations:
            identifier = d.getIdentifier()
            name = identifier.name
            if self.defInCurrentScope(name):
                self.addError(identifier, "Duplicate declaration of identifier in same scope: {}".format(name))
            dType = d.typecheck(self)
            if dType is not None:
                self.addType(name, dType)
        for s in self.statements:
            s.typecheck(self)
    
    def AssignStmt(self, node:AssignStmt):
        pass

    def Errors(self, node:Errors):
        pass

    def IfStmt(self, node:IfStmt):
        pass

    def TypedVar(self, node:TypedVar):
        return self.typecheck(node.type)

    def BinaryExpr(self, node:BinaryExpr):
        pass

    def IndexExpr(self, node:IndexExpr):
        pass

    def NonLocalDecl(self, node:NonLocalDecl):
        pass

    def UnaryExpr(self, node:UnaryExpr):
        pass

    def BooleanLiteral(self, node:BooleanLiteral):
        node.inferredType = BoolType()
        return node.inferredType

    def IntegerLiteral(self, node:IntegerLiteral):
        node.inferredType = IntType()
        return node.inferredType

    def NoneLiteral(self, node:NoneLiteral):
        node.inferredType = NoneType()
        return node.inferredType

    def VarDef(self, node:VarDef):
        varName = node.getIdentifier().name
        if self.currentClass is None:
            if self.classExists(varName):
                self.addError(node.getIdentifier(), "Cannot shadow classes: {}".format(varName))
                return
        else:
            pass
        # TODO check init
        return self.typecheck(node.var.type)

    def CallExpr(self, node:CallExpr):
        pass

    def ForStmt(self, node:ForStmt):
        pass

    def ListExpr(self, node:ListExpr):
        if len(elements) == 0:
            node.inferredType = ListValueType(EmptyType())
        # TODO

    def WhileStmt(self, node:WhileStmt):
        pass

    def ClassDef(self, node:ClassDef):
        className = node.name.name
        self.currentClass = className
        superclass = node.superclass.name
        if not self.classExists(superclass):
            self.addError(node.superclass, "Unknown superclass: {}".format(node.name))
        if superclass in ["int", "bool", "str"]:
            self.addError(node.superclass, "Illegal superclass: {}".format(node.name))
        if self.classExists(superclass):
            self.addError(node.name, "Class is already defined: {}".format(node.name))
        self.superclasses[className, superclass]
        self.classes[className] = {}
        for d in node.declarations:
            if isinstance(d, FuncDef):
                funcName = d.getIdentifier().name
                if funcName in self.classes[self.currentClass]:
                    self.addError(node.getIdentifier(),
                                "Cannot redefine method: {}".format(funcName))
                    continue
                if self.classes[self.currentClass][funcName] != funcType and funcName != "__init__":
                    self.addError(node.getIdentifier(
                    ), "Redefined method doesn't match superclass signature: {}".format(funcName))
                    continue
                self.classes[className][funcName] = FuncType([t for t in self.typecheck(
                            d.params)], self.typecheck(d.returnType))
            if isinstance(d, VarDef):
                pass
                # TODO
        for d in node.declarations:
            node.typecheck(self)
        self.currentClass = None

    def FuncDef(self, node: FuncDef):
        funcName = node.getIdentifier().name
        funcType = FuncType([t for to in self.typecheck(
                            d.params)], self.typecheck(d.returnType))
        if self.currentClass is None:
            if self.classExists(funcName):
                self.addError(node.getIdentifier(),
                              "Cannot shadow classes: {}".format(funcName))
                return
            if self.defInCurrentScope(funcName) and isinstance(self.getType(funcName), FuncType):
                self.addError(node.getIdentifier(
                ), "Cannot redefine function in same scope: {}".format(funcName))
                return
        else:
            if (len(node.params) == 0 or node.params[0].identifier.name != "self" or
                    (not isinstance(funcType.parameters[0], ClassValueType)) or
                    funcType.parameters[0].className != self.currentClass):
                self.addError(
                    node, "Missing self argument in method: {}".format(funcName))
                return
        # TODO check function body
        return 

    def ReturnStmt(self, node:ReturnStmt):
        pass

    def GlobalDecl(self, node:GlobalDecl):
        pass

    def Identifier(self, node:Identifier):
        varType = self.getType(node.name)
        if varType is not None and isinstance(varType, ValueType) {
            node.inferredType = varType;
        } else {
            self.addError(node, "Not a variable: {:s}".format(node.name))
            node.inferredType = self.OBJECT_TYPE
        }
        return node.inferredType

    def MemberExpr(self, node:MemberExpr):
        pass

    def StringLiteral(self, node:StringLiteral):
        node.inferredType = StrType()
        return node.inferredType

    def IfExpr(self, node:IfExpr):
        pass

    def MethodCallExpr(self, node:MethodCallExpr):
        pass

    def ListType(self, node:ListType):
        return ListValueType(node.elementType.typecheck(self))

    def ClassType(self, node:ClassType):
        if not self.classExists(node.name):
            self.addError(node, "Unknown class: {}".format(node.name))
            return ClassValueType(node.className)
        else:
            return self.OBJECT_TYPE

    def TypeAnnotation(self, node:TypeAnnotation):
        pass

