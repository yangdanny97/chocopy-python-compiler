from .astnodes import *
from .types import *
from .visitor import Visitor
from typing import List, Dict, Optional


class HoistedFunctionInfo:
    def __init__(self, name, decl):
        self.name = name
        self.decl = decl


class NestedFuncHoister(Visitor):
    # hoist all nested funcs to be top level funcs
    # rename hoisted functions to be unique & rename call sites
    functionInfo: List[Dict[str, HoistedFunctionInfo]]
    currentClass: Optional[str]
    nestingNames: List[str]
    hoisted: List[FuncDef]

    def __init__(self):
        # map of function names to their modified names
        self.classes = set(["object", "int", "str", "bool"])
        self.functionInfo = [{}]
        self.currentClass = None
        self.nestingNames = []
        self.nestingLevel = 0
        self.hoisted = []

    def visit(self, node: Node):
        if isinstance(node, Stmt) or isinstance(node, Expr):
            return node.postorder(self)
        else:
            return node.visit(self)

    def genFuncName(self, name: str):
        # example:
        # f2 declared inside f1 will be named f1__f2
        # f4 declared inside C.f3 will be named C__f3__f4
        if len(self.nestingNames) == 0:
            return name
        return "__".join(self.nestingNames) + "__" + name

    def Program(self, node: Program):
        for d in node.declarations:
            if isinstance(d, FuncDef):
                self.rename(d)
        for d in node.declarations:
            self.nestingLevel = 0
            self.visit(d)
        node.declarations = node.declarations + self.hoisted
        for s in node.statements:
            self.visit(s)

    def ClassDef(self, node: ClassDef):
        self.nestingLevel = 0
        self.functionInfo.append({})
        self.currentClass = node.getIdentifier().name
        self.nestingNames.append(self.currentClass)
        self.classes.add(self.currentClass)

        for d in node.declarations:
            if isinstance(d, FuncDef):
                self.rename(d)
        for d in node.declarations:
            self.visit(d)

        self.functionInfo.pop()
        self.nestingNames.pop()
        self.currentClass = None

    def rename(self, node: FuncDef):
        identifier = node.getIdentifier()
        oldname = identifier.name
        if self.nestingLevel != 0:
            identifier.name = self.genFuncName(identifier.name)
        self.functionInfo[-1][oldname] = HoistedFunctionInfo(
            identifier.name, node)

    def FuncDef(self, node: FuncDef):
        identifier = node.getIdentifier()
        self.functionInfo.append({})
        self.nestingNames.append(identifier.name)
        self.nestingLevel += 1
        for d in node.declarations:
            if isinstance(d, FuncDef):
                self.rename(d)
        for d in node.declarations:
            self.visit(d)

        for s in node.statements:
            self.visit(s)

        self.functionInfo.pop()
        self.nestingNames.pop()
        self.nestingLevel -= 1

        if self.nestingLevel > 0:
            self.hoisted.append(node)

        node.declarations = [
            d for d in node.declarations
            if not isinstance(d, FuncDef)
        ]

    def CallExpr(self, node: CallExpr):
        for t in self.functionInfo[::-1]:
            if node.function.name in t:
                decl = t[node.function.name].decl
                node.function.name = t[node.function.name].name
                node.freevars = decl.freevars
                return
        if node.function.name in {"__assert__", "print", "input", "len"}:
            return
        if node.function.name in self.classes:
            return
        raise Exception(
            "Unable to find function declaration for " + node.function.name)
