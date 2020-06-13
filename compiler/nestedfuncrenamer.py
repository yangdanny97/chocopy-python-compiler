from .typechecker import TypeChecker
from .typesystem import TypeSystem
from collections import defaultdict
from .astnodes import *
from .types import *
from .visitor import Visitor

class NestedFuncRenamer(Visitor):
    # rename nested functions to be unique, 
    # that way we can declare them in a global ctx for LLVM
    # we do not rename methods at this stage

    def __init__(self):
        # map of function names to their LLVM function names
        self.symbolTable = [defaultdict(lambda: None)]
        self.currentClass = None
        self.funcNesting = []

    def visit(self, node: Node):
        if isinstance(node, Stmt) or isinstance(node, Expr):
            return node.visitChildren(self)
        else:
            return node.visit(self)

    def genFuncName(self, name:str):
        # for example, f2 declared inside f1 will be named f1_f2
        # f4 declared inside C.f3 will be named C_f3_f4
        return "_".join(self.funcNesting) + "_" + name

    def Program(self, node: Program):
        for d in node.declarations:
            if isinstance(d, FuncDef):
                name = d.getIdentifier().name
                self.symbolTable[-1][name] = name
        for d in node.declarations:
            self.visit(d)
        for s in node.statements:
            self.visit(s)

    def ClassDef(self, node: ClassDef):
        self.symbolTable.append(defaultdict(lambda: None))
        self.currentClass = node.getIdentifier().name
        self.funcNesting.append(self.currentClass)

        for d in node.declarations:
            self.visit(d)

        self.symbolTable.pop()
        self.funcNesting.pop()
        self.currentClass = None

    def FuncDef(self, node: FuncDef):
        name = node.getIdentifier().name
        newname = self.genFuncName(name)
        self.symbolTable[-1][name] = newname
        node.getIdentifier().name = newname
        self.symbolTable.append(defaultdict(lambda: None))
        self.funcNesting.append(name)

        for d in node.declarations:
            self.visit(d)
        for s in node.statements:
            self.visit(s)
        
        self.symbolTable.pop()
        self.funcNesting.pop()
        return node

    def CallExpr(self, node: CallExpr):
        for t in self.symbolTable[::-1]:
            if node.function.name in t:
                node.function.name = t[node.function.name]


