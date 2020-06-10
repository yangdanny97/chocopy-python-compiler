from .astnodes import *
from .types import *
from .visitor import Visitor

class NonlocalVisitor(Visitor):
    # record all nonlocal declarations from nested functions

    def __init__(self):
        self.symbolTable = [set()]

    def deduplicate(self, ids:[str])->[str]:
        seen = set()
        res = []
        for i in ids:
            if i in seen:
                continue
            seen.add(i)
            res.append(i)
        return res

    def Program(self, node: Program):
        for d in node.declarations:
            if isinstance(d, VarDef):
                self.symbolTable[-1].add(d.getIdentifier().name)
        for d in node.declarations:
            self.visit(d)

    def ClassDef(self, node: ClassDef):
        node.declarations = [self.visit(d) for d in node.declarations]

    def FuncDef(self, node: FuncDef):
        self.symbolTable.append(set())
        nonlocals = []
        for d in node.declarations:
            if isinstance(d, NonLocalDecl):
                nonlocals.append(d.getIdentifier().name)
            self.symbolTable[-1].add(d.getIdentifier().name)
        node.declarations = [self.visit(d) for d in node.declarations]
        for d in node.declarations:
            if isinstance(d, FuncDef):
                nonlocals += d.nonlocals
        # deduplicate inner function nonlocals, remove the ones declared in this scope
        nonlocals = [x for x in self.deduplicate(nonlocals) if x not in self.symbolTable[-1]]
        self.symbolTable.pop()
        node.nonlocals = nonlocals
        return node

    def GlobalDecl(self, node: NonLocalDecl):
        return node

    def NonLocalDecl(self, node: NonLocalDecl):
        return node

    def VarDef(self, node: VarDef):
        return node

