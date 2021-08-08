from .typechecker import TypeChecker
from .typesystem import TypeSystem
from collections import defaultdict
from .astnodes import *
from .types import *
from .visitor import Visitor

class HoistedFunctionInfo:
    def __init__(self, name, decl):
        self.name = name
        self.decl = decl

class NestedFuncHoister(Visitor):
    # hoist all nested funcs to be top level funcs
    # rename hoisted functions to be unique
    # remove all nonlocal decls
    # while functions nested inside methods will be renamed, the methods themselves will not

    # TODO: properly hoist methods

    def __init__(self):
        # map of function names to their modified names
        self.functionInfo = [defaultdict(lambda: None)]
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
        # f2 declared inside f1 will be named f1__f2
        # f4 declared inside C.f3 will be named C__f3__f4
        if len(self.nestingNames) == 0:
            return name
        return "__".join(self.nestingNames) + "__" + name

    def Program(self, node: Program):
        for d in node.declarations:
            if isinstance(d, FuncDef):
                name = d.getIdentifier().name
                self.functionInfo[-1][name] = HoistedFunctionInfo(name, d)
        for d in node.declarations:
            self.nestingLevel = 0
            self.visit(d)
        node.declarations = node.declarations + self.hoisted
        for s in node.statements:
            self.visit(s)

    def ClassDef(self, node: ClassDef):
        self.nestingLevel = 0
        self.functionInfo.append(defaultdict(lambda: None))
        self.currentClass = node.getIdentifier().name
        self.nestingNames.append(self.currentClass)

        for d in node.declarations:
            self.visit(d)

        self.functionInfo.pop()
        self.nestingNames.pop()
        self.currentClass = None

    def FuncDef(self, node: FuncDef):
        self.functionInfo.append(defaultdict(lambda: None))
        self.nestingNames.append(node.getIdentifier().name)
        self.nestingLevel += 1

        for d in node.declarations:
            if isinstance(d, FuncDef):
                name = d.getIdentifier().name
                newname = self.genFuncName(name)
                self.functionInfo[-1][name] = HoistedFunctionInfo(newname, d)
                d.getIdentifier().name = newname
        
        for d in node.declarations:
            self.visit(d)
        node.declarations = [
            d for d in node.declarations 
            if not isinstance(d, FuncDef) and not isinstance(d, NonLocalDecl)
        ]

        for s in node.statements:
            self.visit(s)
        
        self.functionInfo.pop()
        self.nestingNames.pop()
        self.nestingLevel -= 1

        if self.nestingLevel > 0:
            self.hoisted.append(node)
        return node

    def CallExpr(self, node: CallExpr):
        for t in self.functionInfo[::-1]:
            if node.function.name in t:
                node.function.name = t[node.function.name].name
                return


