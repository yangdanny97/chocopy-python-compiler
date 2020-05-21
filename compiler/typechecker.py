from .AstNodes import *
from .Types import *
from collections import defaultdict

class TypeChecker:
    def __init__(self):
        # stack of hashtables representing scope
        # each table holds identifier->type mappings defined in that scppe
        self.symbolTable = [defaultdict(lambda: None)]
        # type hierachy: dictionary of class->superclass mappings
        self.classes = defaultdict(lambda: None)
        # set up default class hierarchy
        self.classes["object"] = None
        self.classes["int"] = "object"
        self.classes["bool"] = "object"
        self.classes["str"] = "object"
        self.classes["<none>"] = "object"
        self.classes["<empty>"] = "object"
        self.INT_TYPE = Types.IntType()
        self.STR_TYPE = Types.StrType()
        self.BOOL_TYPE = Types.BoolType()
        self.NONE_TYPE = Types.NoneType()
        self.EMPTY_TYPE = Types.EmptyType()
        self.OBJECT_TYPE = Types.ObjectType()
        self.errors = []

    def typecheck(node):
        node.typecheck(self)

    def enterScope():
        self.symbolTable.append(defaultdict(lambda: None))

    def exitScope():
        self.symbolTable.pop()

    def getType(var:str):
        # get the type of an identifier in the current scope, or None if not found
        for table in self.symbolTable[::-1]:
            if var in table:
                return table[var]
        return None

    def defInCurrentScope(var:str)->bool:
        # return if the name was defined in the current scope
        return self.symbolTable[-1][var] is not None

    def isSubClass(a:str, b:str)->bool:
        # return if a is the same class or subclass of b
        curr = a
        while curr is not None:
            if curr == b:
                return True
            else:
                curr = self.classes[curr]
        return False

    def classExists(className:str)->bool:
        # we cannot check for None because it is a defaultdict
        return className in classes

    def isSubtype(a:SymbolType, b:SymbolType)->bool:
        # return if a is a subtype of b
        if b == self.OBJECT_TYPE:
            return True
        if isinstance(a, ClassValueType) and isinstance(b, ClassValueType):
            return self.isSubClass(a.className, b.className)
        return a == b

    def canAssign(a:SymbolType, b:SymbolType)->bool:
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


    # visit methods for each AST node

    def Program(node:Program):
        pass
    
    def AssignStmt(node:AssignStmt):
        pass

    def Errors(node:Errors):
        pass

    def IfStmt(node:IfStmt):
        pass

    def TypedVar(node:TypedVar):
        pass

    def BinaryExpr(node:BinaryExpr):
        pass

    def IndexExpr(node:IndexExpr):
        pass

    def NonLocalDecl(node:NonLocalDecl):
        pass

    def UnaryExpr(node:UnaryExpr):
        pass

    def BooleanLiteral(node:BooleanLiteral):
        node.inferredType = Types.BoolType()

    def ExprStmt(node:ExprStmt):
        pass

    def IntegerLiteral(node:IntegerLiteral):
        node.inferredType = Types.IntType()

    def NoneLiteral(node:NoneLiteral):
        node.inferredType = Types.NoneType()

    def VarDef(node:VarDef):
        pass

    def CallExpr(node:CallExpr):
        pass

    def ForStmt(node:ForStmt):
        pass

    def ListExpr(node:ListExpr):
        if len(elements) == 0:
            node.inferredType = ListValueType(Types.EmptyType())
        # TODO

    def WhileStmt(node:WhileStmt):
        pass

    def ClassDef(node:ClassDef):
        pass

    def FuncDef(node:FuncDef):
        pass

    def ListType(node:ListType):
        pass

    def ReturnStmt(node:ReturnStmt):
        pass

    def ClassType(node:ClassType):
        pass

    def GlobalDecl(node:GlobalDecl):
        pass

    def CompilerError(node:CompilerError):
        pass

    def Identifier(node:Identifier):
        pass

    def MemberExpr(node:MemberExpr):
        pass

    def StringLiteral(node:StringLiteral):
        node.inferredType = Types.StrType()

    def IfExpr(node:IfExpr):
        pass

    def MethodCallExpr(node:MethodCallExpr):
        pass

    def TypeAnnotation(node:TypeAnnotation):
        pass

