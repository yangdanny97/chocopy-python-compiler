from .astnodes import *
from .types import *
from .visitor import Visitor

class ClosureVisitor(Visitor):
    # record all free vars from nested functions

    def __init__(self):
        self.symbolTable = [set()]
        self.vars = []
    
    def visit(self, node: Node):
        if isinstance(node, Expr) or isinstance(node, Stmt):
            return node.visitChildren(self)
        return node.visit(self)

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
        for d in node.declarations:
            self.visit(d)

    def FuncDef(self, node: FuncDef):
        self.vars = []
        self.symbolTable.append(set())
        freevars:[str] = []
        for p in node.params:
            self.symbolTable[-1].add(p.identifier.name)
        for d in node.declarations:
            self.symbolTable[-1].add(d.getIdentifier().name)
        for s in node.statements:
            self.visit(s)
        freevars += self.vars
        for d in node.declarations:
            self.visit(d)
            if isinstance(d, FuncDef):
                freevars += d.freevars
        # deduplicate inner function freevars, remove the ones declared in this scope
        freevars = [x for x in self.deduplicate(freevars) if x not in self.symbolTable[-1]]
        self.symbolTable.pop()
        node.freevars = freevars
        return node
    
    def Identifier(self, node: Identifier):
        self.vars.append(node.name)



