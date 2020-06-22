from .astnodes import *
from .types import *
from .visitor import Visitor

class ClosureVisitor(Visitor):
    # record all free vars from nested functions

    def __init__(self):
        self.globals = set()
        self.vars = []
    
    def visit(self, node: Node):
        if isinstance(node, Expr) or isinstance(node, Stmt):
            return node.visitChildren(self)
        return node.visit(self)

    def deduplicate(self, ids):
        seen = set()
        res = []
        for i in ids:
            if i.name in seen:
                continue
            seen.add(i.name)
            res.append(i)
        return res

    def Program(self, node: Program):
        for d in node.declarations:
            if isinstance(d, VarDef):
                self.globals.add(d.getIdentifier().name)
        for d in node.declarations:
            self.visit(d)

    def ClassDef(self, node: ClassDef):
        for d in node.declarations:
            self.visit(d)

    def FuncDef(self, node: FuncDef):
        self.vars = []
        decls = set()
        for p in node.params:
            decls.add(p.identifier.name)
        for d in node.declarations:
            decls.add(d.getIdentifier().name)
        for s in node.statements:
            self.visit(s)
        freevars = [v for v in self.vars if (v.name not in decls and v.name not in self.globals)]
        for d in node.declarations:
            self.visit(d)
            if isinstance(d, FuncDef):
                freevars += d.freevars
        freevars = [v for v in freevars if (v.name not in decls and v.name not in self.globals)]
        node.freevars = freevars
        return node
    
    def Identifier(self, node: Identifier):
        self.vars.append(node)



