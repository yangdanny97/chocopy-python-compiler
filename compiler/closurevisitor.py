from .astnodes import *
from .types import *
from .visitor import Visitor

class ClosureVisitor(Visitor):
    # record all free vars from nested functions

    def __init__(self):
        self.globals = set()
        self.vars = []
        self.decls = []
    
    def visit(self, node: Node):
        if isinstance(node, Expr) or isinstance(node, Stmt):
            return node.postorder(self)
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
        # mark all top-level vars to be global
        self.vars = []
        for s in node.statements:
            self.visit(s)
        for v in self.vars:
            v.isGlobal = True

    def ClassDef(self, node: ClassDef):
        for d in node.declarations:
            self.visit(d)

    def process_vars(self, decls:[str], variables:[Identifier])->[Identifier]:
        freevars = []
        for v in variables:
            if v.name not in decls and v.name not in self.globals:
                freevars.append(v)
            elif v.name in self.globals and not any([v.name in d for d in self.decls]):
                v.isGlobal = True
        return freevars

    def FuncDef(self, node: FuncDef):
        self.vars = []
        decls = set()
        for p in node.params:
            decls.add(p.identifier.name)
        for d in node.declarations:
            if not (isinstance(d, GlobalDecl) or isinstance(d, NonLocalDecl)):
                decls.add(d.getIdentifier().name)
        self.decls.append(decls)
        for s in node.statements:
            self.visit(s)
        freevars = self.process_vars(decls, self.vars)
        for d in node.declarations:
            self.visit(d)
            if isinstance(d, FuncDef):
                freevars += d.freevars
        freevars = self.process_vars(decls, freevars)
        node.freevars = self.deduplicate(freevars)
        self.decls.pop()
        return node
    
    def Identifier(self, node: Identifier):
        self.vars.append(node)



