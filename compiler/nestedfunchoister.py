from .typechecker import TypeChecker
from .typesystem import TypeSystem
from collections import defaultdict
from .astnodes import *
from .types import *
from .visitor import Visitor

class NestedFuncHoister(Visitor):
    # rename nested functions to be unique
    # hoist all nested funcs to top level
    # remove all nonlocal decls

    # while functions nested inside methods will be renamed, the methods themselves will not

    def __init__(self):
        # map of function names to their LLVM function names
        self.symbolTable = [defaultdict(lambda: None)]
        self.currentClass = None
        self.nestingNames = []
        self.nestingLevel = 0
        self.hoisted = []

    def visit(self, node: Node):
        if isinstance(node, Stmt) or isinstance(node, Expr):
            return node.postorder(self)
        else:
            return node.visit(self)

    def genFuncName(self, name:str):
        # example: 
        # f2 declared inside f1 will be named f1.f2
        # f4 declared inside C.f3 will be named C.f3.f4
        if len(self.nestingNames) == 0:
            return name
        return ".".join(self.nestingNames) + "." + name

    def Program(self, node: Program):
        for d in node.declarations:
            if isinstance(d, FuncDef):
                name = d.getIdentifier().name
                self.symbolTable[-1][name] = name
        for d in node.declarations:
            self.visit(d)
        node.declarations = node.declarations + self.hoisted
        for s in node.statements:
            self.visit(s)

    def ClassDef(self, node: ClassDef):
        self.symbolTable.append(defaultdict(lambda: None))
        self.currentClass = node.getIdentifier().name
        self.nestingNames.append(self.currentClass)

        for d in node.declarations:
            self.visit(d)

        self.symbolTable.pop()
        self.nestingNames.pop()
        self.currentClass = None

    def FuncDef(self, node: FuncDef):
        self.symbolTable.append(defaultdict(lambda: None))
        self.nestingNames.append(node.getIdentifier().name)
        self.nestingLevel += 1

        for d in node.declarations:
            if isinstance(d, FuncDef):
                name = d.getIdentifier().name
                newname = self.genFuncName(name)
                self.symbolTable[-1][name] = newname
                d.getIdentifier().name = newname
        
        for d in node.declarations:
            self.visit(d)
        node.declarations = [d for d in node.declarations if not isinstance(d, FuncDef) and not isinstance(d, NonLocalDecl)]

        for s in node.statements:
            self.visit(s)
        
        self.symbolTable.pop()
        self.nestingNames.pop()
        self.nestingLevel -= 1

        if self.nestingLevel > 0:
            self.hoisted.append(node)
        return node

    def CallExpr(self, node: CallExpr):
        for t in self.symbolTable[::-1]:
            if node.function.name in t:
                node.function.name = t[node.function.name]
                return


